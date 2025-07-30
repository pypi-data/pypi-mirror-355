import sys
import os
import numpy as np
import torch
import yaml
from omegaconf import OmegaConf
from pathlib import Path

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_PATH)

from saicinpainting.evaluation.utils import move_to_device
from saicinpainting.evaluation.refinement import refine_predict
from saicinpainting.training.trainers import load_checkpoint
from saicinpainting.evaluation.data import pad_tensor_to_modulo

class LaMa:
    def __init__(self, refine=False, **kwargs):
        os.environ['OMP_NUM_THREADS'] = '1'
        os.environ['OPENBLAS_NUM_THREADS'] = '1'
        os.environ['MKL_NUM_THREADS'] = '1'
        os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
        os.environ['NUMEXPR_NUM_THREADS'] = '1'

        ckpt_p = os.path.join(os.environ['TORCH_HOME'], "big-lama")
        config_p = os.path.join(CURRENT_PATH, "default.yaml")
        device = torch.device('cuda')
        
        predict_config = OmegaConf.load(config_p)
        predict_config.model.path = ckpt_p
        predict_config.refine = refine

        train_config_path = os.path.join(
            predict_config.model.path, 'config.yaml')

        with open(train_config_path, 'r') as f:
            train_config = OmegaConf.create(yaml.safe_load(f))

        train_config.training_model.predict_only = True
        train_config.visualizer.kind = 'noop'

        checkpoint_path = os.path.join(
            predict_config.model.path, 'models',
            predict_config.model.checkpoint
        )
        self.mod = 8
        self.refine = refine
        self.device = device
        self.predict_config = predict_config
        self.model = load_checkpoint(
            train_config, checkpoint_path, strict=False, map_location='cpu')
        self.model.freeze()
        if not refine:
            self.model.to(device)


    def detect(self, img, mask, **kwargs):
        """
            img:        (H, W, C) opencv image
            mask:       (H, W) binary mask
        """
        img_t = torch.from_numpy(img).float().div(255.)
        mask_t = torch.from_numpy(mask).float()

        batch = {}
        batch['image'] = img_t.permute(2, 0, 1).unsqueeze(0)
        batch['mask'] = mask_t[None, None]
        unpad_to_size = [batch['image'].shape[2], batch['image'].shape[3]]
        batch['image'] = pad_tensor_to_modulo(batch['image'], self.mod)
        batch['mask'] = pad_tensor_to_modulo(batch['mask'], self.mod)
        batch = move_to_device(batch, self.device)
        batch['mask'] = (batch['mask'] > 0) * 1.
        batch['unpad_to_size'] = np.array(unpad_to_size)

        if self.refine:
            cur_res = refine_predict(batch, self.model, **self.predict_config.refiner)
            cur_res = cur_res[0].permute(1,2,0).detach().cpu().numpy()
        else:
            batch = self.model(batch)
            cur_res = batch[self.predict_config.out_key][0].permute(1, 2, 0)
            cur_res = cur_res.detach().cpu().numpy()
            if unpad_to_size is not None:
                orig_height, orig_width = unpad_to_size
                cur_res = cur_res[:orig_height, :orig_width]

        cur_res = np.clip(cur_res * 255, 0, 255).astype('uint8')
        return cur_res

import os
import cv2
import numpy as np
import torch
try:
    from CRFs import DenseCRF
    has_crf = True
except:
    has_crf = False
from segment_anything import sam_model_registry, SamPredictor, SamAutomaticMaskGenerator
from segment_anything.utils.transforms import ResizeLongestSide

class SegmentAnything:
    def __init__(self, auto_mode=False, crf=False, crf_config=None, **kwargs):
        model_path = os.path.join(os.environ['TORCH_HOME'], "sam_vit_h_4b8939.pth")
        model_type = "vit_h"
        device = "cuda"
        self.auto_mode = auto_mode
        self.sam = sam_model_registry[model_type](checkpoint=model_path)
        self.sam.to(device=device).eval()
        self.predictor = SamAutomaticMaskGenerator(self.sam) if auto_mode else SamPredictor(self.sam)
        self.resize_transform = ResizeLongestSide(self.sam.image_encoder.img_size)
        self.crf = crf
        if self.crf and not has_crf:
            self.crf = False
            print("Disable CRF since pydensecrf is not installed")
        if crf_config:
            self.crf_config = crf_config
        else:
            self.crf_config = {'pos_xy_std': (13,13), 'bil_xy_std': (7,7), 'bil_rgb_std': (13,13,13)}

    def prepare_image(self, image, transform, device):
        image = transform.apply_image(image)
        image = torch.as_tensor(image, device=device.device) 
        return image.permute(2, 0, 1).contiguous()

    def detect_auto(self, rgb_image):
        return self.predictor.generate(rgb_image)

    def detect_manual(self, rgb_image, input_points=None, input_labels=None, input_boxes=None):
        self.predictor.set_image(rgb_image)
        with torch.no_grad():
            masks, scores, logits = self.predictor.predict(
                point_coords=input_points,
                point_labels=input_labels,
                box=input_boxes,
                multimask_output=True,
            )
        raw_mask = masks[np.argmax(scores)]
        if self.crf:
            cat_logits = np.concatenate([1.0-raw_mask[None,...], raw_mask[None,...]], dtype=np.float32, axis=0)
            cat_prob = torch.softmax(torch.from_numpy(cat_logits), dim=0).numpy()
            refine_mask = DenseCRF(rgb_image, cat_prob, **self.crf_config)
        else:
            refine_mask = masks[np.argmax(scores)]
        return refine_mask

    def detect(self, img, **kwargs):
        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if self.auto_mode:
            return self.detect_auto(rgb_image)
        else:
            return self.detect_manual(rgb_image, **kwargs)

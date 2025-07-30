import os
import torch
import numpy as np
import cv2
from .model_r50 import R50

class Quality:
    def __init__(self, model_name, device):
        """
            model_name(str):     "r50"
        """
        if model_name == "r50":
            model_path = os.path.join(os.environ['TORCH_HOME'], "SDD_FIQA_checkpoints_r50.pth")
        else:
            raise NotImplementedError("model_name %s not implemented" % model_name)
        self.net = R50([112, 112], use_type="Qua")
        net_dict = self.net.state_dict()     
        data_dict = {
            key.replace('module.', ''): value for key, value in torch.load(model_path, map_location=lambda storage, loc: storage).items()}
        net_dict.update(data_dict)
        self.net.load_state_dict(net_dict)
        self.net.eval().requires_grad_(False)
        self.net.to(device)

    def detect(self, x):
        """ return score in [0.0, 100.0], larger is better
        """
        return self.net(x)

import os
import torch
from torch import nn
import torch.nn.functional as F
from .mobilefacenet import MobileFaceNet
from .model_irse import Backbone

InsightFace_dir = os.path.dirname(os.path.abspath(__file__))

class FaceFeatures(nn.Module):
    def __init__(self, model_name):
        """
        model_name(str):       'model_mobilefacenet' or 'model_ir_se50'
        """
        super().__init__()
        weights_path = os.path.join(os.environ['TORCH_HOME'], model_name+'.pth')
        self.model = MobileFaceNet(512) if model_name == 'model_mobilefacenet' else Backbone(input_size=112, num_layers=50, drop_ratio=0.6, mode='ir_se')
        self.model.load_state_dict(torch.load(weights_path, map_location=lambda storage, loc: storage))
        self.model.eval()
        self.face_pool = torch.nn.AdaptiveAvgPool2d((112, 112))

    def forward(self, batch_tensor):
        ## crop face
        # h, w = batch_tensor.shape[2:]
        # top = int(h / 2.1 * (0.8 - 0.33))
        # bottom = int(h - (h / 2.1 * 0.3))
        # size = bottom - top
        # left = int(w / 2 - size / 2)
        # right = left + size
        # batch_tensor = batch_tensor[:, :, top: bottom, left: right]
        x = self.face_pool(batch_tensor) if batch_tensor.shape[2] != 112 else batch_tensor
        features = self.model(x)
        return features

    def cosine_distance(self, batch_tensor1, batch_tensor2):
        feature1 = self.forward(batch_tensor1)
        feature2 = self.forward(batch_tensor2)
        return 1 - torch.cosine_similarity(feature1, feature2)  # same as 1 - feature1[i].dot(feature2[i])
        

import torch
import lpips
from .base import base_checker
from ..utils import to_tensor

__all__ = ["similarity_checker"]


class similarity_checker(base_checker):
    def __init__(self, threshold=0.08, verbose=False):
        super().__init__()
        self.loss_fn = lpips.LPIPS(net='alex')
        self.loss_fn.cuda().eval()
        self.verbose = verbose
        self.threshold = threshold
        self.score = None

    def check_image_pair(self, img_A, img_B):
        tensor_B = to_tensor(img_B).cuda()
        tensor_A = to_tensor(img_A).cuda()
        with torch.no_grad():
            self.score = self.loss_fn.forward(tensor_A, tensor_B)
        if self.score < self.threshold:
            return True
        return False

    def check_tensor_pair(self, tensor_A, tensor_B):
        with torch.no_grad():
            self.score = self.loss_fn.forward(tensor_A, tensor_B)
        if self.score < self.threshold:
            return True
        return False

"""
Deprecated
"""
import os
import cv2
from .base import base_parser
# from Segmentor import portrait_segmentor
import traceback

class mask_parser(base_parser):
    def __init__(self, mask_mode='portrait'):
        super().__init__()
        self.set_mask_detector(mask_mode)

    def set_mask_detector(self, mask_mode='portrait'):
        self.mask_mode = mask_mode
        if self.mask_mode == 'portrait':
            from detectron2_proj import instance_segmentor
            # self.segmentor = portrait_segmentor()
            self.segmentor = instance_segmentor()
            self.detector_bank += [self.semantic_mask_detector]
        else:
            raise NotImplementedError('mask mode: %s is not implemented' % self.mask_mode)

    def semantic_mask_detector(self, bgr_img):
        self.output_mask_dir = os.path.join(self.output_dir, 'portrait_mask')
        if not os.path.exists(self.output_mask_dir):
            os.makedirs(self.output_mask_dir, exist_ok=True)
        try:
            mask = self.segmentor.segment(bgr_img)
            base_name = self.current_obj_dict['name']
            mask_path = os.path.join(os.path.abspath(self.output_mask_dir), base_name + '.png')
            cv2.imwrite(mask_path, mask)
        except Exception as e:
            print(traceback.print_exc())
            return {}

        mask_path_dict = {self.mask_mode: mask_path}

        return {"masks": mask_path_dict}



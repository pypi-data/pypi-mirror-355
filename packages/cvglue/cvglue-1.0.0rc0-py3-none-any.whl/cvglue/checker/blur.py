import os
import cv2
import numpy as np
from .base import base_checker
from ..utils.faceutils import warp_landmarks, crop_face_v3, generate_face_mask

__all__ = ["blur_checker"]


class blur_checker(base_checker):
    def __init__(self, threshold=300, detect_face=False, verbose=False):
        '''Check whether image is blurry. A smaller score means more blurry.
           可用于人脸筛选部分较小或模糊的情况，但无法应对遮挡、头发、边缘、相机噪点等情况
        '''
        super().__init__()
        self.detect_face = detect_face
        self.crop_params = {"output_size": (224,224), "hp_factor": 1.7, "wd_factor": 0.6, "shift_factor": 1.1, 
                            "border_mode": cv2.BORDER_REPLICATE, "use_chin": True, "antialias": True}
        self.verbose = verbose
        self.threshold = threshold
        self.checked_img = None
        self.score = -1.0

    def check_image(self, img_raw, face=None):
        if face is not None:
            crop_img, wap_mat = crop_face_v3(img_raw, face['key_points'], face['landmarks'], **self.crop_params)
            face_len = crop_img.shape[0]
            mask = generate_face_mask(face_len, face_len, warp_landmarks(face['landmarks'], wap_mat), include_forehead=True, top_y=face_len/11.2, fast=True).astype(np.float64)
            self.checked_img = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
            lap_map = cv2.Laplacian(self.checked_img, cv2.CV_64F)[...,np.newaxis]
            mean_background = np.ones_like(lap_map)
            mean_background *= np.sum(mask*lap_map) / np.sum(mask)
            res = (1.0-mask)*mean_background + mask*lap_map
            self.score = (res.var()*face_len*face_len)/np.sum(mask)
            if self.verbose:
                print(self.score)
        else:
            img_raw = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
            self.checked_img = cv2.resize(img_raw, (224, 224))
            self.score = cv2.Laplacian(self.checked_img, cv2.CV_64F).var()
        if self.score < self.threshold:
            return True
        else:
            return False

    def check_image_pair(self, img_A, img_B):
        img_A = cv2.cvtColor(img_A, cv2.COLOR_BGR2GRAY)
        img_B = cv2.cvtColor(img_B, cv2.COLOR_BGR2GRAY)
        img_A = cv2.resize(img_A, (224, 224))
        img_B = cv2.resize(img_B, (224, 224))
        score_A = cv2.Laplacian(img_A, cv2.CV_64F).var()
        score_B = cv2.Laplacian(img_B, cv2.CV_64F).var()
        if score_A > score_B:
            self.score = score_B
            self.checked_img = img_B
        else:
            self.score = score_A
            self.checked_img = img_A
        return score_A - score_B

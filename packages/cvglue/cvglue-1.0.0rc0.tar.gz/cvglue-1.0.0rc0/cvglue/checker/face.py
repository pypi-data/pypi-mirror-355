import os
import cv2
import numpy as np
from ..detector import face_detector
from .base import base_checker
import functools

__all__ = ["face_checker"]


class face_checker(base_checker):
    def __init__(self, check_num=-1, threshold=0.6, use_detector=True, detect_mode='selfie', verbose=False):
        '''
            detect_mode(str):       'selfie': best performance when faces are close to camera, but more likely to misdetect in small object
        '''
        super().__init__()
        self.check_num = check_num
        self.threshold = threshold
        self.dets = None
        self.verbose = verbose
        if use_detector:
            self.fd = face_detector(detect_mode=detect_mode)

    def check_image(self, img_raw):
        self.dets = self.fd(img_raw)
        if self.dets.size != 0:
            face_cnt = np.sum(self.dets[:, 4] > self.threshold)
        else:
            face_cnt = 0
        return face_cnt == self.check_num if self.check_num >= 0 else face_cnt

    def check_data(self, iap_data):
        try:
            return len(iap_data[1]['faces']) == self.check_num if self.check_num >= 0 else len(iap_data[1]['faces'])
        except:
            return False if self.check_num >= 0 else 0

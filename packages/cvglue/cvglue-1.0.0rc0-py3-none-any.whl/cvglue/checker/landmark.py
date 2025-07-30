import os
import cv2
import numpy as np
from .base import base_checker
from ..thirdparty.AdaptiveWing import AdaptiveWing

__all__ = ["landmark_checker"]


class landmark_checker(base_checker):
    def __init__(self, rtol=0.2, verbose=False):
        super().__init__()
        self.verbose = verbose
        self.rtol = rtol
        self.kp_res = []

    def check_face(self, iap_data, face_id):
        face = iap_data[1]['faces'][face_id]
        boundaries = AdaptiveWing.to_boundaries(face['landmarks'])
        ld_kp = boundaries['keypoints']
        fd_kp = np.reshape(face['key_points'], (-1,2))
        eye_dist = np.sqrt(np.sum((fd_kp[1]-fd_kp[0])**2))
        self.kp_res = np.sqrt(np.sum((ld_kp - fd_kp)**2, axis=-1))
        if self.verbose:
            print(self.kp_res, self.rtol*eye_dist)
        if np.max(self.kp_res) < self.rtol*eye_dist:
            return True
        else:
            return False

    def check_data(self, iap_data):
        '''Check whether landmarks are relaiable.

        Notice:
            - Checking algorithmn using `key_points` from face detector and `landmarks` from landmarks detector
            - Abnormal would appear when large L2 error calculated between `key_points` and `landmarks`
        '''
        ret = True
        for idx in range(len(iap_data[1]['faces'])):
            ret &= self.check_face(iap_data, idx)
        return ret


'''
    Set your custom detector here.
'''
import cv2
import functools
import numpy as np
import torch
from ..thirdparty.FaceDetector.interface import face_detector as custom_detector
from ..thirdparty.AdaptiveWing import AdaptiveWing
from ..utils.faceutils import warp_landmarks, crop_face_v4, norm_crop
from ..thirdparty.HeadPoseDetector import HeadPoseDetector
from ..thirdparty.InsightFace.face_features import FaceFeatures
from ..thirdparty.TFace import Quality

__all__ = ["face_detector", "landmark_detector", "attribute_detector", "faceid_detector", "quality_detector"]

class face_detector:
    def __init__(self, model_name='Resnet50', detect_mode='selfie', verbose=False, **kwargs):
        '''
            detect_mode(str):       'selfie': best performance when faces are close to camera, but more likely to misdetect in small object
        '''
        super().__init__()
        self.verbose = verbose
        self.dets = None
        self.custom_detector = custom_detector(model_name, **kwargs)
        if detect_mode == 'selfie':
            self.detect = functools.partial(self.custom_detector.detect_selfie)
        elif detect_mode == 'resize':
            self.detect = functools.partial(self.custom_detector.detect, origin_size=False)
        elif detect_mode == 'default':
            self.detect = functools.partial(self.custom_detector.detect, origin_size=True)
        else:
            raise RuntimeError("Error detector mode %s" % detect_mode)

    def __call__(self, img_raw):
        self.dets = self.detect(img_raw)
        return self.dets


class landmark_detector:
    def __init__(self, rotate=False, verbose=False):
        '''
            rotate(str):       rotate before landmarks detected
        '''
        super().__init__()
        self.verbose = verbose
        self.dets = None
        self.rotate = rotate
        self.custom_detector = AdaptiveWing()

    def __call__(self, img_raw, face_box):
        align_img, warp_mat = crop_face_v4(img_raw, face_box, rotate=self.rotate, ratio=1.0, output_size=450)
        dets = self.custom_detector.detect(align_img)
        inv_warp_mat = cv2.invertAffineTransform(warp_mat)
        self.dets = warp_landmarks(dets, inv_warp_mat)
        return self.dets


class attribute_detector:
    def __init__(self, verbose=False):
        super().__init__()
        self.verbose = verbose
        self.dets = None
        self.custom_detector = HeadPoseDetector()
        # kwargs = {'providers': ['CUDAExecutionProvider']}
        # self.app = FaceAnalysis(root='/workspace/cpfs-data/pretrained_models', **kwargs)
        # self.app.prepare(ctx_id=0)
        # self.face_dict = insightface.app.common.Face({'bbox':None})

    def __call__(self, img_raw, face_box):
        self.dets = self.custom_detector.detect(img_raw, face_box)
        # self.face_dict['bbox'] = face['face_box']
        # gender, age = self.app.models['genderage'].get(img, self.face_dict)
        # face['gender'] = int(gender)
        # face['age'] = int(age)
        return self.dets


class faceid_detector:
    def __init__(self, model_name, verbose=False):
        self.device = torch.device(torch.cuda.current_device() if torch.cuda.is_available() else "cpu")
        self.custom_detector = FaceFeatures(model_name).to(self.device)
        self.dets = None
        self.verbose = verbose

    def __call__(self, img_raw, keypoints):
        img, _ = norm_crop(img_raw, keypoints, output_size=112, antialias=True)
        rgb_img = np.float32(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        x = torch.from_numpy(rgb_img.transpose([2,0,1]) / 127.5 - 1.0).unsqueeze(0)
        x = x.to(self.device)
        self.dets = self.custom_detector(x)
        return self.dets


class quality_detector:
    def __init__(self, model_name, verbose=False):
        self.device = torch.device(torch.cuda.current_device() if torch.cuda.is_available() else "cpu")
        self.custom_detector = Quality(model_name, self.device)
        self.dets = None
        self.verbose = verbose

    def __call__(self, img_raw, keypoints):
        img, _ = norm_crop(img_raw, keypoints, output_size=112, antialias=True)
        rgb_img = np.float32(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        x = torch.from_numpy(rgb_img.transpose([2,0,1]) / 127.5 - 1.0).unsqueeze(0)
        x = x.to(self.device)
        dets = self.custom_detector.detect(x)
        self.dets = dets.cpu().numpy().squeeze()
        return self.dets

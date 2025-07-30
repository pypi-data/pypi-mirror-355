import os
import glob
import cv2
import numpy as np
from PIL import Image
import torch
import torch.backends.cudnn as cudnn
import albumentations as Alb
from albumentations.pytorch.transforms import ToTensorV2
from ..utils.faceutils import norm_crop
from ..utils import make_dataset
from ..thirdparty.InsightFace.face_features import FaceFeatures, InsightFace_dir
from .base import base_checker

__all__ = ["virtual_face_checker"]


class virtual_face_checker(base_checker):
    def __init__(self, max_threshold=0.6, min_threshold=0.4, detect_face=False, verbose=False):
        super().__init__()
        torch.set_grad_enabled(False)
        cudnn.benchmark = True
        device = torch.device(torch.cuda.current_device() if torch.cuda.is_available() else "cpu")
        self.facenet = FaceFeatures("model_mobilefacenet").to(device).requires_grad_(False)
        self.verbose = verbose
        self.detect_face = detect_face
        self.max_threshold = max_threshold
        self.min_threshold = min_threshold
        if detect_face:
            from .face import face_checker
            self.fd = face_checker()
        trans_list = []
        trans_list += [Alb.Resize(112, 112, interpolation=cv2.INTER_AREA)]
        trans_list += [Alb.Normalize(mean=(0.5,0.5,0.5), std=(0.5,0.5,0.5))]
        trans_list += [ToTensorV2(transpose_mask=True)]
        self.trans = Alb.Compose(trans_list)
        self.template = []
        for fake_face in make_dataset(os.path.join(InsightFace_dir, 'virtual_faces')):
            self.template += [self.trans(image=np.array(Image.open(fake_face)))['image'].unsqueeze(0).to(device)]
        if len(self.template) == 0:
            raise RuntimeError("virtual_faces template is None, check dir: %s" % os.path.join(InsightFace_dir, 'virtual_faces'))


    def check_image(self, raw_img, keypoints=None):
        if self.detect_face:
            face_cnt = self.fd.check_image(raw_img)
            if face_cnt > 0:
                keypoints = np.array(self.fd.dets[0,5:])
                img, _ = norm_crop(raw_img, keypoints, output_size=112, antialias=True)
            else:
                if self.verbose:
                    print("no face detected.")
                return False
        else:
            img, _ = norm_crop(raw_img, keypoints, output_size=112, antialias=True)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        x = self.trans(image=rgb_img)['image'].unsqueeze(0).cuda()
        similarity = []
        one_of_close = False
        for i in range(len(self.template)):
            with torch.no_grad():
                distance = self.facenet.cosine_distance(x, self.template[i])
            similarity += [distance.item()]
            # similarity += distance * distance
            if distance < self.min_threshold:
                one_of_close = True
            if self.verbose:
                print(distance)
        similarity = np.array(similarity)
        median_sim = np.median(similarity)
        similarity = np.sqrt(np.mean(similarity * similarity))
        if self.verbose:
            print('final', similarity)
        if similarity < self.max_threshold or median_sim < self.max_threshold or one_of_close:
            return True
        else:
            return False

    def check_data(self, iap_data):
        for face in iap_data[1]['faces']:
            keypoints = np.array(face['key_points'])
            return not self.check_image(iap_data[0], keypoints)

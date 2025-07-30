import os
import torch
import numpy as np
import cv2
import albumentations as Alb
from albumentations.pytorch.transforms import ToTensorV2
from .models import FAN, get_preds_fromhm

class AdaptiveWing():
    def __init__(self):
        PRETRAINED_WEIGHTS = os.path.join(os.environ['TORCH_HOME'], 'WFLW_4HG.pth')    # too large, not included in package
        GRAY_SCALE = False
        HG_BLOCKS = 4
        END_RELU = False
        NUM_LANDMARKS = 98
        self.model_ft = FAN(HG_BLOCKS, END_RELU, GRAY_SCALE, NUM_LANDMARKS)
        checkpoint = torch.load(PRETRAINED_WEIGHTS, map_location=lambda storage, loc: storage)
        if 'state_dict' not in checkpoint:
            self.model_ft.load_state_dict(checkpoint)
        else:
            pretrained_weights = checkpoint['state_dict']
            model_weights = self.model_ft.state_dict()
            pretrained_weights = {k: v for k, v in pretrained_weights.items() \
                                if k in model_weights}
            model_weights.update(pretrained_weights)
            self.model_ft.load_state_dict(model_weights)

        if torch.cuda.is_available():
            self.model_ft = self.model_ft.cuda().eval()
        else:
            self.model_ft = self.model_ft.eval()

        trans_list = []
        trans_list += [Alb.Normalize(mean=(0.0,0.0,0.0), std=(1.0,1.0,1.0))]
        trans_list += [ToTensorV2(transpose_mask=True)]
        self.trans = Alb.Compose(trans_list)

    def detect(self, img_raw):
        '''Detect face landmarks in image, you should crop out face image before detection.

        Args:
            img_raw: 3-channels opencv image, cropped by face detector.

        Outs:
            out_landmarks: [98, 2] landmarks array
        '''
        img = cv2.resize(img_raw, (256,256), interpolation=cv2.INTER_AREA)
        x = self.trans(image=img)
        inputs = x['image'].unsqueeze(0).cuda()
        outputs, boundary_channels = self.model_ft(inputs)
        pred_heatmap = outputs[-1][:, :-1, :, :][0].detach().cpu()
        pred_landmarks, _ = get_preds_fromhm(pred_heatmap.unsqueeze(0))
        pred_landmarks = pred_landmarks.squeeze().numpy()
        out_landmarks = np.int64(pred_landmarks * 4)
        out_landmarks[:,0] = out_landmarks[:,0] * img_raw.shape[1] / 256
        out_landmarks[:,1] = out_landmarks[:,1] * img_raw.shape[0] / 256
        return out_landmarks

    @staticmethod
    def to_boundaries(landmarks_98):
        landmarks_98 = np.reshape(landmarks_98, (-1, 2))
        assert len(landmarks_98.shape) == 2
        boundaries = {}
        boundaries['full_landmarks'] = landmarks_98

        # parts
        boundaries['cheek'] = landmarks_98[0:33]
        boundaries['eyebrow_left'] = landmarks_98[33:42]
        boundaries['eyebrow_right'] = landmarks_98[42:51]
        boundaries['nose_ridge'] = landmarks_98[51:55]
        boundaries['nose_bot'] = landmarks_98[55:60]
        boundaries['eyelid_left'] = landmarks_98[60:68]
        boundaries['eyelid_right'] = landmarks_98[68:76]
        boundaries['lip_outer'] = landmarks_98[76:88]
        boundaries['lip_inner'] = landmarks_98[88:96]
        boundaries['upper_left_eyelid'] = landmarks_98[60:65]
        boundaries['upper_right_eyelid'] = landmarks_98[68:73]
        boundaries['lower_left_eyelid'] = landmarks_98[65:68]
        boundaries['lower_right_eyelid'] = landmarks_98[73:76]
        boundaries['lower_outer_lip'] = landmarks_98[[76, 87, 86, 85, 84, 83, 82]]

        # extra parts
        boundaries['eyebrow_left_bot'] = boundaries['eyebrow_left'][-4:]
        boundaries['eyebrow_right_bot'] = boundaries['eyebrow_right'][-4:]
        boundaries['cheek_left'] = boundaries['cheek'][:3]
        boundaries['cheek_right'] = boundaries['cheek'][-3:]
        boundaries['malar_bone'] = boundaries['cheek'][[2,-3]]
        boundaries['mandibular_angle'] = boundaries['cheek'][[8,-9]]

        # keypoints
        boundaries['chin'] = boundaries['cheek'][16]
        boundaries['eye_center_left'] = landmarks_98[96]
        boundaries['eye_center_right'] = landmarks_98[97]
        boundaries['nose_center'] = landmarks_98[54]
        boundaries['mouth_corner_left'] = landmarks_98[76]
        boundaries['mouth_corner_right'] = landmarks_98[82]
        boundaries['keypoints'] = landmarks_98[[96,97,54,76,82]]

        # ROI
        boundaries['nose'] = np.concatenate([boundaries['nose_ridge'], boundaries['nose_bot']])
        boundaries['eye_left'] = np.concatenate([boundaries['eyelid_left'], boundaries['eye_center_left'][np.newaxis,...]])
        boundaries['eye_right'] = np.concatenate([boundaries['eyelid_right'], boundaries['eye_center_right'][np.newaxis,...]])
        boundaries['mouth'] = np.concatenate([boundaries['lip_outer'], boundaries['lip_inner']])
        # boundaries['ROI'] = np.concatenate([boundaries['nose'], boundaries['eye_left'], boundaries['eye_right'], boundaries['mouth']])
        
        # Delaunay triangulation
        boundaries['triangulation'] = np.concatenate([boundaries['cheek'][::2],
                                                      boundaries['eyebrow_left'][:5:2],
                                                      boundaries['eyebrow_right'][:5:2],
                                                      boundaries['eyelid_left'][::2],
                                                      boundaries['eyelid_right'][::2],
                                                      boundaries['nose_ridge'],
                                                      boundaries['nose_bot'][::2],
                                                      boundaries['lip_outer'][::2]])

        # contours
        boundaries['ROI'] = np.concatenate([boundaries['upper_left_eyelid'], boundaries['upper_right_eyelid'], boundaries['lower_outer_lip'][::-1]])

        return boundaries

    @classmethod
    def cal_eyelid_closure(cls, lands):
        """Calculate closure score of eyelids. 
        Wide-open(0.35)，Normal(0.25)，Squint(0.2)，Close(0.1)

        Args:
            lands(array):            98 points landmars

        Outs:
            eyelid_closure(float):   closure score
        """
        bd = cls.to_boundaries(lands)

        eye_length_left = np.hypot(*(bd['eyelid_left'][4]-bd['eyelid_left'][0]))
        eyelid_res_left = [np.hypot(*(bd['eyelid_left'][8-i] - bd['eyelid_left'][i])) for i in range(1,4)]
        eyelid_closure_left = np.mean(eyelid_res_left) / eye_length_left

        eye_length_right = np.hypot(*(bd['eyelid_right'][4]-bd['eyelid_right'][0]))
        eyelid_res_right = [np.hypot(*(bd['eyelid_right'][8-i] - bd['eyelid_right'][i])) for i in range(1,4)]
        eyelid_closure_right = np.mean(eyelid_res_right) / eye_length_right

        eyelid_closure = (eyelid_closure_left + eyelid_closure_right) / 2

        return eyelid_closure

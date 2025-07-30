from __future__ import print_function
import os
import argparse
import torch
import torch.backends.cudnn as cudnn
import numpy as np
from .infer_module import cfg_mnet, cfg_slim, cfg_rfb, cfg_re50
from .infer_module.prior_box import PriorBox
from .utils.nms.py_cpu_nms import py_cpu_nms
import cv2
from .infer_module import retinaface
from .infer_module import retinaface_resnet50
from .infer_module.net_slim import Slim
from .infer_module.net_rfb import RFB
from .utils.box_utils import decode, decode_landm
import albumentations as Alb


def check_keys(model, pretrained_state_dict):
    ckpt_keys = set(pretrained_state_dict.keys())
    model_keys = set(model.state_dict().keys())
    used_pretrained_keys = model_keys & ckpt_keys
    unused_pretrained_keys = ckpt_keys - model_keys
    missing_keys = model_keys - ckpt_keys
    print('Missing keys:{}'.format(len(missing_keys)))
    print('Unused checkpoint keys:{}'.format(len(unused_pretrained_keys)))
    print('Used keys:{}'.format(len(used_pretrained_keys)))
    assert len(used_pretrained_keys) > 0, 'load NONE from pretrained checkpoint'
    return True


def remove_prefix(state_dict, prefix):
    ''' Old style model is stored with all names of parameters sharing common prefix 'module.' '''
    print('remove prefix \'{}\''.format(prefix))
    f = lambda x: x.split(prefix, 1)[-1] if x.startswith(prefix) else x
    return {f(key): value for key, value in state_dict.items()}


def load_model(model, pretrained_path, load_to_cpu):
    print('Loading pretrained model from {}'.format(pretrained_path))
    if load_to_cpu:
        pretrained_dict = torch.load(pretrained_path, map_location=lambda storage, loc: storage)
    else:
        device = torch.cuda.current_device()
        pretrained_dict = torch.load(pretrained_path, map_location=lambda storage, loc: storage.cuda(device))
    if "state_dict" in pretrained_dict.keys():
        pretrained_dict = remove_prefix(pretrained_dict['state_dict'], 'module.')
    else:
        pretrained_dict = remove_prefix(pretrained_dict, 'module.')
    check_keys(model, pretrained_dict)
    model.load_state_dict(pretrained_dict, strict=False)
    return model


class face_detector():
    def __init__(self, name, conf_thres=0.02):
        self.cfg = None
        self.net = None
        current_path = os.path.dirname(os.path.abspath(__file__))
        if name == "mobile0.25":
            self.cfg = cfg_mnet
            self.net = retinaface.RetinaFace(cfg=self.cfg, phase='test')
            weights_path = os.path.join(current_path, 'weights/mobilenet0.25_Final.pth')
        elif name == "slim":
            self.cfg = cfg_slim
            self.net = Slim(cfg=self.cfg, phase='test')
            weights_path = os.path.join(current_path, 'weights/slim_Final.pth')
        elif name == "RBF":
            self.cfg = cfg_rfb
            self.net = RFB(cfg=self.cfg, phase='test')
            weights_path = os.path.join(current_path, 'weights/RBF_Final.pth')
        elif name == "Resnet50":
            self.cfg = cfg_re50
            self.net = retinaface_resnet50.RetinaFace(cfg=self.cfg, phase='test')
            weights_path = os.path.join(os.environ['TORCH_HOME'], 'Resnet50_Final.pth')
        else:
            raise RuntimeError(f"Model {name} is not supported!")
            exit(0)

        if torch.cuda.is_available():
            self.net = load_model(self.net, weights_path, False)
            self.net.eval().cuda().requires_grad_(False)
            self.cuda = True
        else:
            self.net = load_model(self.net, weights_path, True)
            self.net.eval().requires_grad_(False)
            self.cuda = False
        self.long_side = 640
        self.confidence_threshold = conf_thres
        self.top_k = 5000
        self.nms_threshold = 0.4
        self.keep_top_k = 750
        self.vis_thres = 0.6

    def detect(self, img_raw, origin_size=True, save_image=False):
        '''Detect faces in image, you may need to pad image if detect in selfie.

        Args:
            img_raw: 3-channels opencv image.
            origin_size: Whether use origin image size to evaluate
            save_image: Whether to save image

        Outs:
            dets: Detected face boxes and landmarks in shape [n, 15]
                face boxes index [0-4], lx, ly, rx, ry, confidence
                landmarks index [5-14], leye xy, reye xy, nose xy, lcorn xy, rcorn xy
        '''
        img = np.float32(img_raw)

        # testing scale
        target_size = self.long_side
        max_size = self.long_side
        im_shape = img.shape
        im_size_min = np.min(im_shape[0:2])
        im_size_max = np.max(im_shape[0:2])
        resize = float(target_size) / float(im_size_min)
        # prevent bigger axis from being more than max_size:
        if np.round(resize * im_size_max) > max_size:
            resize = float(max_size) / float(im_size_max)
        if origin_size:
            resize = 1

        if resize != 1:
            img = cv2.resize(img, None, None, fx=resize, fy=resize, interpolation=cv2.INTER_LINEAR)
        im_height, im_width, _ = img.shape

        scale = torch.Tensor([img.shape[1], img.shape[0], img.shape[1], img.shape[0]])
        img -= (104, 117, 123)
        img = img.transpose(2, 0, 1)
        img = torch.from_numpy(img).unsqueeze(0)
        img = img.cuda() if self.cuda else img
        scale = scale.cuda() if self.cuda else scale

        loc, conf, landms = self.net(img)  # forward pass

        priorbox = PriorBox(self.cfg, image_size=(im_height, im_width))
        priors = priorbox.forward()
        priors = priors.cuda() if self.cuda else priors
        prior_data = priors.data
        boxes = decode(loc.data.squeeze(0), prior_data, self.cfg['variance'])
        boxes = boxes * scale / resize
        boxes = boxes.cpu().numpy()
        scores = conf.squeeze(0).data.cpu().numpy()[:, 1]
        landms = decode_landm(landms.data.squeeze(0), prior_data, self.cfg['variance'])
        scale1 = torch.Tensor([img.shape[3], img.shape[2], img.shape[3], img.shape[2],
                                img.shape[3], img.shape[2], img.shape[3], img.shape[2],
                                img.shape[3], img.shape[2]])
        scale1 = scale1.cuda() if self.cuda else scale1
        landms = landms * scale1 / resize
        landms = landms.cpu().numpy()

        # ignore low scores
        inds = np.where(scores > self.confidence_threshold)[0]
        boxes = boxes[inds]
        landms = landms[inds]
        scores = scores[inds]

        # keep top-K before NMS
        order = scores.argsort()[::-1][:self.top_k]
        boxes = boxes[order]
        landms = landms[order]
        scores = scores[order]

        # do NMS
        dets = np.hstack((boxes, scores[:, np.newaxis])).astype(np.float64, copy=False)
        keep = py_cpu_nms(dets, self.nms_threshold)
        # keep = nms(dets, self.nms_threshold,force_cpu=False)
        dets = dets[keep, :]
        landms = landms[keep]

        # keep top-K faster NMS
        dets = dets[:self.keep_top_k, :]
        landms = landms[:self.keep_top_k, :]
        dets = np.concatenate((dets, landms), axis=1)

        # show image
        if save_image:
            img_disp = self.draw_dets_image(img_raw, dets)
            name = "test.jpg"
            cv2.imwrite(name, img_disp)
        return dets

    def draw_dets_image(self, img_raw, dets):
        img_disp = np.uint8(img_raw.copy())
        for b in dets:
            if b[4] < self.vis_thres:
                continue
            text = "{:.4f}".format(b[4])
            b = list(map(int, b))
            cv2.rectangle(img_disp, (b[0], b[1]), (b[2], b[3]), (0, 0, 255), 2)
            cx = b[0]
            cy = b[1] + 12
            cv2.putText(img_disp, text, (cx, cy),
                        cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255))

            cv2.circle(img_disp, (b[5], b[6]), 1, (0, 0, 255), 4)
            cv2.circle(img_disp, (b[7], b[8]), 1, (0, 255, 255), 4)
            cv2.circle(img_disp, (b[9], b[10]), 1, (255, 0, 255), 4)
            cv2.circle(img_disp, (b[11], b[12]), 1, (0, 255, 0), 4)
            cv2.circle(img_disp, (b[13], b[14]), 1, (255, 0, 0), 4)
        return img_disp

    def transfer_dets(self, dets, trans_mat):
        landmarks = np.delete(dets, 4, axis=1)
        landmarks = np.reshape(landmarks, [dets.shape[0], -1, 2])
        trans_landmarks = np.matmul(np.insert(landmarks, 2, 1, axis=-1), trans_mat)
        trans_landmarks = np.reshape(trans_landmarks, [dets.shape[0], -1])
        trans_dets = np.insert(trans_landmarks, 4, dets[:,4], axis=1)
        return trans_dets

    def detect_selfie(self, img_raw):
        '''Detecting face with image padding to double longest size. This may great helpful in selfie.

        Args:
            img_raw: 3-channels opencv image.

        Outs:
            dets: Detected face boxes and landmarks in shape [n, 15]
                face boxes index [0-4], lx, ly, rx, ry, confidence
                landmarks index [5-14], leye xy, reye xy, nose xy, lcorn xy, rcorn xy
        '''
        long_size = img_raw.shape[0] if img_raw.shape[0] > img_raw.shape[1] else img_raw.shape[1]
        trans_list = []
        trans_list += [Alb.PadIfNeeded(min_height=long_size*2, min_width=long_size*2, border_mode=cv2.BORDER_CONSTANT, value=0)]
        trans_list += [Alb.Resize(self.long_side, self.long_side, interpolation=cv2.INTER_AREA)]
        trans = Alb.Compose(trans_list)
        img = trans(image=img_raw)['image']
        dets = self.detect(img, origin_size=True)
        if len(dets) > 0:
            x_bias = long_size - img_raw.shape[1] // 2
            y_bias = long_size - img_raw.shape[0] // 2
            scale_ratio = long_size*2.0 / self.long_side
            trans_mat = np.zeros([3,2])
            trans_mat[0,0] = scale_ratio
            trans_mat[1,1] = scale_ratio
            trans_mat[2,0] = -x_bias
            trans_mat[2,1] = -y_bias
            trans_dets = self.transfer_dets(dets, trans_mat)
            return trans_dets
        else:
            return dets


import os
import cv2
import numpy as np
from functools import wraps
import torch
import albumentations as Alb
from albumentations.pytorch.transforms import ToTensorV2
from .imageutils import resize_fix
from .fileutils import get_ext_name, SUPPORTED_VIDEO_EXTENSIONS

__all__ = ["to_tensor", "to_image", 'scale_min_max', "get_random_data", "SubscriDict"]

def scale_min_max(array, min_v, max_v, percentile=100.0):
    '''
    Scales array values between user-defined min and max, after applying a percentile.

    Args:
        array(array):       Array to be scaled. Can be of any dimension. 
                            Example: np.array([1, 2, 3, 4, 5])
        min_v(float):       Desired minimum value for the scaled array.
                            Example: -1.0
        max_v(float):       Desired maximum value for the scaled array.
                            Example: 1.0
        percentile(float):  Percentile to be considered for scaling. 
                            Must be in the range (50.0, 100.0]. Default is 100.0.
                            Example: 90 (considering 90th percentile)

    Returns:
        array_scaled(array): The scaled array with same dimensions as input.
    '''
    assert max_v > min_v
    assert percentile <= 100.0 and percentile > 50.0
    Q_min = np.percentile(array, 100.0-percentile)
    Q_max = np.percentile(array, percentile)
    scale_v = max_v - min_v
    array_scaled = scale_v * (array - Q_min) / (Q_max - Q_min) + min_v
    array_scaled = np.clip(array_scaled, min_v, max_v)
    return array_scaled


def to_tensor(img, shape=None, cvtcolor=True, mean=(0.5,0.5,0.5), std=(0.5,0.5,0.5)):
    '''
        shape(list):     (H, W)
    '''
    img = img.reshape([img.shape[0], img.shape[1], -1])
    if img.shape[-1] != 3:
        cvtcolor = False
        mean = (mean[0],) * img.shape[-1]
        std = (std[0],) * img.shape[-1]
    trans_list = []
    trans_list += [Alb.Normalize(mean=mean, std=std)]
    trans_list += [ToTensorV2(transpose_mask=True)]
    trans = Alb.Compose(trans_list, additional_targets={'image0': 'image'})
    if cvtcolor:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    if shape:
        img = resize_fix(img, shape[0], shape[1], pad_method=cv2.BORDER_CONSTANT)
    tensor = trans(image=img)['image'].unsqueeze(0)
    return tensor

def to_image(tensor, cvtcolor=False):
    if isinstance(tensor, list) or (len(tensor.shape) == 4):
        img_list = [to_image(tensor[i], cvtcolor=cvtcolor) for i in range(len(tensor))]
        return img_list
    img = (tensor.detach() + 1) * 127.5
    img = img.clamp(0, 255).cpu().numpy()
    img = img.transpose(1,2,0)
    img = np.uint8(img)
    if cvtcolor and img.shape[-1] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    elif cvtcolor and img.shape[-1] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGRA)
    return img


def get_random_data(dataset, func=None, out_size=None, out_format='BGR'):
    '''Get random data for testing.

    Args:
        dataset(str/list):         video path or image path list
        out_size(tuple):           resize if specify in (h, w), specify interpolation mode via (h, w, cv2.INTER_XXX)
        out_format(str):           output format, from BGR to one of TENSOR or RGB or BGR(default)

    Outs:
        test_img(array):
        (data_name, randnum):      name and index of data in dataset
    '''
    trans_list = []
    if out_size:
        trans_list += [Alb.Resize(*out_size)]
    trans_list += [Alb.Normalize(mean=(0.5,0.5,0.5), std=(0.5,0.5,0.5))]
    trans_list += [ToTensorV2(transpose_mask=True)]
    trans = Alb.Compose(trans_list, additional_targets={'image0': 'image'})
    if get_ext_name(dataset) in SUPPORTED_VIDEO_EXTENSIONS:
        capture = cv2.VideoCapture(dataset)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        randnum = np.random.randint(0, frame_count, 1)[0]
        data_name = dataset
        capture.set(cv2.CAP_PROP_POS_FRAMES, randnum)
        ret, test_img = capture.read()
    else:
        randnum = np.random.randint(0, len(dataset), 1)[0]
        try:
            data_name = dataset[randnum]
            test_img = cv2.imread(data_name)
        except:
            data_name = ''
            test_img = dataset[randnum]

    if func:
        test_img = func(test_img)

    if out_format == 'TENSOR':
        test_img = cv2.cvtColor(test_img, cv2.COLOR_BGR2RGB)
        test_img = trans(image=test_img)['image'].unsqueeze(0)
    elif out_format == 'RGB':
        test_img = cv2.cvtColor(test_img, cv2.COLOR_BGR2RGB)

    return test_img, (data_name, randnum)


class SubscriDict():
    def __init__(self, d):
        self.d = d
        self.d_keys = list(d.keys())

    def __getitem__(self, item):
        if isinstance(item, slice):
            return {key:self.d[key] for key in self.d_keys[item]}
        elif isinstance(item, list):
            if isinstance(item[0], str):
                return {key:self.d[key] for key in item}
            return {self.d_keys[idx]:self.d[self.d_keys[idx]] for idx in item}
        elif isinstance(item, str):
            return self.d[item]
        else:
            return self.d[self.d_keys[item]]

    def __len__(self):
        return len(self.d)

    def size(self):
        full_size = 0
        for k in self.d_keys:
            if isinstance(k, list):
                full_size += len(k)
            else:
                full_size += 1
        return full_size

import numpy as np
import torch
import torch.nn.functional as F
from .imageutils import warpAffine
from ..faceutils import cal_eye_dist, generate_contours_mask
from ...thirdparty.AdaptiveWing import AdaptiveWing
from ...thirdparty.InsightFace.face_align import estimate_norm

__all__ = ["cal_ROI_AUC", "cal_ROI_metric", "crop_face_v3_tensor", "norm_crop_tensor"]


# TODO: face_anno to mask input
def cal_ROI_AUC(pred, gt, face_anno, dscale=0.3, eye_mouth_only=True, return_curve=False):
    '''Calculate pixel similarity AUC in face ROI area.

    Args:
        pred(tensor):      [N,C,H,W] network prediction torch tensor, values in [-1, 1]
        gt(tensor):        [N,C,H,W] groundtruth torch tensor, values in [-1, 1]
        face_anno(dict):   AdaptiveWing predict results should be contained in face_anno['landmarks']

    Outs:
        AUC(float):        AUC score for pixel similarity between prediction and groundtruth
    '''
    ac_curve = []
    bounds = AdaptiveWing.to_boundaries(np.array(face_anno['landmarks']))
    eye_dist = cal_eye_dist(bounds)
    dsize = int(eye_dist*dscale)
    if eye_mouth_only:
        contours = [np.int64(bounds['eyelid_left']), np.int64(bounds['eyelid_right']), np.int64(bounds['lip_outer'])]
    else:
        contours = [np.int64(bounds['ROI'])]
    fg_mask = generate_contours_mask(pred.shape[2], pred.shape[3], contours, blur=False, dsize=dsize)
    fg_mask_gpu = torch.from_numpy(fg_mask[np.newaxis,np.newaxis,:,:]).cuda(non_blocking=True)
    diff_map = torch.sum(torch.abs(pred-gt), axis=1, keepdim=True)
    diff_map = diff_map * fg_mask_gpu
    n = torch.sum(fg_mask_gpu)
    xs = 1-np.logspace(0, 2, 100, endpoint=False)/100   # In case of higher metric matter
    xs = xs[::-1]
    # xs = np.logspace(0, 3, 50)*2/1000                   # In case of lower metric matter
    # xs = np.linspace(0, 2.0, 100)                       # In case of uniform metric matter
    for factor in xs:
        TF = torch.sum(diff_map > factor)
        accuracy = 1 - TF / n
        ac_curve += [accuracy.item()]
    AUC = np.mean(ac_curve)
    if return_curve:
        return AUC, ac_curve
    else:
        return AUC

# TODO: face_anno to mask input
def cal_ROI_metric(pred, gt, face_anno, metric, dscale=0.3, eye_mouth_only=True):
    '''Calculate metric loss in face ROI area.

    Args:
        pred(tensor):      [N,C,H,W] network prediction torch tensor, values in [-1, 1]
        gt(tensor):        [N,C,H,W] groundtruth torch tensor, values in [-1, 1]
        face_anno(dict):   AdaptiveWing predict results should be contained in face_anno['landmarks']

    Outs:
        loss(tensor):      metric loss between prediction and groundtruth
    '''
    bounds = AdaptiveWing.to_boundaries(np.array(face_anno['landmarks']))
    eye_dist = cal_eye_dist(bounds)
    dsize = int(eye_dist*dscale)
    if eye_mouth_only:
        contours = [np.int64(bounds['eyelid_left']), np.int64(bounds['eyelid_right']), np.int64(bounds['lip_outer'])]
    else:
        contours = [np.int64(bounds['ROI'])]
    fg_mask = generate_contours_mask(pred.shape[2], pred.shape[3], contours, blur=False, dsize=dsize)
    fg_mask_gpu = torch.from_numpy(fg_mask[np.newaxis,np.newaxis,:,:]).cuda(non_blocking=True)
    loss = metric(pred*fg_mask_gpu, gt*fg_mask_gpu)
    return loss.squeeze()


def crop_face_v3_tensor(img, keypoints, landmarks, rotate=True, output_size=None, **kwargs):
    '''Crop face ROI according to cheek corner and eye-mouth distance.

    Notice:
        - Crop whole face region

    Args:
        img(tensor):            torch tensor
        keypoints(array):       eye_left, eye_right, mouth_left, mouth_right in (x, y)
        landmarks(array):       landmarks with [0, 32] corresponding cheek contour
        rotate(bool):           if rotate image
        output_size(int/tuple): output: [h,w] = [output_size, output_size/ratio] or [output_size[0], output_size[1]]

    Optional:
        ratio(float):           output h/w ratio
        use_chin(bool):         if using chin point to shift up face rect, work well when making dataset
        no_img(bool):           calculate warp_mat only 

    Outs:
        crop_img(array)
        warp_mat(array):        used to align points or recover alignment
    '''
    keypoints = np.array(keypoints)
    if keypoints.shape == (10, ):
        eye_left, eye_right, _, mouth_left, mouth_right = np.reshape(keypoints, [-1,2])
    elif keypoints.shape == (8, ):
        eye_left, eye_right, mouth_left, mouth_right = np.reshape(keypoints, [-1,2])
    elif keypoints.shape == (5, 2):
        eye_left, eye_right, _, mouth_left, mouth_right = keypoints
    elif keypoints.shape == (4, 2):
        eye_left, eye_right, mouth_left, mouth_right = keypoints
    else:
        raise ValueError("key points shape", keypoints.shape, "error.")

    eye_avg      = (eye_left + eye_right) * 0.5
    eye_to_eye   = eye_right - eye_left
    mouth_avg    = (mouth_left + mouth_right) * 0.5
    eye_to_mouth = mouth_avg - eye_avg
    use_chin = kwargs.get('use_chin', False)
    no_img = kwargs.get('no_img', False)
    hp_factor = kwargs.get('hp_factor', 1.7)
    wd_factor = kwargs.get('wd_factor', 0.6)
    shift_factor = kwargs.get('shift_factor', 1.1)
    antialias = kwargs.get('antialias', False)
    if isinstance(output_size, (tuple, list)):
        output_size_h = int(output_size[0])
        output_size_w = int(output_size[1])
        ratio = output_size_h / output_size_w
    elif isinstance(output_size, int):
        ratio = kwargs.get('ratio', 1.0)
        output_size_h = int(output_size)
        output_size_w = int(output_size / ratio)
    else:
        ratio = kwargs.get('ratio', 1.0)
        output_size_h = 0
        output_size_w = 0
        antialias = False    # antialias set to false when output_size is not specify

    left_cheek_corner = np.mean(landmarks[:6], axis=0)
    right_cheek_corner = np.mean(landmarks[33-6:33], axis=0)
    center = (right_cheek_corner+left_cheek_corner) / 2.0
    cheek_vector = right_cheek_corner - left_cheek_corner

    if use_chin:
        chin = np.mean(landmarks[15:18], axis=0)
        center_to_chin = chin - center
        hp_dst = np.hypot(*eye_to_mouth) * hp_factor
        ms_dst = np.hypot(*center_to_chin)
        shift_factor = shift_factor if hp_dst / shift_factor > ms_dst else 1.0    # need to slightly shift up face_rect in common case
        face_height_half = max(hp_dst, ms_dst)
    else:
        hp_dst = np.hypot(*eye_to_mouth) * hp_factor
        face_height_half = hp_dst
    face_width_half = np.hypot(*cheek_vector) * wd_factor

    rectify_height_half = face_width_half * ratio
    if rectify_height_half < face_height_half:
        rectify_height_half = face_height_half
        rectify_width_half = face_height_half / ratio
    else:
        rectify_width_half = face_width_half

    rect_height = rectify_height_half * 2.0
    rect_width = rectify_width_half * 2.0

    if output_size and not antialias:
        scale = output_size_h / rect_height
        warp_height = output_size_h
        warp_width = output_size_w
    else:
        scale = 1.0
        warp_height = int(rect_height)
        warp_width = int(rect_width)

    if rotate:
        rad = np.arctan2(cheek_vector[1], cheek_vector[0])
    else:
        rad = 0.0

    start_x = center[0] - rectify_width_half * scale
    start_y = center[1] - rectify_height_half * shift_factor * scale
    alpha=scale*np.cos(rad)
    beta=scale*np.sin(rad)
    warp_mat = np.array([[alpha, beta, (1-alpha)*center[0]-beta*center[1]], [-beta, alpha, beta*center[0]+(1-alpha)*center[1]]])
    warp_mat[0,2] -= start_x
    warp_mat[1,2] -= start_y
    if no_img:
        crop_img = None
    else:
        crop_img = warpAffine(img, warp_mat, (img.shape[0], img.shape[1], warp_height, warp_width))
        if antialias:
            crop_img = F.interpolate(crop_img, (output_size_h, output_size_w), mode='area')

    if antialias:
        warp_mat *= output_size_h / rect_height

    return crop_img, warp_mat


def norm_crop_tensor(img, keypoints, output_size=None, mode='arcface', **kwargs):
    no_img = kwargs.get('no_img', False)
    antialias = kwargs.get('antialias', False)
    keypoints = np.reshape(keypoints, [-1,2])
    eye_dist = np.hypot(*(keypoints[1]-keypoints[0]))

    in_size = 112 if mode == 'arcface' else 224
    M, pose_index = estimate_norm(keypoints, in_size, mode)

    std_face = arcface_src[0] if mode == 'arcface' else src_map[224][pose_index]
    std_dist = np.hypot(*(std_face[1]-std_face[0]))
    face_size = 224 * eye_dist / std_dist
    warp_size = int(face_size) if output_size is None or antialias else int(output_size)
    M *= warp_size / in_size

    if no_img:
        crop_img = None
    else:
        crop_img = warpAffine(img, M, (img.shape[0], img.shape[1], warp_size, warp_size))
        if antialias:
            crop_img = F.interpolate(crop_img, (output_size, output_size), mode='area')
    if antialias:
        M *= output_size / warp_size
    return crop_img, M

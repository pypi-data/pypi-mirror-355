import os
import cv2
import numpy as np
import torch
import torch.nn.functional as F

__all__ = ["affine2theta", "cal_residual_diff_tensor", "color_calibration_tensor", 
           "crop_tensor", "ordinary_ridge_regression", "resize_fix_tensor", 
           "resize_scale_tensor", "warpAffine"]


def cal_residual_diff_tensor(tensor_a, tensor_b, method='', fg_mask=None):
    '''Calculate residual standard deviation value of two tensor.

    Args:
        method(array):        'color': calculate standard diviation map 
                                         if img_a and img_b is mainly 
                                         different in color channel

    Outs:
        diff_v(float)
    '''
    res = tensor_a - tensor_b
    if fg_mask is not None:
        res = res * fg_mask
    diff_map = torch.std(res, dim=1) if 'color' in method else res
    if fg_mask is not None:
        diff_v = torch.sum(diff_map) / torch.sum(fg_mask)
    else:
        diff_v = torch.mean(diff_map)
    return diff_v

def color_calibration_tensor(roi_img, roi_ref):
    '''Get color calibration matrix from roi_img to roi_ref.

    Args:
        roi_img(tensor):            pytorch tensor in [3, n] or [3*n]
        roi_ref(tensor):            pytorch tensor in [3, n] or [3*n]

    Outs:
        trans_mat(tensor):          matrix transfer color from roi_img to roi_ref in [4, 3]

    Usage:
        clib_img = np.uint8(np.clip(np.matmul(np.insert(img.reshape(-1,3), [3], 1, axis=-1), trans_mat).reshape(img.shape), 0, 255))
    '''
    roi_mat = roi_img.reshape((3, -1))
    poi_img_mat = torch.cat([roi_mat, torch.ones(1, roi_mat.shape[1], device=roi_mat.device)], axis=0).transpose(1,0)
    poi_ref_mat = roi_ref.reshape(3, -1).transpose(1,0)
    trans_mat_t = torch.matmul(torch.matmul(torch.linalg.pinv(torch.matmul(poi_img_mat.transpose(1,0), poi_img_mat)), poi_img_mat.transpose(1,0)), poi_ref_mat)
    return trans_mat_t


def ordinary_ridge_regression(X, y, penalty):
    '''

    Args:
        X(tensor):        pytorch tensor in [1, M]
        y(tensor):        pytorch tensor in [1, M]

    Outs:
        A(tensor):        matrix transfer from X to y
    '''
    X = torch.cat([X, torch.ones((1, X.shape[1]), device=X.device)], axis=0)
    lam = penalty * torch.eye(X.shape[0])
    lam[1,1] = 0.0
    A = torch.linalg.pinv(X.T @ X + lam) @ X.T @ y
    return A


# def apply_calibration_tensor(img_tensor, trans_mat_t):
#     '''Apply color calibration matrix from roi_img to roi_ref.

#     Args:
#         img_tensor(tensor):             pytorch tensor in [N, C, H, W]
#         trans_mat_t(tensor):            pytorch tensor in  [N, C+1, C]

#     Outs:
#         calib_tensor(tensor):           pytorch tensor in  [N, C, H, W]
#     '''
#     img_mat = img_tensor.permute((0,2,3,1))
#     img_mat = img_mat.reshape((-1, 1, img_mat.shape[3]))
#     img_mat = torch.cat([img_mat, torch.ones((img_mat.shape[0], img_mat.shape[1], 1), device=img_mat.device)], axis=-1)
#     res = torch.bmm(img_tensor, trans_mat_t)
#     res = res.reshape((img_tensor.shape[0], img_tensor.shape[2], img_tensor.shape[3], img_tensor.shape[1]))
#     res = res.permute((0,3,1,2))
#     return res


def affine2theta(warp_mat, in_size, out_size):
    bs = warp_mat.shape[0]
    W1 = in_size[3]
    H1 = in_size[2]
    W2 = out_size[3]
    H2 = out_size[2]
    warp_wh_2 = np.array([2/W2, 0, -1, 0, 2/H2, -1, 0, 0, 1]).reshape(1,3,3).repeat(bs, axis=0)
    warp_wh_1 = np.array([W1/2, 0, W1/2, 0, H1/2, H1/2, 0, 0, 1]).reshape(1,3,3).repeat(bs, axis=0)
    warp_mat_r = np.insert(warp_mat, [2], [0,0,1], axis=1)
    aff_theta = torch.from_numpy(np.linalg.pinv(warp_wh_2 @ warp_mat_r @ warp_wh_1))[:,:2].type(torch.float32)
    return aff_theta

def warpAffine(src, M, out_size, interp_mode='bilinear', align_corners=True, padding_mode="zeros"):
    '''Applies an affine transformation to an image.

    Notice:
        - Unlike OpenCV, resolution and H/W ratio is affected by out_size
        - Only tested in keeping H/W ratio warp affine

    Args:
        src(Tensor):           (NxCxHxW) input image
        M(array):              (2x3) or (Nx2x3) OpenCV affine transform matrix
        out_size(Tensor):      (4) Tensor size

    Outs:
        dst(Tensor)
    '''
    M = M if len(M.shape) == 3 else M[np.newaxis,:].repeat(src.shape[0], axis=0)
    W1 = src.size()[3]
    H1 = src.size()[2]
    W2 = out_size[3]
    H2 = out_size[2]
    # keep resolution when shinking
    if W1 > W2 and H1 > H2:
        out_size = src.size()
    # deterministic algorithms supported
    if os.environ.get('DETERMINISTIC_TEST') == "True":
        imgs = src.detach().cpu().numpy()
        imgs_t = imgs.transpose(0,2,3,1)
        dst_img = []
        for i in range(M.shape[0]):
            tmp_img = cv2.warpAffine(imgs_t[i], M[i], (out_size[3], out_size[2]))[np.newaxis,...]
            dst_img.append(tmp_img.transpose(0,3,1,2))
        dst = torch.from_numpy(np.concatenate(dst_img, axis=0)).cuda()
    else:
        # aff_theta (Nx2x3)
        aff_theta = affine2theta(M, src.size(), out_size)
        # grid (NxHxWx2)
        grid = torch.nn.functional.affine_grid(aff_theta.cuda(), out_size, align_corners=align_corners)
        dst = torch.nn.functional.grid_sample(src.cuda(), grid, mode=interp_mode, align_corners=align_corners, padding_mode=padding_mode)
        dst = dst[:,:,:H2,:W2]
    return dst

## simplify version (Not tested)
# def affine2theta(param, w, h):
#     param = np.linalg.inv(param)
#     theta = np.zeros([2,3])
#     theta[0,0] = param[0,0]
#     theta[0,1] = param[0,1]*h/w
#     theta[0,2] = param[0,2]*2/w + theta[0,0] + theta[0,1] - 1
#     theta[1,0] = param[1,0]*w/h
#     theta[1,1] = param[1,1]
#     theta[1,2] = param[1,2]*2/h + theta[1,0] + theta[1,1] - 1
#     theta = torch.from_numpy(theta).unsqueeze(0).type(torch.float32)
#     return theta

def resize_scale_tensor(src_img, scale=1.0, align_length=0, align_flag='height', interp='bilinear', align_grid=0):
    """Scale resize input image.

    Args:
        src_img: Input image, torch tensor, in [N, C, H, W]
        scale: Scale ratio, default 1.0
        align_length: Align length, auto infer scale param, default 0
        align_flag: 'height' or 'width' to align, default 'height'
        interp: interpolation method, default bilinear
        align_grid: Special use for 2x upsample network

    Outs:
        Resized image
    """
    def apply_align_grid(length, grid):
        return grid * (length // grid)

    if scale == 1.0 and align_length == 0:
        return src_img
    elif align_length > 0:
        if align_flag == 'height':
            align_w = int(src_img.shape[3] * align_length / src_img.shape[2])
            align_w = apply_align_grid(align_w, align_grid) if align_grid > 0 else align_w
            resize_img = F.interpolate(src_img, size=(align_length, align_w), mode=interp)
        elif align_flag == 'width':
            align_h = int(src_img.shape[2] * align_length / src_img.shape[3])
            align_h = apply_align_grid(align_h, align_grid) if align_grid > 0 else align_h
            resize_img = F.interpolate(src_img, size=(align_h, align_length), mode=interp)
        else:
            print('resize_scale(): unkown align_flag %s' % align_flag)
            return
    elif scale != 1.0:
        align_w = int(src_img.shape[3] * scale)
        align_h = int(src_img.shape[2] * scale)
        align_w = apply_align_grid(align_w, align_grid) if align_grid > 0 else align_w
        align_h = apply_align_grid(align_h, align_grid) if align_grid > 0 else align_h
        resize_img = F.interpolate(src_img, size=(align_h, align_w), mode=interp)
    else:
        print('resize_scale(): error input align_length or scale')
        return src_img
    return resize_img


def resize_fix_tensor(src_img, dst_h, dst_w, flag='pad'):
    """Fix source image size to a fixed size.

    Args:
        src_img:        Input image, torch tensor, in [N, C, H, W]
        dst_h:          Fixed height
        dst_w:          Fixed width
        flag:           Resize flag: 'pad' or 'crop', default 'pad'
                                    pad: Resize according image's long size and pad 0 to fix short size
                                    crop: Resize according image's short size and crop center to fix long size
    
    Outs:
        fixed-size image
        fix-scale shape
    """
    src_h = src_img.shape[2]
    src_w = src_img.shape[3]
    src_ratio = np.float32(src_h)/np.float32(src_w)
    dst_ratio = np.float32(dst_h)/np.float32(dst_w)

    if src_ratio > dst_ratio:
        if flag == 'crop':
            align_flag = 1
            resize_img = resize_scale_tensor(src_img, align_length=dst_w, align_flag='width')
            crop_start = int((resize_img.shape[2] - dst_h) / 2)
            fixed_img = resize_img[:, :, crop_start:crop_start + dst_h, :]
        elif flag == 'pad':
            align_flag = 0
            resize_img = resize_scale_tensor(src_img, align_length=dst_h, align_flag='height')
            fixed_img = torch.zeros((src_img.shape[0],src_img.shape[1],dst_h,dst_w), device=src_img.device)
            fixed_img[:,:,:resize_img.shape[2], :resize_img.shape[3]] = resize_img
        else:
            print("fix_to_image_size(): error input flag.")
            return
    else:
        if flag == 'crop':
            align_flag = 0
            resize_img = resize_scale_tensor(src_img, align_length=dst_h, align_flag='height')
            crop_start = int((resize_img.shape[3] - dst_w) / 2)
            fixed_img = resize_img[:, :, :, crop_start:crop_start + dst_w]
        elif flag == 'pad':
            align_flag = 1
            resize_img = resize_scale_tensor(src_img, align_length=dst_w, align_flag='width')
            fixed_img = torch.zeros((src_img.shape[0],src_img.shape[1],dst_h,dst_w), device=src_img.device)
            fixed_img[:,:,:resize_img.shape[2], :resize_img.shape[3]] = resize_img
        else:
            print("fix_to_image_size(): error input flag.")
            return

    return fixed_img


def crop_tensor(img, shape, position='ssss'):
    '''Crop a sub-tensor according position.

    Args:
        img(tensor):            pytorch tensor
        shape(tuple/array):     target sub-tensor shape
        position:               code of targe sub-tensor position: s(start), c(center), e(end)

    Outs:
    '''
    assert(len(shape) == 4)
    if position == 'ssss':
        return img[:shape[0], :shape[1], :shape[2], :shape[3]]
    elif position == 'eeee':
        return img[-shape[0]:, -shape[1]:, -shape[2]:, -shape[3]:]
    else:
        raise NotImplementedError('%s not implemented' % position)

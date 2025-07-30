import cv2
import numpy as np
from matplotlib import pyplot as plt
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn import linear_model
from .fileutils import check_image_format

SUPPORTED_BOX_FORMAT = ['ltrb', 'ltwh', 'cxywh', 'cw']

__all__ = ["apply_calibration", "apply_mask", "apply_mask_merge", "cal_bounding_rect", 
           "cal_color_hist", "cal_residual_diff", "cal_residual_image", "color_calibration", 
           "color_calibration_v2", "crop_center", "crop_rect", "crop_roi_points_image", 
           "cvt_box_format", "cvt_color", "fill_roi_image", "gaussian_kernel", "generate_log_filter", 
           "get_colormap_array", "get_rounded_rect", "masked_gaussian_blur", "pad_center", 
           "pad_rect", "resize_alignrect", "resize_fix", "resize_like", "resize_scale",
           "SUPPORTED_BOX_FORMAT"]


def apply_mask(img, mask, norm_mask=False, int_out=False):
    '''Apply a mask to an image.

    Args:
        img (array):              Input image
        mask (array):             Input binary mask image
        norm_mask (bool):         Whether to normalize the mask to [0,1]. Default is False.
        int_out (bool):           Whether to return the output image as an integer array. Default is False.

    Returns:
        array:                    Masked output image.
    '''
    mask = check_image_format(mask, allow_float=True)
    if norm_mask:
        mask = mask / 255.0
    out = np.float32(img) * mask
    if int_out:
        out = np.uint8(np.clip(out, 0, 255))
    return out

def apply_mask_merge(img_a, img_b, mask, norm_mask=False, int_out=True):
    """Merge img_a to img_b according to mask.
    """
    img_a = check_image_format(img_a, allow_float=True)
    img_b = check_image_format(img_b, allow_float=True)
    mask = check_image_format(mask, allow_float=True)
    mask = mask / 255.0 if norm_mask else mask
    merge_mask = apply_mask(img_a, mask) + apply_mask(img_b, 1.0-mask)
    if int_out:
        return np.uint8(np.clip(merge_mask, 0, 255))
    return merge_mask

def cal_residual_image(img_a, img_b, scale=1.0, bias=127, clip=True):
    '''
    Calculate the residual image between two images and apply optional scaling and bias.

    Args:
        img_a(array):        [H, W, C], input image A
        img_b(array):        [H, W, C], input image B
        scale(float):        scale factor applied on the difference
        bias(float):         added to the scaled difference
        clip(bool):          if True, clip the result to the range [0, 255]

    Returns:
        res(array):          [H, W, C], residual image
    '''
    res = (np.float32(img_a) - img_b) * scale + bias
    res = np.uint8(np.clip(res, 0, 255)) if clip else res
    return res

def cal_residual_diff(img_a, img_b, method='', fg_mask=None, morpho='', morpho_size=None):
    '''Calculate residual standard deviation value of two image.

    Args:
        method(array):        'color': calculate standard diviation map 
                                         if img_a and img_b is mainly 
                                         different in color channel

    Outs:
        diff_v(float)
    '''
    res = cal_residual_image(img_a, img_b, bias=0, clip=False)
    if fg_mask is not None:
        fg_mask = check_image_format(fg_mask, allow_float=True)
        res = res * fg_mask
    diff_map = np.std(res, axis=2) if 'color' in method else res
    if 'open' in morpho:
        diff_map = cv2.morphologyEx(diff_map, cv2.MORPH_OPEN, np.ones(morpho_size))
    if fg_mask is not None:
        diff_v = np.sum(diff_map) / np.sum(fg_mask)
    else:
        diff_v = np.mean(diff_map)
    return diff_v


def cvt_color(img, format=cv2.COLOR_BGR2RGB):
    return cv2.cvtColor(img, format)

def cvt_box_format(box, format='ltrb2cxywh'):
    from_format, to_format = format.split('2')
    assert from_format in SUPPORTED_BOX_FORMAT and to_format in SUPPORTED_BOX_FORMAT

    # Convert to ltwh first
    in_box = np.array(box).reshape((-1,2))
    ltwh_box = np.zeros((2,2))
    if from_format == 'ltrb':
        ltwh_box[0] = in_box[0]
        ltwh_box[1] = in_box[1] - in_box[0]
    elif from_format == 'cxywh':
        ltwh_box[0] = in_box[0] - in_box[1] // 2
        ltwh_box[1] = in_box[1]
    elif from_format == 'cw':
        ltwh_box[0] = in_box[0]
        ltwh_box[1] = in_box[2]

    # Convert to dst format
    if to_format == 'ltrb':
        out_box = np.zeros((2,2))
        out_box[0] = ltwh_box[0]
        out_box[1] = ltwh_box[0] + ltwh_box[1]
    elif to_format == 'ltwh':
        out_box = ltwh_box
    elif to_format == 'cxywh':
        out_box = np.zeros((2,2))
        out_box[0] = ltwh_box[0] + ltwh_box[1] // 2
        out_box[1] = ltwh_box[1]
    elif to_format == 'cw':
        out_box = np.array([(ltwh_box[0,0], ltwh_box[0,1]),
                            (ltwh_box[0,0]+ltwh_box[1,0], ltwh_box[0,1]),
                            (ltwh_box[0,0]+ltwh_box[1,0], ltwh_box[0,1]+ltwh_box[1,1]),
                            (ltwh_box[0,0], ltwh_box[0,1]+ltwh_box[1,1])])

    return out_box.reshape(-1)

def cal_bounding_rect(points):
    '''
    Calculate bounding rectangle for given points.

    Args:
        points(array):      [N, 2], np.array([[x1, y1], [x2, y2], ...])

    Returns:
        bbox(array):        [4, ], [xmin, ymin, xmax, ymax]
    '''
    lt = points.min(axis=0)
    rb = points.max(axis=0)
    return np.concatenate([lt, rb])

def pad_rect(rect, padding_scale=None, padding_fix=None, box_wh_fix=None):
    '''
    Padding rectangle.

    Args:
        rect(array/list):       [4, ] or [2, 2], rectangle in [xmin, ymin, xmax, ymax]
        padding_scale(float):   scale factor for padding, e.g. 0.2
        padding_fix(array):     [4, ], [left, top, right, bottom], padding fix size
        box_wh_fix(array):      [2, ], [width, height], fix output box size

    Returns:
        box(array):             [4, ], [xmin, ymin, xmax, ymax] padding rect
    '''
    cbox = cvt_box_format(rect, format='ltrb2cxywh')
    if box_wh_fix is not None:
        cbox[2] = box_wh_fix[0]
        cbox[3] = box_wh_fix[1]
    if padding_scale is not None:
        cbox[2] = cbox[2] * padding_scale
        cbox[3] = cbox[3] * padding_scale
    box = cvt_box_format(cbox, format='cxywh2ltrb')
    if padding_fix is not None:
        padding_fix = np.array([-padding_fix[0], -padding_fix[1], padding_fix[2], padding_fix[3]])
        box += np.array(padding_fix)
    return box

def crop_rect(img, rect, border_mode=cv2.BORDER_CONSTANT, value=0):
    '''Crop a rectangle area from image, this allow the area partly outside the image.

    Args:
        img(array):           opencv image
        rect(tuple/array):    tuple of (left, top, right, bottom)

    Outs:
        face_img(array)
        pad_l, pad_t(tuple):  bias of axis origin
    '''
    if isinstance(rect, np.ndarray):
        rect_int = np.int64(rect.flatten())
    else:
        rect_int = list(map(int, rect))
    face_lt = rect_int[:2]
    face_rb = rect_int[2:4]
    pad_l = -face_lt[0] if face_lt[0] < 0 else 0
    pad_t = -face_lt[1] if face_lt[1] < 0 else 0
    pad_r = face_rb[0]-img.shape[1] if face_rb[0] > img.shape[1] else 0
    pad_b = face_rb[1]-img.shape[0] if face_rb[1] > img.shape[0] else 0
    pad_img = cv2.copyMakeBorder(img, pad_t, pad_b, pad_l, pad_r, border_mode, value=value)
    face_img = pad_img[face_lt[1]+pad_t:face_rb[1]+pad_t+pad_b, face_lt[0]+pad_l:face_rb[0]+pad_l+pad_r]
    return face_img, (pad_l, pad_t)

def crop_roi_points_image(image, roi_points, padding_scale=None, padding_fix=None, box_wh_fix=None):
    '''
    Crop ROI from original image with points and padding.

    Args:
        image(array):           [H, W, C], opencv image
        roi_points(array):      [N, 2] or [N, 1, 2], np.array([[x1, y1], [x2, y2], ...])
        padding_scale(float):   scale factor for padding, e.g. 0.2
        padding_fix(array):     [4, ], [left, top, right, bottom], padding fix size
        box_wh_fix(array):      [2, ], [width, height], fix output box size

    Returns:
        roi_image(array):       [H', W', C], ROI image with padding
        box(array):             [4, ], [xmin, ymin, xmax, ymax] of the ROI without padding
    '''
    if len(roi_points.shape) == 3:
        roi_points = roi_points[:,0,:]

    box = cal_bounding_rect(roi_points)
    box = pad_rect(box, padding_scale=padding_scale, padding_fix=padding_fix, box_wh_fix=box_wh_fix)
    roi_image, __ = crop_rect(image, box)
    return roi_image, box

def crop_center(img, size, border_mode=cv2.BORDER_CONSTANT, value=0):
    '''Crop the center area of image with (height, width) output

    Args:
        img(array):         opencv image
        size(tuple):        (height, width) after center crop

    Outs:
        face_img(array)
    '''
    c_h = img.shape[0] // 2
    c_w = img.shape[1] // 2
    rect_l = c_w - size[1] // 2
    rect_t = c_h - size[0] // 2
    rect = [rect_l, rect_t, rect_l+size[1], rect_t+size[0]]
    out_img, _ = crop_rect(img, rect, border_mode=border_mode, value=value)
    return out_img

def pad_center(img, size, border_mode=cv2.BORDER_CONSTANT, value=0):
    '''Padding around the image to (height, width).

    Args:
        img(array):     opencv image
        size(tuple):    (height, width) after padding

    Outs:
        padded_img(array)
        pad_l, pad_t(tuple): bias of axis origin
    '''
    height, width = size[0], size[1]
    if height > img.shape[0]:
        pad_t = int((height-img.shape[0]) // 2)
        pad_b = height-img.shape[0]-pad_t
    else:
        pad_t = 0
        pad_b = 0
    if width > img.shape[1]:
        pad_l = int((width-img.shape[1]) // 2)
        pad_r = width-img.shape[1]-pad_l
    else:
        pad_l = 0
        pad_r = 0
    padded_img = cv2.copyMakeBorder(img, pad_t, pad_b, pad_l, pad_r, border_mode, value=value)
    return padded_img, (pad_l, pad_t)

def fill_roi_image(src_image, roi_images, boxes):
    from .maskutils import apply_feather
    mask_img = np.zeros_like(src_image, dtype=np.float32)
    mask_cnt = np.zeros_like(src_image, dtype=np.float32)
    for rimg, box in zip(roi_images, boxes):
        l, t, r, b = box
        mask_img[t:b, l:r] += rimg
        mask_cnt[t:b, l:r] += 1.
    src_mask = np.float32(mask_cnt == 0)
    mask_cnt[mask_cnt==0] = 1.
    mask_img = mask_img / mask_cnt
    res_img = apply_mask_merge(src_image, mask_img, src_mask)
    # eliminate edges
    src_mask = apply_feather(src_mask, dsize=3, sigma=2, ksize=5)
    res_img = apply_mask_merge(src_image, res_img, src_mask)
    return np.uint8(res_img)


def color_calibration(roi_img, roi_ref):
    '''Get color calibration matrix from roi_img to roi_ref.

    Args:
        roi_img(array):            OpenCV image ROI
        roi_ref(array):            OpenCV image ROI

    Outs:
        trans_mat(array):          matrix transfer color from roi_img to roi_ref

    Usage: 
        clib_img = np.uint8(np.clip(np.matmul(np.insert(img.reshape(-1,3), [3], 1, axis=-1), trans_mat).reshape(img.shape), 0, 255))
    '''
    poi_img_mat = np.float64(np.insert(roi_img.reshape(-1,3), [3], 1, axis=-1))
    poi_ref_mat = np.float64(roi_ref.reshape(-1,3))
    trans_mat = np.matmul(np.matmul(np.linalg.pinv(np.matmul(poi_img_mat.transpose(), poi_img_mat)), poi_img_mat.transpose()), poi_ref_mat)
    return trans_mat

def color_calibration_v2(roi_img, roi_ref, print_inlier_ratio=True):
    '''Get color calibration regressor from roi_img to roi_ref.

    Args:
        roi_img(array):            OpenCV image ROI
        roi_ref(array):            OpenCV image ROI

    Outs:
        regressor(model):          sklearn ransac regressor model 
        pipeline(pipe):            preprocessing pipeline

    Usage: 
        pred = ransac.predict(pipe.fit_transform(img.reshape(-1, 3)))
        pred_rec = np.clip(pred * (pipe['scaler'].scale_[1:4]) + pipe['scaler'].mean_[1:4], 0, 255).reshape(img.shape)
    '''
    pipe = Pipeline([('poly', PolynomialFeatures()), ('scaler', StandardScaler())])
    x = roi_img.reshape(-1, 3)
    y = roi_ref.reshape(-1, 3)
    norm_x = pipe.fit_transform(x)
    norm_y = (y - pipe['scaler'].mean_[1:4]) / (pipe['scaler'].scale_[1:4])
    ransac = linear_model.RANSACRegressor(estimator=linear_model.Ridge(alpha=0.001), min_samples=norm_x.shape[1]+1)
    ransac.fit(norm_x, norm_y)
    if print_inlier_ratio:
        ratio = np.count_nonzero(ransac.inlier_mask_) / ransac.inlier_mask_.size
        print(f"calibration inlier ratio:{ratio:.3f}")
    return ransac, pipe

def apply_calibration(img, trans_mat):
    return np.uint8(np.clip(np.matmul(np.insert(img.reshape(-1,3), [3], 1, axis=-1), trans_mat).reshape(img.shape), 0, 255))


def cal_color_hist(img):
    bgr_hist = []
    for i,color in enumerate(['b','g','r']):
        hist = cv2.calcHist([img],[i],None,[256],[0,256])
        bgr_hist += [hist]
    bgr_hist = np.concatenate(bgr_hist, axis=-1)
    return bgr_hist


def get_colormap_array(n, name='gist_rainbow', int_out=True):
    '''Get colormap numpy array in n points. Returns in RGB [0,1].
    
    Args:
        n(int):         color gradations number
        name(str):      matplotlib colormaps name
        
    Outs:
        np.ndarray:     [n, 4] in RGB, values in [0.0, 1.0]
    '''
    colormap = plt.get_cmap(name)
    gradations = np.linspace(0, 1, n)
    colormap_array = colormap(gradations)
    if int_out:
        colormap_array = np.uint8(colormap_array * 255)
    return colormap_array


def get_rounded_rect(size, padv, radius):
    '''Get an rounded rectangle drawing by 1 x rect + 4 x round.

    Notice:
        1. get a round: padv = radius = size[0]//2 = size[1]//2
        2. might be replaced by cv2.getStructuringElement in general cases

    Args:
        size(list/tuple):           
        padv(int):            
        radius(int):

    Outs:
        img(array)
    '''
    img = np.zeros(size, dtype=np.uint8)
    img[padv:-padv,padv:-padv] = 255
    cv2.circle(img, (padv,padv), radius, 255, -1)
    cv2.circle(img, (padv,img.shape[0]-padv-1), radius, 255, -1)
    cv2.circle(img, (img.shape[1]-padv-1,padv), radius, 255, -1)
    cv2.circle(img, (img.shape[1]-padv-1,img.shape[0]-padv-1), radius, 255, -1)
    img[padv:-padv,padv-radius:img.shape[1]-padv+radius] = 255
    img[padv-radius:img.shape[0]-padv+radius, padv:-padv] = 255
    return img


def resize_like(src_img, dst_img, interp=cv2.INTER_LINEAR):
    resize_img = cv2.resize(src_img, (dst_img.shape[1], dst_img.shape[0]), interpolation=interp)
    return resize_img


def resize_scale(src_img, scale=1.0, align_length=0, align_flag='height', interp=cv2.INTER_LINEAR):
    """Scale resize input image.

    Args:
        src_img:        Input image, cv2 numpy array, in [H, W, C] or [H, W] format
        scale:          Scale ratio, default 1.0
        align_length:   Align length, auto infer scale param, default 0
        align_flag:     'height' or 'width' to align, default 'height'
        interp:         interpolation method, default bilinear
    
    Outs:
        Resized image
    """
    if scale == 1.0 and align_length == 0:
        return src_img
    elif align_length > 0:
        if align_flag == 'height':
            resize_img = cv2.resize(src_img, (int(src_img.shape[1] * align_length / src_img.shape[0]), align_length),
                                    interpolation=interp)
        elif align_flag == 'width':
            resize_img = cv2.resize(src_img, (align_length, int(src_img.shape[0] * align_length / src_img.shape[1])),
                                    interpolation=interp)
        else:
            print('resize_scale(): unkown align_flag %s' % align_flag)
            return
    elif scale != 1.0:
        resize_img = cv2.resize(src_img, (int(src_img.shape[1] * scale), int(src_img.shape[0] * scale)), interpolation=interp)
    else:
        print('resize_scale(): error input align_length or scale')
        return src_img

    return resize_img

def resize_alignrect(src_img, align_rect, bounding=False):
    """Scale a resize image to a rectangle area.

    Args:
        src_img:        Input image, cv2 numpy array, in [H, W, C] or [H, W] format
        align_rect:     Rectangle in [height, width]
        bounding:       Specify whether the align_rect bounding src_img or inscribed in it 
    
    Outs:
        Resized image
    """
    src_h = src_img.shape[0]
    src_w = src_img.shape[1]
    dst_h = align_rect[0]
    dst_w = align_rect[1]
    src_ratio = np.float32(src_h)/np.float32(src_w)
    dst_ratio = np.float32(dst_h)/np.float32(dst_w)

    if src_h >= dst_h and src_w >= dst_w:
        interp = cv2.INTER_AREA
    elif src_h < dst_h and src_w < dst_w:
        interp = cv2.INTER_CUBIC
    else:
        interp = cv2.INTER_LINEAR

    if src_ratio > dst_ratio:
        align_length = dst_h if bounding else dst_w
        align_flag = 'height' if bounding else 'width'
    else:
        align_length = dst_w if bounding else dst_h
        align_flag = 'width' if bounding else 'height'

    src_img = resize_scale(src_img, align_length=align_length, align_flag=align_flag, interp=interp)
    return src_img

def resize_fix(src_img, dst_h=0, dst_w=0, flag='pad', pad_method=cv2.BORDER_CONSTANT, pad_value=0, position='center'):
    """Fix source image size to a fixed size.

    Args:
        src_img:        Input image, cv2 numpy array, in [H, W, C] or [H, W] format
        dst_h:          Fixed height
        dst_w:          Fixed width
        flag:           Resize flag: ['fix', 'pad', 'crop'], default 'pad'
                                    fix:   Resize to (dst_h, dst_w), keep ratio when dst_h or dst_w is set to 0
                                    pad:   Resize according image's long size and pad 0 to fix short size
                                    crop:  Resize according image's short size and crop to fix long size
        pad_method:     Padding mode of opencv
        pad_value:      In 'pad' flag, padding with pad_value
        position:       Position of output image content: ['center', 'topleft']
    Outs:
        Fixed-size image
    """
    assert(len(src_img.shape) == 3 or len(src_img.shape) == 2)
    assert(dst_h > 0 or dst_w > 0)

    src_h = src_img.shape[0]
    src_w = src_img.shape[1]
    src_ratio = np.float32(src_h)/np.float32(src_w)
    dst_ratio = np.float32(dst_h)/np.float32(dst_w)

    if src_h >= dst_h and src_w >= dst_w:
        interp = cv2.INTER_AREA
    elif src_h < dst_h and src_w < dst_w:
        interp = cv2.INTER_CUBIC
    else:
        interp = cv2.INTER_LINEAR

    if flag == 'fix':
        if dst_w == 0:
            resize_img = resize_scale(src_img, align_length=dst_h, align_flag='height', interp=interp)
        elif dst_h == 0:
            resize_img = resize_scale(src_img, align_length=dst_w, align_flag='width', interp=interp)
        else:
            resize_img = cv2.resize(src_img, (int(dst_w), int(dst_h)), interpolation=interp)
        return resize_img

    if src_ratio > dst_ratio:
        if flag == 'crop':
            align_flag = 1
            resize_img = resize_scale(src_img, align_length=dst_w, align_flag='width', interp=interp)
            if position == 'center':
                crop_start = int((resize_img.shape[0] - dst_h) / 2)
                fixed_img = resize_img[crop_start:crop_start + dst_h, ...]
            elif position == 'topleft':
                fixed_img = resize_img[:dst_h, ...]
            else:
                raise NotImplementedError('position "%s" not avaliable' % position)
        elif flag == 'pad':
            align_flag = 0
            resize_img = resize_scale(src_img, align_length=dst_h, align_flag='height', interp=interp)
            if position == 'center':
                fixed_img, _ = pad_center(resize_img, (dst_h, dst_w), border_mode=pad_method, value=pad_value)
            elif position == 'topleft':
                fixed_img = cv2.copyMakeBorder(resize_img, 0, 0, 0, dst_w-resize_img.shape[1], pad_method, value=pad_value)
            else:
                raise NotImplementedError('position "%s" not avaliable' % position)
        else:
            print("fix_to_image_size(): error input flag.")
            return
    else:
        if flag == 'crop':
            align_flag = 0
            resize_img = resize_scale(src_img, align_length=dst_h, align_flag='height', interp=interp)
            if position == 'center':
                crop_start = int((resize_img.shape[1] - dst_w) / 2)
                fixed_img = resize_img[:, crop_start:crop_start + dst_w, ...]
            elif position == 'topleft':
                fixed_img = resize_img[:, :dst_w, ...]
            else:
                raise NotImplementedError('position "%s" not avaliable' % position)
        elif flag == 'pad':
            align_flag = 1
            resize_img = resize_scale(src_img, align_length=dst_w, align_flag='width', interp=interp)
            if position == 'center':
                fixed_img, _ = pad_center(resize_img, (dst_h, dst_w), border_mode=pad_method, value=pad_value)
            elif position == 'topleft':
                fixed_img = cv2.copyMakeBorder(resize_img, 0, dst_h-resize_img.shape[0], 0, 0, pad_method, value=pad_value)
            else:
                raise NotImplementedError('position "%s" not avaliable' % position)
        else:
            print("fix_to_image_size(): error input flag.")
            return

    return fixed_img

def gaussian_kernel(sigma, ksize=None):
    ksize = max(1, int(6*sigma + 1)) | 1 if ksize is None else ksize
    if isinstance(ksize, int):
        ksize_y = ksize
        ksize_x = ksize
    else:
        ksize_y = ksize[1]
        ksize_x = ksize[0]
    weight = np.matmul(cv2.getGaussianKernel(ksize_y, sigma), 
                       cv2.getGaussianKernel(ksize_x, sigma).T)
    return weight

def generate_log_filter(sigma, size=None, norm=True):
    """Generate a Laplacian of Gaussian (LoG) kernel.

    Args:
        sigma (float):               Standard deviation of the Gaussian distribution.
        kernel_size (int, optional): Size of the kernel. If None, it will be set to `6 * sigma + 1`.

    Returns:
        numpy.ndarray:               The LoG kernel.
    """
    if size is None:
        size = int(6 * sigma + 1)
    else:
        assert size % 2 == 1, "Kernel size must be odd."

    radius = size // 2
    y, x = np.ogrid[-radius: radius+1, -radius: radius+1]

    # Create Gaussian Filter
    gaussian_filter = 1/(2*np.pi*sigma**2) * np.exp(-(x**2+y**2)/(2*sigma**2))

    # Create Laplacian Filter
    laplacian_filter = (x**2 + y**2 - 2*sigma**2) / sigma**4

    # Combine Gaussian and Laplacian Filter to form LoG Filter
    log_filter = laplacian_filter * gaussian_filter

    # Implement 2
    # ax = np.arange(-size // 2 + 1., size // 2 + 1.)
    # xx, yy = np.meshgrid(ax, ax)
    # log_filter = -1 / (np.pi * sigma**4) * (1 - (xx**2 + yy**2) / (2 * sigma**2)) * np.exp(-(xx**2 + yy**2) / (2 * sigma**2))

    if norm:
        log_filter = log_filter - log_filter.mean()

    return log_filter

def masked_gaussian_blur(img, mask, ksize, sigma, erode_size=5, blur_size=3):
    if isinstance(sigma, (tuple, list)):
        sigmaX = sigma[0]
        sigmaY = sigma[1]
    else:
        sigmaX = sigma
        sigmaY = sigma

    src_array = np.concatenate([img * mask, mask], axis=-1)
    blur_array = cv2.GaussianBlur(src_array, ksize, sigmaX=sigmaX, sigmaY=sigmaY)
    blurry_img = blur_array[...,:-1]
    blurry_mask = blur_array[...,-1:]
    recov_img = blurry_img / ((blurry_mask - mask) + 1)
    merge_mask = cv2.erode(mask, np.ones((erode_size,erode_size)))
    merge_mask = cv2.blur(merge_mask, (blur_size, blur_size))
    merge_img = apply_mask_merge(recov_img, img, merge_mask, int_out=False)
    return merge_img

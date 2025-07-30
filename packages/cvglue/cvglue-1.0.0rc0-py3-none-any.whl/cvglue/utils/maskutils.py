import cv2
import numpy as np
from .fileutils import check_image_format
from .imageutils import get_rounded_rect, pad_center, crop_rect

__all__ = ["DoG", "XDoG", "apply_feather", "cal_residual_mask", 
           "calculate_similarity_to_shape", "crop_contours", 
           "detect_white_edge_padding", "edge_soft_mask", "generate_contours_mask", 
           "render_mask", "select_mask_area", "select_mask_regoin", "soft_threshold"]


def cal_residual_mask(img_a, img_b, method='l1sum', threshold=50, morpho='', morpho_size=None):
    '''Calculate residual mask of (img_a - img_b).

    Args:
        img(array):                opencv image
        method(string):            residual method: 
                                     - 'l1sum': set 1 once L1 sum of res over each 
                                                channel is large than threshold
        threshold(int):            tuple of (left, top, right, bottom)
        morpho(bool):              make morphology manipulate to reduce mask noise
        morpho_size(tuple):        morphology kernel size

    Outs:
        res(array):                output mask in [0, 255]
    '''
    res_img = np.float32(img_a) - img_b
    if method == 'l1sum':
        res = np.sum(np.abs(res_img), axis=2) > threshold
    elif method == 'inner':
        res = np.sqrt(np.sum(res_img**2, axis=2)) > threshold
    elif method == 'light':
        res = np.sum(res_img, axis=2) > threshold
    elif method == 'lightspot':
        res_img = np.clip(res_img, 0, 255)
        kernel_d = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(11,11))   # spot max size
        res_img_d = res_img - cv2.morphologyEx(res_img, cv2.MORPH_OPEN, kernel_d)
        res = np.max(res_img_d > threshold, axis=-1)
    res = np.uint8(res*255)
    if 'open' in morpho:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,morpho_size)
        res = cv2.morphologyEx(res, cv2.MORPH_OPEN, kernel)
    if 'close' in morpho:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,morpho_size)
        res = cv2.morphologyEx(res, cv2.MORPH_CLOSE, kernel)
    return res

def apply_feather(mask, blur=True, dilate=True, **kwargs):
    '''Apply feathering to a mask.

    Args:
        mask (array):             Input binary mask image
        blur (bool):              Whether to blur the mask using a Gaussian filter. Default is True.
        dilate (bool):            Whether to dilate the mask. Default is True.
        **kwargs:                 Additional keyword arguments that will be passed to the functions called internally.
            dsize (int):          Size of the dilation kernel. Default is 9.
            ksize (int):          Size of the Gaussian kernel. Default is 13.
            sigma (int):          Sigma value of the Gaussian filter. Default is 5.

    Returns:
        array:                    Feathered binary mask image.
    '''
    dsize = kwargs.get('dsize', 9)
    ksize = kwargs.get('ksize', 13)
    sigma = kwargs.get('sigma', 5)
    if dilate:
        kernel = get_rounded_rect((dsize,dsize), dsize//2, dsize//2)
        mask = cv2.dilate(mask, kernel)
    if blur:
        # choose with cv2.getGaussianKernel(ksize, sigma)
        mask = cv2.GaussianBlur(mask, (ksize, ksize), sigmaX=sigma, sigmaY=sigma)
    return mask

def generate_contours_mask(src_height, src_width, contours, blur=True, dilate=True, **kwargs):
    '''
        Notice:
            - output mask: shape [src_height, src_width] in [0.0, 1.0] value

        Example: 
            mask = generate_contours_mask(1024, 576, [lands])   # lands: [n, 2]
    '''
    padv = kwargs.get('padv', 0)
    fg_mask = np.ones((src_height,src_width,1), dtype=np.float32) * padv
    fg_mask = cv2.fillPoly(fg_mask, contours, (1.0))
    fg_mask = apply_feather(fg_mask, blur=blur, dilate=dilate, **kwargs)
    fg_mask = np.clip(fg_mask, 0.0, 1.0)
    return fg_mask.squeeze()

def crop_contours(image, contours):
    crop_img_list = []
    crop_box_list = []
    for contour in contours[0]:
        box = cv2.boundingRect(contour)
        box = np.reshape(box, (2,2))
        box[1] += box[0]
        crop_img, _ = crop_rect(image, box, border_mode=cv2.BORDER_REFLECT_101)
        crop_img_list.append(crop_img)
        crop_box_list.append(box)
    return crop_img_list, crop_box_list

def render_mask(img, mask, alpha=0.3, thres=0.5, color=[255,144,30], norm_mask=True, matting=False):
    '''Render a mask on an image using alpha blending.

    Args:
        img (array):         The input image as a numpy array.
        mask (array):        The mask to be rendered as a numpy array.
        alpha (float):       The alpha value to use for blending. Default 0.3.
        thres (float):       The thres of the mask to overlay. Default 0.5.
        color (list):        Color list to render mask in.
        norm_mask (bool):    Whether to normalize the input mask. Default True.
        matting(bool):       Rendering matting mask. Default False.

    Returns:
        The output image as a numpy array of unsigned integers.

    Usage:
        # Render a binary mask on an RGB image:
        img = cv2.imread("image.jpg")
        mask = cv2.imread("mask.png")
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        output = render_mask(img, mask, alpha=0.5)
    '''
    img = check_image_format(img, allow_float=True).astype(np.float32)
    mask = check_image_format(mask, allow_float=True).astype(np.float32)
    src_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.shape[-1] == 1 else img    
    mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)[:,:,None] if mask.shape[-1] == 3 else mask
    if matting:
        mask = mask / np.max(mask)
        cover_mask = mask * alpha
    else:
        mask = mask / np.max(mask) if norm_mask else mask
        cover_mask = (mask > thres) * alpha if alpha > 0. else mask
    cover_mask = cover_mask.astype(np.float32)
    cover_img = cover_mask * np.array(color, dtype=np.float32).reshape(1, 1, -1)
    disp_img = cv2.blendLinear(src_img, cover_img, 1.0-cover_mask, cover_mask)
    disp_img = disp_img.astype(np.uint8)
    return disp_img

def select_mask_area(mask, select_area=None, largest=False, method='pixel'):
    """Select submask according to mask contours area

    Notice:
        1. this function is inplace.

    Args:
        method(str):        'pixel' or 'rect', calculate contours area according to pixel or bounding rect
        select_area(tuple): (minimal, maximal) area of target mask
    """
    contours = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    if method == 'pixel':
        cons_area = [cv2.contourArea(contour) for contour in contours[0]]
    elif method == 'rect':
        times_func = lambda x : x[2] * x[3]
        cons_area = [times_func(cv2.boundingRect(contour)) for contour in contours[0]]
    if select_area:
        _ = [cv2.fillPoly(mask, [contours[0][i]], (0)) for i in range(len(cons_area)) if cons_area[i] < select_area[0] or cons_area[i] > select_area[1]]
    elif largest:
        _ = [cv2.fillPoly(mask, [contours[0][i]], (0)) for i in range(len(cons_area)) if cons_area[i] < max(cons_area)]
    return mask

def select_mask_regoin(mask, limit_box, threshold=0.10):
    """Select submask according to IOU with limit_box

    Notice:
        1. this function is inplace.
    """
    def cal_rect_area(rect):
        rect = np.reshape(rect, (-1))
        width = rect[3] - rect[1]
        height = rect[2] - rect[0]
        if width > 0 and height > 0:
            return width * height
        else:
            return -1

    contours = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    for contour in contours[0]:
        box = cv2.boundingRect(contour)
        box = np.reshape(box, (2,2))
        box[1] += box[0]

        inter_left = limit_box[0] if limit_box[0] > box[0,0] else box[0,0]
        inter_top = limit_box[1] if limit_box[1] > box[0,1] else box[0,1]
        inter_right = limit_box[2] if limit_box[2] < box[1,0] else box[1,0]
        inter_bottom = limit_box[3] if limit_box[3] < box[1,1] else box[1,1]
        inter_area = cal_rect_area([inter_left, inter_top, inter_right, inter_bottom])
        iou = inter_area / cal_rect_area(box)
        if iou < threshold:
            _ = cv2.fillPoly(mask, [contour], (0))
    return mask


def calculate_similarity_to_shape(contour, size, shape='ellipse'):
    '''
    Calculate Jaccard similarity index between a shape fitted to a contour and the contour itself.

    Args:
        contour(array):     [N, 1, 2], np.array([[[x1, y1]], [[x2, y2]], ...])
        size(tuple):        size of the image, (height, width)

    Returns:
        jaccard_similarity(float):  Jaccard similarity index between the shape and the contour
        fit_shape(tuple):           tuple containing the parameters of the fitted shape 
                                        ellipse/rrect: ((center_x, center_y), (major_axis, minor_axis), angle)
        fill_rate(float):           Intersection between shape and contour over contour area
    '''
    if shape == 'ellipse':
        # ((center_x, center_y), (major_axis, minor_axis), angle)
        fit_shape = cv2.fitEllipse(contour)
        mask_1 = np.zeros(size)
        cv2.ellipse(mask_1, fit_shape, 1, -1)
    elif shape == 'rrect':
        fit_shape = cv2.minAreaRect(contour)
        mask_1 = np.zeros(size)
        box = cv2.boxPoints(fit_shape)
        box = np.intp(box)
        cv2.drawContours(mask_1, [box], -1, 1, -1)
    else:
        raise NotImplementedError(f"{shape} not implemented")

    # Draw the contour on the mask
    mask_2 = np.zeros(size)
    cv2.drawContours(mask_2, [contour], -1, 1, -1)

    # Calculate the Jaccard similarity index between the shape and the contour
    intersection = np.sum(np.logical_and(mask_1, mask_2))
    union = np.sum(np.logical_or(mask_1, mask_2))
    
    jaccard_similarity = intersection / union
    fill_rate = intersection / np.sum(mask_2)

    return jaccard_similarity, fit_shape, fill_rate


def detect_white_edge_padding(img, feather=False, **kwargs):
    '''
    Detect white edge padding area in the image.

    Args:
        img(array):         [H, W, C], opencv image
        feather(bool):      whether use feather to apply mask or not
        **kwargs(optional): additional parameters for feather function

    Returns:
        out_mask(array):    [H, W], binary float mask of detected padding area
    '''
    thres_mask = (np.sum(img, axis=-1) > 245*3)*1
    pad_mask, (pl, pt) = pad_center(thres_mask, (thres_mask.shape[0]*2, thres_mask.shape[1]*2), value=1)
    pad_mask = pad_mask.astype(np.uint8)
    kernel_d = cv2.getStructuringElement(cv2.MORPH_RECT,(5, 5))
    pad_mask_d = cv2.morphologyEx(pad_mask, cv2.MORPH_CLOSE, kernel_d)
    pad_mask_d = select_mask_area(pad_mask_d, largest=True)
    out_mask = apply_feather(pad_mask_d, **kwargs) if feather else pad_mask_d
    return out_mask[pt:-pt, pl:-pl]


def DoG(img, sigma, k, tau=1.0, ks=(0,0)):
    '''
    Perform Difference of Gaussian (DoG) operation on an image.

    Args:
        img(array):         2D grayscale image (or 3D color image) to be processed.
        sigma(float):       Standard deviation for the Gaussian kernel.
        k(float):           Scale multiplier for creating two Gaussian kernels.
        tau(float):         Weight for the difference operation.

    Returns:
        Gsigma(array):      Resulting image after DoG operation.
    '''
    ksigma = k*sigma

    ## Implementation 1
    # Gsigma = cv2.GaussianBlur(img, ks, sigmaX=sigma, sigmaY=sigma)
    # Gksigma = cv2.GaussianBlur(img, ks, sigmaX=ksigma, sigmaY=ksigma)
    # dog_img = Gsigma - tau * Gksigma

    ## Implementation 2
    kern = gaussian_kernel(sigma, ks) - gaussian_kernel(ksigma, ks)
    dog_img = cv2.filter2D(np.float32(img), -1, kern)
    return dog_img

def soft_threshold(img, mask, thres=0.0, alpha=1.0, norm_mask=False):
    '''
    Perform soft thresholding operation on an image. 

    Args:
        img(array):         2D grayscale image (or 3D color image) to be processed.
        mask(array):        Binary mask, same shape as input image.
        thres(float):       Threshold value for mask processing.
        alpha(float):       Scaling factor for transforming mask.
        norm_mask(bool):    Whether to normalize the mask or not.

    Returns:
        soft_thres(array):  Resultant image after soft thresholding.
    '''
    if norm_mask:
        mask = mask / mask.max()
    soft_mask = img * mask
    soft_thres = 1 + np.tanh(alpha * (soft_mask - thres))
    soft_thres[soft_mask > thres] = 1.0
    return soft_thres

def XDoG(img, sigma, k, tau=1.0, alpha=1.0, beta=0.0, white_edge=False):
    '''
    Perform eXtended Difference of Gaussian (XDoG) operation on an image.

    Args:
        img(array):         2D grayscale image (or 3D color image) to be processed.
        sigma(float):       Standard deviation for the Gaussian kernel.
        k(float):           Scale multiplier for creating two Gaussian kernels.
        tau(float):         Weight for the DoG operation.
        alpha(float):       Scaling factor for soft thresholding.
        beta(float):        Threshold for the soft thresholding operation.

    Returns:
        edge_img(array):    Resulting image after XDoG operation.
    '''
    dog = DoG(img, sigma, k, tau=tau)
    edge_img = soft_threshold(img, dog, thres=beta, alpha=alpha, norm_mask=True)
    if white_edge:
        edge_img = 1.0 - edge_img
    return edge_img

def edge_soft_mask(img, sigma=1.0, k=5.0, tau=1.0, scaling_factor=2.8):
    dog = np.abs(DoG(img, sigma, k, tau=1.0))
    if len(dog.shape) == 3 and dog.shape[2] != 1:
        dog = np.mean(dog, axis=2)
    soft_mask = dog / dog.max()
    # soft_mask = cv2.morphologyEx(soft_mask, cv2.MORPH_CLOSE, np.ones((3,3)))
    soft_mask = np.clip(soft_mask * scaling_factor, 0.0, 1.0)
    return soft_mask

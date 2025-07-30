import copy
import cv2
import numpy as np
import scipy.ndimage
import PIL.Image
import itertools
import skimage
from skimage import transform as trans
from scipy.spatial import Delaunay
from .imageutils import cvt_box_format, get_rounded_rect, pad_rect, crop_rect, cal_bounding_rect, apply_mask_merge
from .maskutils import generate_contours_mask
from .logger import setup_logger
try:
    from ..thirdparty.InsightFace.face_align import norm_crop
except Exception as e:
    print(repr(e))

llog = setup_logger(name=__name__)

__all__ = ["align_face", "cal_eye_dist", "cal_face_area", "crop_face_v2", "crop_face_v3", 
           "crop_face_v4", "draw_headpose", "generate_face_mask", "generate_under_cheek_mask", 
           "get_face_parser", "get_hairline_point_cropv3", "get_landmarks_boundaries", 
           "render_face", "warp_back", "warp_face_Delaunay", "warp_face_Delaunay_flow", 
           "warp_face_box", "warp_face_landsmarks", "warp_landmarks", "warp_with_landmarks"]


def get_face_parser():
    from ..parser import face_parser, landmarks_parser
    class merge_parser(landmarks_parser, face_parser):
        __version__ = 'lamply-1.3-mini'
        def __init__(self):
            super().__init__()
    return merge_parser()


def cal_face_area(face_box):
    return (face_box[2]-face_box[0])*(face_box[3]-face_box[1])

def cal_eye_dist(boundaries):
    return np.sqrt(np.sum((boundaries['eye_center_right']-boundaries['eye_center_left'])**2))

def draw_headpose(raw_img, pitch, yaw, roll, face_box=None, size=50, thickness=(2,2,2), show_detail=False):
    """
    Function used to draw y (headpose label) on Input Image x.
    Implemented by: shamangary
    https://github.com/shamangary/FSA-Net/blob/master/demo/demo_FSANET.py
    Modified by: Omar Hassan
    """
    img = raw_img.copy()
    if show_detail:
        cv2.putText(img, 'p:%f y:%f r:%f'%(pitch, yaw, roll), (10, 40), cv2.FONT_HERSHEY_COMPLEX, 0.6, (0,0,255), 1)
    pitch = pitch * np.pi / 180
    yaw = -(yaw * np.pi / 180)
    roll = roll * np.pi / 180

    if face_box != None:
        tdx = (face_box[2]-face_box[0])//2+face_box[0]
        tdy = (face_box[3]-face_box[1])//2+face_box[1]
    else:
        height, width = img.shape[:2]
        tdx = width / 2
        tdy = height / 2

    # X-Axis pointing to right. drawn in red
    x1 = size * (np.cos(yaw) * np.cos(roll)) + tdx
    y1 = size * (np.cos(pitch) * np.sin(roll) + np.cos(roll) * np.sin(pitch) * np.sin(yaw)) + tdy

    # Y-Axis | drawn in green
    #        v
    x2 = size * (-np.cos(yaw) * np.sin(roll)) + tdx
    y2 = size * (np.cos(pitch) * np.cos(roll) - np.sin(pitch) * np.sin(yaw) * np.sin(roll)) + tdy

    # Z-Axis (out of the screen) drawn in blue
    x3 = size * (np.sin(yaw)) + tdx
    y3 = size * (-np.cos(yaw) * np.sin(pitch)) + tdy

    cv2.line(img, (int(tdx), int(tdy)), (int(x1),int(y1)),(0,0,255),thickness[0])
    cv2.line(img, (int(tdx), int(tdy)), (int(x2),int(y2)),(0,255,0),thickness[1])
    cv2.line(img, (int(tdx), int(tdy)), (int(x3),int(y3)),(255,0,0),thickness[2])

    return img


def render_face(img_raw, lands=[], face_box=None, headpose=None, radius=1, thickness=2, color=(0,255,0), inplace=False, lands_id=False):
    '''Render face landmarks and/or face_box in image.

    Args:
        img_raw(array):        opencv image
        lands(array):          (x1, y1, x2, y2, ...) or np.array([[x1, y1], [x2, y2], ...])
        face_box(array):       (left, top, right, bottom)

    Outs:
        img(array)
    '''
    img = img_raw
    if not inplace:
        img = np.zeros(img_raw.shape, dtype=img_raw.dtype)
        img[...] = img_raw[...]
    lands = np.reshape(lands, [-1,2])
    if face_box is not None:
        face_box = np.reshape(face_box, [-1])
        face_box = list(map(int, face_box))
        cv2.rectangle(img, (face_box[0], face_box[1]), (face_box[2], face_box[3]), color, thickness)
    for i, land in enumerate(lands):
        land = list(map(int, land))
        cv2.circle(img, (land[0], land[1]), radius, color, thickness)
        if lands_id:
            cv2.putText(img, '%d'%(i), (land[0]-10, land[1]-10), cv2.FONT_HERSHEY_COMPLEX, 0.6, (0,0,255), 1)
    if headpose is not None:
        img = draw_headpose(img, headpose[0], headpose[1], headpose[2], face_box=face_box, show_detail=True)
    return img


def warp_landmarks(landmarks, warp_mat):
    '''
    Apply warp transform to input landmarks.

    Args:
        landmarks(array/list):   [(x1, y1), (x2, y2), ...], landmark coordinates
        warp_mat(array):         [2, 3], affine transform matrix

    Returns:
        rotated_landmark(array): [N, 2]
    '''
    landmark_array = np.array(landmarks).reshape(-1,2)
    rotated_landmark = np.matmul(np.insert(landmark_array, [2], 1, axis=-1), np.transpose(warp_mat))
    return rotated_landmark


def warp_face_box(face_box, landmarks, warp_mat):
    '''
    Adjust face_box according to warped_lands after warp transform.

    Args:
        face_box(array/list):   [x1, y1, x2, y2], top-left and bottom-right coordinates
        landmarks(array):       [N, 2], facial landmarks
        warp_mat(array):        [2, 3], affine transform matrix

    Returns:
        new_bound_rect(array):  [4], adjusted bounding box [x1, y1, x2, y2]
    '''
    hairline_point = get_hairline_point_cropv3(face_box, landmarks, debug=False)
    warped_lands = warp_landmarks(landmarks, warp_mat)
    warped_hairline_point = warp_landmarks(hairline_point, warp_mat)
    new_bound_rect = cal_bounding_rect(warped_lands)
    new_bound_rect[1] = warped_hairline_point[0,1]
    return new_bound_rect


def warp_with_landmarks(img, landmarks, out_size, center, angle, scale=1.0, shift_xy=(0,0)):
    '''Warp affine transform image with landmarks.

    Args:
        img(array):            opencv image
        landmarks(array):      (x1, y1, x2, y2, ...) or np.array([[x1, y1], [x2, y2], ...])
        center(array):         (center_x, center_y)
        angle(float/int):      angle in degree

    Outs:
        rotated_img(array)
        rotated_landmark(array)
    '''
    rot_mat = cv2.getRotationMatrix2D((center[0], center[1]), angle, scale)
    rotated_img = cv2.warpAffine(img, rot_mat, (img.shape[1], img.shape[0]))
    rotated_landmark = warp_landmarks(landmarks, rot_mat)
    return rotated_img, rotated_landmark


def warp_back(img, src, warp_mat, mask_warp=True, remove_edge=False, keep_mask=False, **kwargs):
    """Warp img back to src.

    Args:
        img(array):            opencv image as foreground
        src(array):            opencv image as background

    Outs:
        back_img(array)        opencv image
    """
    if mask_warp:
        if img.shape[2] != 4:
            img = np.insert(img, [3], 1.0, axis=-1)
        else:
            img = np.float32(img)
            img[:,:,3] /= 255.0
    else:
        img = np.insert(np.float32(img[:,:,:3]), [3], 1.0, axis=-1)

    back_img = np.float32(cv2.warpAffine(img, cv2.invertAffineTransform(warp_mat), (src.shape[1], src.shape[0]), **kwargs))
    fg_mask = back_img[:,:,3:]
    if remove_edge:
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_ERODE, np.ones((7,7)))[:,:,np.newaxis]
    back_img = apply_mask_merge(back_img[:,:,:-1], src, fg_mask)
    if keep_mask:
        back_img = np.concatenate([back_img, fg_mask*255], axis=-1)
    back_img = np.uint8(back_img)
    return back_img


def warp_face_Delaunay(src_img, tgt_img, src_points, tgt_points):
    '''(Experimental) Warp two face in Delaunay way, not smooth
    '''
    def create_mask(triangles, shape):
        mask = np.zeros(shape, dtype=np.uint8)
        for tri in triangles:
            cv2.drawContours(mask, [tri], -1, (255, 255, 255), -1)
        return mask > 0

    def warp_triangle(img, fromTri, toTri):
        warpMat = cv2.getAffineTransform(np.float32(fromTri), np.float32(toTri))
        return cv2.warpAffine(img, warpMat, (img.shape[1], img.shape[0]), None, flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REFLECT_101)

    triangulation = Delaunay(tgt_points)
    warped_img = np.zeros(src_img.shape, dtype=src_img.dtype)
    for i, triangle in enumerate(triangulation.simplices):
        src_triangle = np.float32([src_points[i] for i in triangle])
        tgt_triangle = np.float32([tgt_points[i] for i in triangle])

        mask = create_mask([tgt_triangle.astype(np.int32)], warped_img.shape[:2])
        warped_piece = warp_triangle(src_img, src_triangle, tgt_triangle)
        np.copyto(warped_img, warped_piece, where=mask[:,:,None])

    return np.uint8(warped_img)


def warp_face_Delaunay_flow(src_img, tgt_img, src_points, tgt_points, patch_warp=False, patch_factor=1.1):
    '''(Experimental) Warp two face in Delaunay flow way, not smooth
    
    Using:
        src_points = bound1['triangulation']
        tgt_points = bound2['triangulation']
        out_grid = warp_face_Delaunay_flow(src_img, tgt_img, src_points, tgt_points)
        res = cv2.remap(src_img, out_grid, None, cv2.INTER_LINEAR)
    '''
    def create_mask(triangles, shape):
        mask = np.zeros(shape, dtype=np.uint8)
        for tri in triangles:
            cv2.drawContours(mask, [tri], -1, (255, 255, 255), -1)
        return mask > 0

    def warp_triangle(img, fromTri, toTri, shape):
        warpMat = cv2.getAffineTransform(np.float32(fromTri), np.float32(toTri))
        return cv2.warpAffine(img, warpMat, shape, None, flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_CONSTANT)
        
    def cal_patch_corner(points, padding):
        corner = cal_bounding_rect(points)
        corner = pad_rect(corner, padding_scale=padding)
        corner = cvt_box_format(corner, format='ltrb2cw').reshape((-1,2))
        return corner

    if patch_warp:
        src_corner = cal_patch_corner(src_points, patch_factor)
        tgt_corner = cal_patch_corner(tgt_points, patch_factor)
        src_points = np.concatenate([src_points, src_corner], axis=0)
        tgt_points = np.concatenate([tgt_points, tgt_corner], axis=0)

    out_shape = np.maximum(src_img.shape, tgt_img.shape)
    out_grid = np.zeros((out_shape[0], out_shape[1], 2), dtype=np.float32)

    x_grid, y_grid = np.meshgrid(np.arange(src_img.shape[1]), np.arange(src_img.shape[0]))
    xy_grid = np.float32(np.stack([x_grid, y_grid], axis=-1))

    # tform = skimage.transform.SimilarityTransform()
    # tform.estimate(src_points, tgt_points)
    # warp_mat_key = tform.params[0:2, :]
    # out_grid = cv2.warpAffine(xy_grid, warp_mat_key, (out_shape[1], out_shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    triangulation = Delaunay(tgt_points)
    for i, triangle in enumerate(triangulation.simplices):
        src_triangle = np.float32([src_points[i] for i in triangle])
        tgt_triangle = np.float32([tgt_points[i] for i in triangle])

        mask = create_mask([tgt_triangle.astype(np.int32)], out_shape[:2])
        warped_grid = warp_triangle(xy_grid, src_triangle, tgt_triangle, shape=(out_shape[1], out_shape[0]))
        np.copyto(out_grid, warped_grid, where=mask[:,:,None])

    # out_grid = cv2.blur(out_grid, (3,3))

    return out_grid


def warp_face_landsmarks(src_img, tgt_shape, src_points, tgt_points):
    '''
    Apply affine transformation on source image based on source and target points
    and warp it to match the target image.

    Args:
        src_img(array):         [Hs, Ws, Cs], source image
        tgt_shape(tuple):       [2, ], target shape (Ht, Wt)
        src_points(array):      [N, 2], np.array([[x1s, y1s], [x2s, y2s], ...]), Source points
        tgt_points(array):      [N, 2], np.array([[x1t, y1t], [x2t, y2t], ...]), Target points

    Returns:
        warped_img(array):      [Ht, Wt, Ct], Warped source image to match target image.
    '''
    tform = trans.SimilarityTransform()
    tform.estimate(src_points, tgt_points)
    M = tform.params[0:2, :]
    warped_img = cv2.warpAffine(src_img, M, (tgt_shape[1], tgt_shape[0]))
    return warped_img


def align_face(img, keypoints, output_size=None, rotate=True, **kwargs):
    '''Align face use OpenCV FFHQ method, is called "ffhq_fast".

    Args:
        img(array):             opencv image
        keypoints(tuple):       eye_left, eye_right, mouth_left, mouth_right in (x, y)
        output_size(int/tuple): output: [h,w] = [output_size, output_size/ratio] or [output_size[0], output_size[1]]
        rotate(bool):           if rotate image

    Outs:
        aligned_img(array)
        warp_mat(array):       used to align points or recover alignment
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
    antialias = kwargs.get('antialias', False)
    border_mode = kwargs.get('border_mode', cv2.BORDER_CONSTANT)
    border_value = kwargs.get('border_value', 0)
    if isinstance(output_size, tuple):
        output_size = int(output_size[0])

    # Get aligned image center and length
    center = eye_avg + eye_to_mouth * 0.1
    face_length = max(np.hypot(*eye_to_eye) * 2.0, np.hypot(*eye_to_mouth) * 1.8)

    # Get output shape
    face_lt = np.int64(center + 0.5) - np.int64(face_length + 0.5)
    face_rb = np.int64(center + 0.5) + np.int64(face_length + 0.5)
    if face_lt[0] > img.shape[1] or face_lt[1] > img.shape[0] or face_rb[0] < 0 or face_rb[1] < 0:
        llog.warning("face box outside the image (%s, %s)." % (face_lt, face_rb))
    face_size = face_rb - face_lt

    if rotate:
        rad = np.arctan2(eye_to_eye[1], eye_to_eye[0])
        angle = 180 * rad / np.pi
        if angle > 85 and angle < 95:
            llog.warning("nearly 90 degree (%f) rotation may cause inversion of left right." % angle)
    else:
        angle = 0

    if output_size and antialias:
        scale = 1.0
        warp_size = face_size[0]
    elif output_size:
        scale = output_size / face_size[0]
        warp_size = output_size
    else:
        scale = 1.0
        warp_size = face_size[0]
        antialias = False

    dst_lt = np.int64(center + 0.5) - np.int64(face_length * scale + 0.5)
    interp_method = cv2.INTER_CUBIC if scale > 1.0 else cv2.INTER_LINEAR
    warp_mat = cv2.getRotationMatrix2D((center[0], center[1]), angle, scale)
    warp_mat[0, 2] -= dst_lt[0]
    warp_mat[1, 2] -= dst_lt[1]
    aligned_img = cv2.warpAffine(img, warp_mat, (warp_size, warp_size), flags=interp_method, borderMode=border_mode, borderValue=border_value)
    # aligned_landmark = warp_landmarks(keypoints, warp_mat)
    if antialias:
        aligned_img = cv2.resize(aligned_img, (output_size, output_size), interpolation=cv2.INTER_AREA)
        warp_mat *= output_size / face_size[0]
    return aligned_img, warp_mat


def crop_face_v2(img, keypoints, landmarks):
    '''Crop 256:192 ratio face ROI according to cheek corner and chin, smallest face ROI

    Notice:
        - Compatible with FFHQ alignment (320x320 output)
        - Might not crop whole face region

    Args:
        img(array):            opencv image
        keypoints(array):      eye_left, eye_right, mouth_left, mouth_right in (x, y)
        landmarks(array):      landmarks with [0, 32] corresponding cheek contour

    Outs:
        crop_img(array)
        warp_mat(array):       used to align points or recover alignment
    '''
    eye_left, eye_right, mouth_left, mouth_right = np.reshape(keypoints, [-1,2])
    eye_avg      = (eye_left + eye_right) * 0.5
    eye_to_eye   = eye_right - eye_left
    mouth_avg    = (mouth_left + mouth_right) * 0.5
    eye_to_mouth = mouth_avg - eye_avg
    center = eye_avg + eye_to_mouth * 0.1
    face_length = max(np.hypot(*eye_to_eye) * 2.0, np.hypot(*eye_to_mouth) * 1.8)

    left_cheek_corner = np.mean(landmarks[:6], axis=0)
    right_cheek_corner = np.mean(landmarks[33-6:33], axis=0)
    chin = np.mean(landmarks[15:18], axis=0)
    cheek_vector = right_cheek_corner - left_cheek_corner

    rad = np.arctan2(cheek_vector[1], cheek_vector[0])
    angle = 180 * rad / np.pi
    warp_mat = cv2.getRotationMatrix2D((center[0], center[1]), angle, 1.0)

    scale_ratio = 2 * face_length / 320.0
    corner_dist = np.hypot(*cheek_vector)

    rect_top = warp_landmarks(left_cheek_corner, warp_mat)
    rect_bottom = warp_landmarks(chin, warp_mat)

    rotate_start_x = rect_top[0,0]
    rotate_end_y = rect_bottom[0,1]
    start_x = rotate_start_x - (192 * scale_ratio - corner_dist) // 2
    end_y = rotate_end_y + 5.0 * scale_ratio
    start_y = end_y - 256.0 * scale_ratio
    end_x = start_x + 192.0 * scale_ratio
    face_rect = (start_x, start_y, end_x, end_y)

    warp_mat[0,2] -= start_x
    warp_mat[1,2] -= start_y
    crop_img = cv2.warpAffine(img, warp_mat, (int(face_rect[2]-face_rect[0]), int(face_rect[3]-face_rect[1])))

    return crop_img, warp_mat


def crop_face_v3(img, keypoints, landmarks, rotate=True, output_size=None, **kwargs):
    '''Crop face ROI according to cheek corner and eye-mouth distance.

    Notice:
        - Dynamic adjust cropping regoin according to hp_factor, wd_factor, shift_factor

    Args:
        img(array):             opencv image
        keypoints(array):       eye_left, eye_right, mouth_left, mouth_right in (x, y)
        landmarks(array):       landmarks with [0, 32] corresponding cheek contour
        rotate(bool):           if rotate image
        output_size(int/tuple): output: [h,w] = [output_size, output_size/ratio] or [output_size[0], output_size[1]]
                                output to origin face size if output_size set to None

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
    border_mode = kwargs.get('border_mode', cv2.BORDER_CONSTANT)
    border_value = kwargs.get('border_value', 0)
    antialias = kwargs.get('antialias', False)
    max_warp_size = kwargs.get('max_warp_size', np.inf)   # performance setting, 512 is recommended
    debug = kwargs.get('debug', False)
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
        if debug:
            img = cv2.circle(img, (int(center[0]), int(center[1])), 2, (0,0,255), 2)
    else:
        rectify_width_half = face_width_half
        if debug:
            img = cv2.circle(img, (int(center[0]), int(center[1])), 2, (0,255,0), 2)

    rect_height = rectify_height_half * 2.0
    rect_width = rectify_width_half * 2.0
    # print(rect_height)

    if output_size and not antialias:
        warp_height = output_size_h
        warp_width = output_size_w
    else:
        warp_height = int(rect_height) if rect_height <= max_warp_size else max_warp_size
        warp_width = int(rect_width) if rect_height <= max_warp_size else int(max_warp_size / ratio)

    scale = warp_height / rect_height

    if rotate:
        rad = np.arctan2(cheek_vector[1], cheek_vector[0])
        angle = 180.0 * rad / np.pi
    else:
        angle = 0.0

    start_x = center[0] - rectify_width_half * scale
    start_y = center[1] - rectify_height_half * shift_factor * scale
    interp_method = cv2.INTER_CUBIC if scale > 1.0 else cv2.INTER_LINEAR
    warp_mat = cv2.getRotationMatrix2D((center[0], center[1]), angle, scale)
    warp_mat[0,2] -= start_x
    warp_mat[1,2] -= start_y
    if no_img:
        crop_img = None
    else:
        crop_img = cv2.warpAffine(img, warp_mat, (warp_width, warp_height), flags=interp_method, borderMode=border_mode, borderValue=border_value)
        if antialias:
            crop_img = cv2.resize(crop_img, (output_size_w, output_size_h), interpolation=cv2.INTER_AREA)

    if antialias:
        warp_mat *= output_size_h / rect_height

    # start_x = center[0] - rectify_width_half
    # end_x = start_x + rect_width
    # start_y = center[1] - rectify_height_half * shift_factor
    # end_y = start_y + rect_height
    # ori_face_corner = [start_x, start_y, start_x, end_y, end_x, end_y, end_x, start_y]
    # rotate_mat = cv2.getRotationMatrix2D((center[0], center[1]), -angle, 1.0)
    # ori_face_corner = warp_landmarks(ori_face_corner, rotate_mat)

    # face_corner = [0, 0, 0, output_size_h, output_size_w, output_size_h, output_size_w, 0]
    # ori_face_corner = warp_landmarks(face_corner, cv2.invertAffineTransform(warp_mat))

    return crop_img, warp_mat


def crop_face_v4(img, face_box, keypoints=[], rotate=False, ratio=1.0, output_size=None):
    '''Crop face ROI according to face box.

    Args:
        img(array):            opencv image
        face_box(array):       [left, top, right, bottom]
        keypoints(array):      eye_left, eye_right, ... in (x, y)
        output_size(int):      output: h = output_size, w = output_size/ratio

    Outs:
        crop_img(array)
        warp_mat(array):       used to align points or recover alignment
    '''
    face_box = np.reshape(face_box, (-1, 2))
    face_size = face_box[1,:] - face_box[0,:]
    center = face_box[0] + face_size / 2
    face_max_size = max(face_size[0], face_size[1])
    face_length_h = face_max_size * 1.2
    face_length_w = face_length_h / ratio
    face_length = np.array([face_length_w, face_length_h])

    if output_size:
        scale = output_size / face_length_h
        output_size_h = int(output_size)
        output_size_w = int(output_size / ratio)
    else:
        scale = 1.0
        output_size_h = int(face_length_h)
        output_size_w = int(face_length_w)

    if rotate:
        keypoints = np.reshape(keypoints, [-1,2])
        eye_left = keypoints[0]
        eye_right = keypoints[1]
        eye_avg      = (eye_left + eye_right) * 0.5
        eye_to_eye   = eye_right - eye_left
        rad = np.arctan2(eye_to_eye[1], eye_to_eye[0])
        angle = 180 * rad / np.pi
    else:
        angle = 0

    dst_lt = center - face_length * scale / 2
    interp_method = cv2.INTER_CUBIC if scale > 1.0 else cv2.INTER_LINEAR
    warp_mat = cv2.getRotationMatrix2D((center[0], center[1]), angle, scale)
    warp_mat[0,2] -= dst_lt[0]
    warp_mat[1,2] -= dst_lt[1]
    crop_img = cv2.warpAffine(img, warp_mat, (output_size_w, output_size_h), flags=interp_method)

    return crop_img, warp_mat


def get_landmarks_boundaries(landmarks, method='AdaptiveWing'):
    if method == 'AdaptiveWing':
        from ..thirdparty.AdaptiveWing.interface import AdaptiveWing
        boundaries = AdaptiveWing.to_boundaries(landmarks)
    else:
        raise NotImplementedError(f"avaliable method ['AdaptiveWing'], get {method}")
    return boundaries


def get_hairline_point_cropv3(face_box, landmarks, rotate=True, debug=False):
    if not rotate:
        hairline_point = np.array([(face_box[2]+face_box[0])/2, face_box[1]])
        return hairline_point
    landmarks = np.array(landmarks).reshape(-1,2)
    left_cheek_corner = np.mean(landmarks[:6], axis=0)
    right_cheek_corner = np.mean(landmarks[33-6:33], axis=0)
    center = (right_cheek_corner+left_cheek_corner) / 2.0
    cheek_vector = right_cheek_corner - left_cheek_corner
    k = - cheek_vector[0] / cheek_vector[1]   # set minus because the image x-y axis is right-bottom, set k=(x / y) indicates rotation
    k = np.clip(k, -1e7, 1e7)                 # cut value for numerical stability
    b = center[1] - k * center[0]
    y0 = face_box[1]
    x0 = (y0 - center[1]) / k + center[0]
    if x0 > face_box[2] or x0 < face_box[0]:
        if debug:
            raise RuntimeError(f"bravo! x0={x0}, y0={y0}, k={k}, b={b}")
        x0 = face_box[2] if k < 0 else face_box[0]
        y0 = k * x0 + b
    hairline_point = np.array([x0, y0])
    return hairline_point


def generate_face_mask(src_height, src_width, landmarks, include_forehead=True, top_y=-1, fast=False, remove_ROI=False, version='lamply-1.0', **kwargs):
    """
    Generates a mask for a face given facial landmarks.

    Args:
        src_height (int):                   Height of the source image.
        src_width (int):                    Width of the source image.
        landmarks (list or np.ndarray):     Facial landmarks detected from the source image.
        include_forehead (bool, optional):  Whether to include the forehead region in the mask. Default is True.
        top_y (int, optional):              The top y coordinate of the forehead region. Only used when include_forehead is True.
                                            -1 means calculate top_y automatically, Default is -1.
        fast (bool, optional):              Whether to use a faster algorithm for generating the mask. Default is False.
        remove_ROI(bool, optional):         Whether to remove ROI.
        version (str, optional):            The version of the facial landmarks used. Currently supports 'lamply-1.0' and 'normal-68'. Default is 'lamply-1.0'.
        **kwargs:                           Additional keyword arguments to be passed to the generate_contours_mask function.

    Returns:
        np.ndarray: float mask of the face with 1's indicating the foreground and 0's indicating the background.
    """
    def bezier_func(t, P0, P1, P2):
        return (1 - t)**2 * P0 + 2 * t * (1 - t) * P1 + t**2 * P2

    landmarks = np.array(landmarks)
    if version.split('.')[0] == 'lamply-1':
        boundaries = get_landmarks_boundaries(landmarks)
        eye_left = landmarks[96]
        eye_right = landmarks[97]
        left_cheek_top = landmarks[0]
        right_cheek_top = landmarks[32]
        landmarks = np.array(landmarks)
    elif version == 'normal-68':
        landmarks = np.reshape(landmarks, (-1, 2))
        boundaries = {}
        boundaries['cheek'] = landmarks[:17]
        boundaries['eyebrow_left'] = landmarks[17:22]
        boundaries['eyebrow_right'] = landmarks[22:27]
        eye_left = np.mean(landmarks[36:42], axis=0)
        eye_right = np.mean(landmarks[42:48], axis=0)
        left_cheek_top = landmarks[0]
        right_cheek_top = landmarks[16]
    else:
        raise NotImplementedError('not implement for version:', version)

    if include_forehead:
        if top_y == -1:
            top_center = get_hairline_point_cropv3(kwargs['face_box'], landmarks, rotate=False)
            top_y = top_center[1]
        else:
            top_center = (eye_left + eye_right) / 2
            top_center[1] = top_y
        top_left = np.array([left_cheek_top[0], top_y])
        top_right = np.array([right_cheek_top[0], top_y])
        inter_t = np.linspace(0, 1, 5)[1:-1]
        boundaries['left_head'] = np.array([bezier_func(t,top_center,top_left,left_cheek_top) for t in inter_t])
        boundaries['right_head'] = np.array([bezier_func(t,right_cheek_top,top_right,top_center) for t in inter_t])
        contours = np.int64(np.concatenate((boundaries['cheek'], boundaries['right_head'], top_center.reshape(-1,2), boundaries['left_head'])))
    else:
        contours = np.int64(np.concatenate((boundaries['cheek'], boundaries['eyebrow_right'][::-1], boundaries['eyebrow_left'][::-1])))

    if not fast:
        blur = True
        dilate = True
    else:
        blur = False
        dilate = False
    fg_mask = generate_contours_mask(src_height, src_width, [contours], blur=blur, dilate=dilate, **kwargs)

    if remove_ROI:
        contours = []
        contours += [np.int64((boundaries['eyebrow_left']))]
        contours += [np.int64((boundaries['eyebrow_right']))]
        contours += [np.int64((boundaries['eyelid_left']))]
        contours += [np.int64((boundaries['eyelid_right']))]
        contours += [np.int64((boundaries['lip_outer']))]
        remove_mask_ROI = 1.0 - generate_contours_mask(src_height, src_width, contours, blur=blur, dilate=dilate)
        fg_mask = fg_mask * remove_mask_ROI

    return fg_mask


def generate_under_cheek_mask(cheek_points, img_hw, depth=8, **kwargs):
    """
    Generates a mask under cheek.

    Args:
        cheek_points (np.ndarray):          Facial landmarks detected from the source image.
        img_hw (list):                      Image height and width.
        depth (int, optional):              The depth of the points to be considered under the cheek.

    Returns:
        np.ndarray: The generated mask under cheek.
    """
    num_cp = cheek_points.shape[0]
    # Get the initial and the final cheek point based on the depth
    close_s1 = copy.deepcopy(cheek_points[[depth]])
    close_e1 = copy.deepcopy(cheek_points[[num_cp-depth-1]])
    # Create two additional points to join the initial and final points to the edges
    close_s2 = copy.deepcopy(close_s1)
    close_e2 = copy.deepcopy(close_e1)
    close_s1[0, 0] = 0
    close_s1[0, 1] = img_hw[0]
    close_e1[0, 0] = img_hw[1]
    close_s2[0, 0] = 0
    close_e2[0, 0] = img_hw[1]
    close_e2[0, 1] = img_hw[0]
    # Concatenate all the points to draw contours
    contours = [np.int64(np.concatenate((close_s1, close_s2, cheek_points[depth:num_cp-depth], close_e1, close_e2)))]
    # Generate contours mask from the contours
    under_cheek_mask = generate_contours_mask(img_hw[0], img_hw[1], contours, **kwargs)
    return under_cheek_mask



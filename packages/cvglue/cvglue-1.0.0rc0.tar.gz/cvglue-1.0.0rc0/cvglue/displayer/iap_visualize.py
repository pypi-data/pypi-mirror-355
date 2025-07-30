import numpy as np
import cv2
from ..utils import render_face, render_mask, draw_headpose
from ..parser import anno_exists

__all__ = ['render_lamply']


def render_lamply(iap_data, disable_domain=[]):
    """Visualize iap_data with lamply annotations

    Args:
        iap_data (tuple):                 iap data (image, annotations)
        disable_domain (list, optional):  hiding specify domain. Defaults to [].

    Returns:
        img_disp (np.array):              image with annotaion visualized
    """
    img_disp = np.uint8(iap_data[0].copy())
    if anno_exists(iap_data[1], 'faces'):
        for face in iap_data[1]['faces']:
            face_box = face['face_box']
            face_box = list(map(int, face_box))
            cv2.rectangle(img_disp, (face_box[0], face_box[1]), (face_box[2], face_box[3]), (0, 0, 255), 2)
            if anno_exists(face, 'key_points') and 'key_points' not in disable_domain:
                key_points = face['key_points']
                key_points = list(map(int, key_points))
                thickness = max(img_disp.shape[0], img_disp.shape[1]) // 200
                cv2.circle(img_disp, (key_points[0], key_points[1]), 1, (0, 0, 255), thickness)
                cv2.circle(img_disp, (key_points[2], key_points[3]), 1, (0, 255, 255), thickness)
                cv2.circle(img_disp, (key_points[4], key_points[5]), 1, (255, 0, 255), thickness)
                cv2.circle(img_disp, (key_points[6], key_points[7]), 1, (0, 255, 0), thickness)
                if len(key_points) > 8:
                    cv2.circle(img_disp, (key_points[8], key_points[9]), 1, (255, 0, 0), thickness)
            if anno_exists(face, 'landmarks') and 'landmarks' not in disable_domain:
                img_disp = render_face(img_disp, face['landmarks'], thickness=max(img_disp.shape[0], img_disp.shape[1]) // 300)
            if anno_exists(face, 'gender') and anno_exists(face, 'age') and 'genderage' not in disable_domain:
                gender = 'female' if face['gender'] == 0 else 'male'
                cv2.putText(img_disp, '%s,%d'%(gender,face['age']), (face_box[0]-1, face_box[1]-4), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0,255,0), 1)
            if anno_exists(face, 'headpose') and 'headpose' not in disable_domain:
                img_disp = draw_headpose(img_disp, *face['headpose'], face_box=face['face_box'])
    if anno_exists(iap_data[1], 'masks'):
        if anno_exists(iap_data[1]['masks'], 'portrait') and 'portrait' not in disable_domain:
            mask = cv2.imread(iap_data[1]['masks']['portrait'])
            img_disp = render_mask(img_disp, mask, channel=2)
    return img_disp

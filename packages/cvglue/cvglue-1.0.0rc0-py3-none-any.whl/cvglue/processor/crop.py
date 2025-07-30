import copy
import numpy as np
import functools
from ..utils.faceutils import *
from ..parser import anno_exists, set_image_anno

__all__ = ["crop_processor"]

class crop_processor():
    def __init__(self, method, params, parser_version):
        self.method = method
        self.params = params
        if parser_version.split('-')[0] != 'lamply':
            raise NotImplementedError("parser version %s not supported" % parser_version)
        def process_func(iap_data):
            processed_data = []
            for i, face in enumerate(iap_data[1]['faces']):
                if face['confidence'] < params.get('conf_thres', 0.0):
                    continue
                if method == crop_face_v3.__name__:
                    crop_img, warp_mat = crop_face_v3(iap_data[0], face['key_points'], face['landmarks'], **params)
                elif method == crop_face_v4.__name__:
                    crop_img, warp_mat = crop_face_v4(iap_data[0], face['face_box'], face['key_points'], **params)
                elif method == norm_crop.__name__:
                    crop_img, warp_mat = norm_crop(iap_data[0], face['key_points'], **params)
                else:
                    raise NotImplementedError('Method %s is not implemented' % method)
                cropped_face = copy.deepcopy(face)
                cropped_face['face_box'] = list(warp_face_box(face['face_box'], face['landmarks'], warp_mat).reshape(-1))
                cropped_face['key_points'] = list(warp_landmarks(face['key_points'], warp_mat).reshape(-1))
                cropped_face['landmarks'] = warp_landmarks(face['landmarks'], warp_mat).tolist()
                if params.get('rotate', True) and cropped_face.get('headpose'):
                    cropped_face['headpose'][2] = 0.0
                id_suffix = '_'+str(i) if len(iap_data[1]['faces']) > 1 else ''
                face_img_name = iap_data[1]['name'] + id_suffix
                crop_anno = {'name': face_img_name} if params.get('no_img', False) else set_image_anno(face_img_name, 
                                                                                height=crop_img.shape[0], 
                                                                                width=crop_img.shape[1], 
                                                                                channel=crop_img.shape[2])
                crop_anno['faces'] = [cropped_face]
                for key in iap_data[1]:
                    if key not in crop_anno:
                        crop_anno[key] = iap_data[1][key]
                processed_data += [(crop_img, crop_anno)]
            return None if len(processed_data) == 0 else processed_data
        self.process_func = process_func

    def dump_config(self):
        config = {"__name__": "crop_processor", "method": self.method}
        config.update(self.params)
        return config

    def __call__(self, iap_data):
        return self.process_func(iap_data)
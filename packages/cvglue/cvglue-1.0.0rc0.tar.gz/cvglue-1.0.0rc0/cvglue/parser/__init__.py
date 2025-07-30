import PIL.ImageFile
from typing import Union
import numpy as np

PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True # avoid "Decompressed Data Too Large" error

__all__ = ["set_image_anno", "anno_exists", "get_parser", 
           "face_parser", "landmarks_parser", "blur_parser", 
           "attribute_parser", "genderage_parser", "faceid_parser", 
           "quality_parser"]

def set_image_anno(base_name, **kwargs):
    return {"name": base_name, **kwargs}

def anno_exists(anno: dict, domain: Union[str, list], **kwargs):
    if isinstance(domain, list):
        logit = [anno_exists(anno, spec) for spec in domain]
        return np.sum(logit) == len(domain)
    if not anno.__contains__(domain):
        return False
    if isinstance(anno[domain], (dict, list)) and len(anno[domain]) == 0:
        return False
    return True

from .base import base_parser
# from .mask import mask_parser
from .face import face_parser, landmarks_parser, blur_parser, attribute_parser, genderage_parser, faceid_parser, quality_parser

def get_parser(version):
    if 'lamply' in version:
        if 'faceid' in version:
            class merge_parser(faceid_parser, blur_parser, quality_parser, attribute_parser, landmarks_parser, face_parser):
                __version__ = 'lamply-1.3-faceid'
                def __init__(self):
                    super().__init__()
        else:
            class merge_parser(blur_parser, quality_parser, attribute_parser, landmarks_parser, face_parser):
                __version__ = 'lamply-1.3'
                def __init__(self):
                    super().__init__()
    else:
        raise NotImplementedError(version, "is not avaliable.")
    return merge_parser()

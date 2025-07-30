import os
import cv2
from .base import base_parser

__all__ = ["attribute_parser", "blur_parser", "face_parser", "faceid_parser", 
           "genderage_parser", "landmarks_parser", "quality_parser"]


class face_parser(base_parser):
    def __init__(self, method='lamply', mode='selfie', **kwargs):
        super().__init__()
        if method == 'lamply':
            self.set_lamply_detector(mode, **kwargs)
        elif method == 'insightface':
            self.set_insightface_detector()
        else:
            raise NotImplementedError('method %s is not implemented, choose one of [lamply, insightface]' % method)

    def set_lamply_detector(self, mode, **kwargs):
        from ..detector import face_detector
        self.fd = face_detector(detect_mode=mode, **kwargs)
        self.detector_bank += [self.face_bbox_keypoints_detector]

    def set_insightface_detector(self):
        from insightface.app import FaceAnalysis
        self.app = FaceAnalysis(root='/workspace/cpfs-data/pretrained_models', providers=['CUDAExecutionProvider'])
        self.app.prepare(ctx_id=0)
        self.detector_bank += [self.face_analysis_detector]
        # self.verison = 'insightface-' + insightface.__version__

    def face_bbox_keypoints_detector(self, img):
        face_list = []
        try:
            dets = self.fd(img)
            face_cnt = dets.shape[0] if len(dets) > 0 else 0
        except Exception as e:
            print(repr(e))
            return {}

        cal_face_area = lambda face_box: (face_box[2]-face_box[0])*(face_box[3]-face_box[1])
        for i in range(face_cnt):
            face_box = list(dets[i,:4])
            lx = face_box[0] if face_box[0] > 0 else 0
            ly = face_box[1] if face_box[1] > 0 else 0
            rx = face_box[2] if face_box[2] < img.shape[1] else img.shape[1]
            ry = face_box[3] if face_box[3] < img.shape[0] else img.shape[0]
            inout_area = cal_face_area((lx, ly, rx, ry)) / cal_face_area(face_box)
            face_list += [{"face_box":face_box, "inout_area":inout_area, "confidence":dets[i,4], "key_points":list(dets[i,5:])}]

        return {"faces":face_list}

    def face_analysis_detector(self, img):
        try:
            face_list = self.app.get(img)
        except Exception as e:
            print(repr(e))
            return {}
        return {"faces":face_list}


class landmarks_parser(base_parser):
    def __init__(self, method='adaptivewing'):
        super().__init__()
        if method == 'adaptivewing':
            self.set_adaptivewing_detector()
        else:
            raise NotImplementedError('method %s is not implemented, choose one of [adaptivewing]' % method)

    def set_adaptivewing_detector(self):
        from ..detector import landmark_detector
        self.ld = landmark_detector()
        self.detector_bank += [self.adaptivewing_detector]

    def adaptivewing_detector(self, img):
        base_name = ''
        try:
            base_name = self.current_obj_dict.get('name', '')
            update_dict = self.current_obj_dict['faces']
            for face in update_dict:
                face_box = face['face_box']
                lands = self.ld(img, face_box)
                face['landmarks'] = lands.tolist()
        except Exception as e:
            print(base_name, repr(e))
        return {}


class attribute_parser(base_parser):
    def __init__(self, method='headpose'):
        super().__init__()
        if method == 'headpose':
            self.set_headpose_detector()
        else:
            raise NotImplementedError('method %s is not implemented, choose one of [headpose]' % method)

    def set_headpose_detector(self):
        from ..detector import attribute_detector
        self.ad = attribute_detector()
        self.detector_bank += [self.face_attribute_detector]

    def face_attribute_detector(self, img):
        base_name = ''
        try:
            base_name = self.current_obj_dict.get('name', '')
            update_dict = self.current_obj_dict['faces']
            for face in update_dict:
                headpose_pyr = self.ad(img, face['face_box'])
                face['headpose'] = headpose_pyr
        except Exception as e:
            print(base_name, repr(e))
        return {}


class genderage_parser(base_parser):
    def __init__(self, method='insightface'):
        super().__init__()
        if method == 'insightface':
            self.set_genderage_detector()
        else:
            raise NotImplementedError('method %s is not implemented, choose one of [headpose]' % method)

    def set_genderage_detector(self):
        import insightface
        from insightface.app import FaceAnalysis
        kwargs = {'providers': ['CUDAExecutionProvider']}
        self.app = FaceAnalysis(root='/workspace/cpfs-data/pretrained_models', **kwargs)
        self.app.prepare(ctx_id=0)
        self.face_dict = insightface.app.common.Face({'bbox':None})
        self.detector_bank += [self.face_genderage_detector]

    def face_genderage_detector(self, img):
        base_name = ''
        try:
            base_name = self.current_obj_dict.get('name', '')
            update_dict = self.current_obj_dict['faces']
            for face in update_dict:
                self.face_dict['bbox'] = face['face_box']
                gender, age = self.app.models['genderage'].get(img, self.face_dict)
                face['gender'] = int(gender)
                face['age'] = int(age)
        except Exception as e:
            print(base_name, repr(e))
        return {}


class faceid_parser(base_parser):
    def __init__(self, method='insightface'):
        super().__init__()
        if method == 'insightface':
            self.set_faceid_detector()
        else:
            raise NotImplementedError('method %s is not implemented, choose one of [headpose]' % method)

    def set_faceid_detector(self):
        from ..detector import faceid_detector
        self.faid_detector = faceid_detector('model_ir_se50')
        self.detector_bank += [self.face_id_detector]

    def face_id_detector(self, img):
        base_name = ''
        try:
            base_name = self.current_obj_dict.get('name', '')
            update_dict = self.current_obj_dict['faces']
            for face in update_dict:
                face['faceid'] = self.faid_detector(img, face['key_points']).flatten().tolist()
        except Exception as e:
            print(base_name, repr(e))
        return {}


class blur_parser(base_parser):
    def __init__(self, method='opencv'):
        super().__init__()
        if method == 'opencv':
            self.set_blur_detector()
        else:
            raise NotImplementedError('method %s is not implemented, choose one of [insightface]' % method)

    def set_blur_detector(self):
        from ..checker import blur_checker
        self.blur_detector = blur_checker()
        self.detector_bank += [self.blur_detect]

    def blur_detect(self, img):
        try:
            update_dict = self.current_obj_dict['faces']
            for face in update_dict:
                self.blur_detector.check_image(img, face)
                face['blurriness'] = self.blur_detector.score
        except:
            pass
        return {}


class quality_parser(base_parser):
    def __init__(self, method='tface'):
        super().__init__()
        if method == 'tface':
            self.set_face_quality_detector()
        else:
            raise NotImplementedError('method %s is not implemented, choose one of [headpose]' % method)

    def set_face_quality_detector(self):
        from ..detector import quality_detector
        self.qd = quality_detector('r50')
        self.detector_bank += [self.face_quality_detector]

    def face_quality_detector(self, img):
        base_name = ''
        try:
            base_name = self.current_obj_dict.get('name', '')
            update_dict = self.current_obj_dict['faces']
            for face in update_dict:
                face['quality'] = self.qd(img, face['key_points']).item()
        except Exception as e:
            print(base_name, repr(e))
        return {}



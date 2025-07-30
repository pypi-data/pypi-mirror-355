import os
import numpy as np
import cv2

class HeadPoseDetector:
    def __init__(self):
        import onnxruntime
        weights_path = os.path.dirname(os.path.abspath(__file__)) 
        self.sess = onnxruntime.InferenceSession(os.path.join(weights_path, 'weights/fsanet.onnx'), providers=['CUDAExecutionProvider','CPUExecutionProvider'])
        self.sess2 = onnxruntime.InferenceSession(os.path.join(weights_path, 'weights/fsanet_var.onnx'), providers=['CUDAExecutionProvider','CPUExecutionProvider'])
        self.sess3 = onnxruntime.InferenceSession(os.path.join(weights_path, 'weights/fsanet_noS.onnx'), providers=['CUDAExecutionProvider','CPUExecutionProvider'])

    def detect(self, img, face_box):
        '''Detect head pose from face ROI.

        Args:
            img:            3-channels opencv image
            face_box:       face_box detected by face detector

        Outs:
            pitch:          degree, negative is downside, positive is upside.           outer of [-30, 30] will not perform well 
            yaw:            degree, negative is turn right, positive is turn left.      perform well
            roll:           degree, negative is anti-closewise, positive is closewise.  perform well
        '''
        x1,y1,x2,y2 = map(int, face_box)
        ad = 0.6
        w = x2-x1
        h = y2-y1
        img_w = img.shape[1]
        img_h = img.shape[0]
        xw1 = max(int(x1 - ad * w), 0)
        yw1 = max(int(y1 - ad * h), 0)
        xw2 = min(int(x2 + ad * w), img_w - 1)
        yw2 = min(int(y2 + ad * h), img_h - 1)
        face_roi = cv2.resize(img[yw1:yw2 + 1, xw1:xw2 + 1, :], (64, 64))
        face_roi = cv2.normalize(face_roi, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        face_roi = np.expand_dims(face_roi,axis=0)
        face_roi = face_roi.astype(np.float32)
        res1 = self.sess.run(["pred_pose/mul_24:0"], {"input_1:0": face_roi})[0]
        res2 = self.sess2.run(["pred_pose/mul_24:0"], {"input_1:0": face_roi})[0]
        res3 = self.sess3.run(["pred_pose/mul_24:0"], {"input_1:0": face_roi})[0]
        yaw,pitch,roll = np.mean(np.vstack((res1,res2,res3)),axis=0,dtype=np.float64)
        return pitch, yaw, roll

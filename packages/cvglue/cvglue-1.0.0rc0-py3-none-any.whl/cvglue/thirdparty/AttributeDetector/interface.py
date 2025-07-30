import os
import json
import cv2
import pandas as pd
from . import sklearn_json as skljson
import face_recognition
from face_recognition import face_locations

class AttributeDetector():
    def __init__(self, mode='hog'):
        weights_path = os.path.dirname(os.path.abspath(__file__)) 
        self.clf = skljson.from_json(os.path.join(weights_path, 'face_model.json'))
        with open(os.path.join(weights_path, 'labels.json')) as f:
            self.labels = json.load(f)
        self.mode = mode

    def detect(self, img):
        """Detect facial image attribute

        Args:
            img(array):   RGB facial image array
        """
        # training in lfwa+ 250x250
        img = cv2.resize(img, (250, 250), interpolation=cv2.INTER_AREA)
        locs = face_locations(img, model=self.mode)
        if len(locs) == 0:
            raise RuntimeError('empty face')
        # seems expected 150x150 image
        face_encodings = face_recognition.face_encodings(img, known_face_locations=locs)
        if not face_encodings:
            raise RuntimeError('empty encodings')
        res = self.clf.predict_proba(face_encodings)
        return res

# interest_list = [
#  'Male',
#  'Asian',
#  'White',
#  'Black',
#  'Indian',
#  'Baby',      # inaccurate
#  'Child',     # inaccurate
#  'Youth',
#  'Middle Aged',
#  'Senior',
#  'Shiny Skin',
#  'Pale Skin',
#  'Heavy Makeup',
#  'Strong Nose-Mouth Lines',
#  'Wearing Lipstick',
#  'Rosy Cheeks',
#  'Flushed Face',
#  'Blurry',
#  'Flash',
#  'Harsh Lighting',   # inaccurate
#  'Soft Lighting']    # inaccurate

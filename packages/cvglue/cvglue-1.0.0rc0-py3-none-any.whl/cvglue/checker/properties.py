from .base import base_checker

__all__ = ["image_properties_checker"]


class image_properties_checker(base_checker):
    def __init__(self, min_size=None, max_size=None, hw_ratio=0.0, verbose=False):
        super().__init__()
        self.min_size = min_size
        self.max_size = max_size
        self.hw_ratio = hw_ratio
        self.verbose = verbose

    def check_image(self, img_raw):
        if self.min_size:
            if img_raw.shape[0] < self.min_size[0] or img_raw.shape[1] < self.min_size[1]:
                return False
        if self.max_size:
            if img_raw.shape[0] > self.max_size[0] or img_raw.shape[1] > self.max_size[1]:
                return False
        if self.hw_ratio != 0.0:
            return img_raw.shape[0] / img_raw.shape[1] >= self.hw_ratio
        return True

    def check_data(self, iap_data):
        if self.min_size:
            if iap_data[1]['height'] < self.min_size[0] or iap_data[1]['width'] < self.min_size[1]:
                return False
        if self.max_size:
            if iap_data[1]['height'] > self.max_size[0] or iap_data[1]['width'] > self.max_size[1]:
                return False
        if self.hw_ratio != 0.0:
            return iap_data[1]['height'] / iap_data[1]['width'] >= self.hw_ratio
        return True

"""Multi-process example

Notice:
    1. sample checker is not designed for this situation.
"""
import os
import argparse
import cvglue
import iap

def parse_args():
    parser = argparse.ArgumentParser(description='Generator')
    parser.add_argument('--pid', type=int, help='worker id')
    parser.add_argument('--num_worker', type=int, help='worker number')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    opts = parse_args()
    root_dir = './'
    A_set = iap.IAPDataset(os.path.join(root_dir, 'metadata.yml'))
    idx_list = list(range(A_set.metadata['size']))
    crop_params = {'output_size': [512, 512], 'hp_factor': 1.7, 'wd_factor': 0.6, 'shift_factor': 1.1, 'use_chin': True, 'border_mode': 0, 'border_value': 127, 'antialias': True}
    processor = cvglue.processor.crop_processor('crop_face_v3', crop_params, 'lamply-1.0')
    A_set.pipeline('cropD_sub'+str(opts.pid), [processor], idx_list[opts.pid::opts.num_worker])

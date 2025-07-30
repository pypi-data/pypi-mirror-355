import os
import glob
import re
import json
import requests
import numpy as np
from typing import List
try:
    from deepdiff import DeepDiff
    # pip install u-msgpack-python
    import umsgpack
except:
    pass

from .logger import setup_logger
llog = setup_logger(name=__name__)

SUPPORTED_IMG_EXTENSIONS = [
    '.jpg', '.JPG', '.jpeg', '.JPEG',
    '.png', '.PNG', '.bmp', '.BMP'
]

SUPPORTED_VIDEO_EXTENSIONS = [
    '.mp4', '.MP4', '.flv', '.FLV'
]

__all__ = ["check_aligned_img_dataset", "check_dict_differences", "check_grouped_img_dataset", 
           "check_if_overlap_files", "check_image_format", "convert_valid_name", "download_url", 
           "get_base_name", "get_ext_name", "get_file_name", "make_dataset", "make_grouped_dataset", 
           "make_structural_dataset", "read_json_file", "select_subdataset", "select_subdataset_idxs", 
           "write_json_file", "SUPPORTED_IMG_EXTENSIONS"]


def get_file_name(file_path):
    file_name = os.path.basename(file_path)
    return file_name

def get_base_name(file_path):
    file_name = get_file_name(file_path)
    split_name = file_name.split('.')
    base_name = '.'.join(split_name[:-1]) if len(split_name) > 1 else split_name[0]
    return base_name

def get_ext_name(file_path):
    try:
        ext_name = os.path.splitext(file_path)[-1]
    except:
        ext_name = None
    return ext_name

def convert_valid_name(name: str, invalid_char: str = r"[^\w\s.-]", replace: str = "") -> str:
    return re.sub(invalid_char, replace, name)


def make_dataset(dir):
    paths = []
    for ext in SUPPORTED_IMG_EXTENSIONS:
        paths += glob.glob(os.path.join(dir, '*'+ext))
    return paths

def select_subdataset(dataset, subset_list, path2name=False):
    name_list = [get_base_name(p) for p in subset_list] if path2name else subset_list
    return [p for p in dataset if get_base_name(p) in name_list]

def select_subdataset_idxs(dataset, subset_list, path2name=False):
    name_list = [get_base_name(p) for p in subset_list] if path2name else subset_list
    return [i for i, p in enumerate(dataset) if get_base_name(p) in name_list]

def make_grouped_dataset(dir):
    images = []
    assert os.path.isdir(dir), '%s is not a valid directory' % dir
    sequences_dir = sorted(os.listdir(dir))
    for seq in sequences_dir:
        seq_dir = os.path.join(dir, seq)
        if os.path.isdir(seq_dir) and seq[0] != '.':
            paths = sorted(make_dataset(seq_dir))
            if len(paths) > 0:
                images.append(paths)
    return images

def make_structural_dataset(root_dir, leaf_depth):
    '''Build structural dataset which images place in the leaf of directory tree.

    Args:
        root_dir(str):            root directory
        leaf_depth(int):          depth of leaf

    Outs:
        dataset(dict)
    '''
    def recursive_list(cur_dir, cur_depth=0):
        cur_depth += 1
        if cur_depth == leaf_depth:
            return sorted(make_dataset(cur_dir))
        dataset_tree = {}
        for file_name in os.listdir(cur_dir):
            file_path = os.path.join(cur_dir, file_name)
            if os.path.isdir(file_path) and file_name[0] != '.':
                dataset_tree[file_name] = recursive_list(os.path.join(cur_dir, file_name), cur_depth)
        return dataset_tree

    dataset = recursive_list(root_dir)
    return dataset


def check_if_overlap_files(paths):
    from collections import Counter
    base_names = [get_base_name(path) for path in paths]
    count_list = dict(Counter(base_names))
    return {key:value for key,value in count_list.items()if value > 1}


def check_image_format(img, allow_float=False, fix_channels=True):
    if img is None:
        raise RuntimeError("Image is empty!")

    if fix_channels:
        if len(img.shape) == 2 or len(img.shape) == 3:
            img = img.reshape([img.shape[0], img.shape[1], -1])
        else:
            raise ValueError(f"Image is not regular image! img.shape: {img.shape}")

    if img.dtype == np.uint8:
        pass
    elif img.dtype == (np.float32, np.float64):
        if not allow_float:
            llog.info(f"Image data type is not uint8 and {img.dtype} is not allowed, convert to uint8 format")
            img = np.uint8(np.clip(img, 0, 255))
    else:
        raise TypeError(f"Image data type {img.dtype} is unexpected.")

    return img


def check_aligned_img_dataset(A_paths, B_paths):
    if len(A_paths) == 0:
        raise Exception("Dataset A is empty, please check the `dataroot` option.")
    if len(A_paths) != len(B_paths):
        raise ValueError("Different size of A=%d and B=%d " % (len(A_paths), len(B_paths)))
    for i in range(len(A_paths)):
        A_name = get_base_name(A_paths[i])
        B_name = get_base_name(B_paths[i])
        if A_name != B_name:
            raise ValueError("A and B names is not aligned: {}, {}".format(A_paths[i], B_paths[i]))

def check_grouped_img_dataset(A_paths, B_paths):
    if len(A_paths) == 0:
        raise Exception("Dataset is empty, please check the `dataroot` option.")
    if len(A_paths) != len(B_paths):
        raise ValueError("Different size of A=%d and B=%d " % (len(A_paths), len(B_paths)))
    for i in range(len(A_paths)):
        check_aligned_img_dataset(A_paths[i], B_paths[i])


def download_url(url, out_path):
    with open(out_path, "wb") as f:
        r = requests.get(url, timeout=None, verify=False)
        f.write(r.content)


def read_json_file(file, use_msgpack=False, **open_kwargs):
    with open(file, 'rb' if use_msgpack else 'r', **open_kwargs) as f:
        out = umsgpack.unpack(f) if use_msgpack else json.load(f)
    return out

def write_json_file(file, obj, override=False, use_msgpack=False, min_size=10, encoding='utf-8', **dump_kwargs):
    if os.path.exists(file) and not override:
        raise RuntimeError(f"Try to override file with override={override}.")
    dump_cont = umsgpack.packb(obj) if use_msgpack else json.dumps(obj, **dump_kwargs)
    if len(dump_cont) <= min_size:
        raise RuntimeError(f"Dump object size is smaller than {min_size}, which is not expected.")
    with open(file, 'wb+' if use_msgpack else 'w+', encoding=encoding) as f:
        f.write(dump_cont)


def check_dict_differences(src_dict: dict,
                           ref_dict: dict,
                           exclude_diff: List[str] = None,
                           exclude_keys: List[str] = None) -> None:
    '''
    Check the differences between two dictionaries.

    Args:
        src_dict(dict):          Source dictionary to compare
        ref_dict(dict):          Reference dictionary to compare
        exclude_diff(List[str]): List of differences types to ignore in the checking process
                                 (defaults to None)
        exclude_keys(List[str]): List of keys to exclude from comparison (defaults to None)

    Raises:
        ValueError: If there are differences between the dictionaries that are not excluded
    '''
    if exclude_diff is None:
        exclude_diff = []
    if exclude_keys is None:
        exclude_keys = []

    dict_diff = DeepDiff(src_dict, ref_dict)
    # print(dict_diff.pretty())

    def log_errors(diff_type, diff_data):
        if diff_type in ['dictionary_item_removed', 'dictionary_item_added']:
            return [entity for entity in diff_data if all(ex_key not in entity for ex_key in exclude_keys)]
        else:
            return [f"{name} {entity}" for name, entity in diff_data.items() if all(ex_key not in name for ex_key in exclude_keys)]

    for diff_type, diff_data in dict_diff.items():
        if diff_type in exclude_diff:
            continue
        errors = log_errors(diff_type, diff_data)
        if len(errors) > 0:
            raise ValueError(f'Unexpected {diff_type}: {errors}.')

import iap
import cvglue

A_set = iap.IAPDataset('metadataA.yml')
B_set = iap.IAPDataset('metadataB.yml')
mask_set = iap.IAPDataset('metadata_mask.yml')

def color_calibrator(iap_data, **kwargs):
    base_name = iap_data[1]['name']
    ref_img, _ = A_set.load_data(name=base_name)
    mask, _ = mask_set.load_data(name=base_name)
    mask = (mask-127.)/128.
    mask_bool = mask[...,0] > 0.5
    color_mat = cvglue.color_calibration(iap_data[0][mask_bool].reshape(-1,3), ref_img[mask_bool].reshape(-1,3))
    gt_calib = cvglue.apply_calibration(iap_data[0], color_mat)
    gt_calib = cvglue.apply_mask_merge(gt_calib, ref_img, mask)
    return (gt_calib, iap_data[1])

processors = [iap.func_processor(color_calibrator, {})]
B_set.pipeline('./', processors, meta_file='metadata_calib.yml', img_dir='calib', anno_file='blank.json')


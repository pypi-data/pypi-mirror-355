import cv2
import numpy as np
from skimage import transform as trans

src1 = np.array([[51.642, 50.115], [57.617, 49.990], [35.740, 69.007],
                 [51.157, 89.050], [57.025, 89.702]],
                dtype=np.float32)
#<--left
src2 = np.array([[45.031, 50.118], [65.568, 50.872], [39.677, 68.111],
                 [45.177, 86.190], [64.246, 86.758]],
                dtype=np.float32)

#---frontal
src3 = np.array([[39.730, 51.138], [72.270, 51.138], [56.000, 68.493],
                 [42.463, 87.010], [69.537, 87.010]],
                dtype=np.float32)

#-->right
src4 = np.array([[46.845, 50.872], [67.382, 50.118], [72.737, 68.111],
                 [48.167, 86.758], [67.236, 86.190]],
                dtype=np.float32)

#-->right profile
src5 = np.array([[54.796, 49.990], [60.771, 50.115], [76.673, 69.007],
                 [55.388, 89.702], [61.257, 89.050]],
                dtype=np.float32)

src = np.array([src1, src2, src3, src4, src5])
src_map = {112: src, 224: src * 2}

arcface_src = np.array(
    [[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366],
     [41.5493, 92.3655], [70.7299, 92.2041]],
    dtype=np.float32)

arcface_src = np.expand_dims(arcface_src, axis=0)

# lmk is prediction; src is template
def estimate_norm(lmk, image_size=112, mode='arcface'):
    assert lmk.shape == (5, 2)
    tform = trans.SimilarityTransform()
    lmk_tran = np.insert(lmk, 2, values=np.ones(5), axis=1)
    min_M = []
    min_index = []
    min_error = float('inf')
    if mode == 'arcface':
        assert image_size == 112
        src = arcface_src # * 2
    else:
        src = src_map[image_size]
    for i in np.arange(src.shape[0]):
        tform.estimate(lmk, src[i])
        M = tform.params[0:2, :]
        results = np.dot(M, lmk_tran.T)
        results = results.T
        error = np.sum(np.sqrt(np.sum((results - src[i])**2, axis=1)))
        # print(error)
        if error < min_error:
            min_error = error
            min_M = M
            min_index = i
    return min_M, min_index


def norm_crop(img, keypoints, output_size=None, mode='arcface', **kwargs):
    border_mode = kwargs.get('border_mode', cv2.BORDER_CONSTANT)
    border_value = kwargs.get('border_value', 0)
    no_img = kwargs.get('no_img', False)
    antialias = kwargs.get('antialias', False)
    keypoints = np.reshape(keypoints, [-1,2])
    eye_dist = np.hypot(*(keypoints[1]-keypoints[0]))

    in_size = 112 if mode == 'arcface' else 224
    M, pose_index = estimate_norm(keypoints, in_size, mode)

    std_face = arcface_src[0] if mode == 'arcface' else src_map[224][pose_index]
    std_dist = np.hypot(*(std_face[1]-std_face[0]))
    face_size = 224 * eye_dist / std_dist
    warp_size = int(face_size) if output_size is None or antialias else int(output_size)
    M *= warp_size / in_size

    if no_img:
        crop_img = None
    else:
        crop_img = cv2.warpAffine(img, M, (warp_size, warp_size), flags=cv2.INTER_LINEAR, borderMode=border_mode, borderValue=border_value)
        if antialias:
            crop_img = cv2.resize(crop_img, (output_size, output_size), interpolation=cv2.INTER_AREA)
    if antialias:
        M *= output_size / warp_size
    return crop_img, M



def batch_compute_similarity_transform_torch(S1, S2):
    '''Computes a similarity transform of two points set.

    Args:
        S1: source landmarks, torch tensor, in [N, P, 2]
        S2: reference landmarks, torch tensor, in [N, P, 2]

    Outs:
        S1_hat:     reconstruct S1
        M:          affine matrix
    '''
    assert(S2.shape[1] == S1.shape[1])
    S1 = S1.permute(0,2,1)
    S2 = S2.permute(0,2,1)

    # 1. Remove mean.
    mu1 = S1.mean(axis=-1, keepdims=True)
    mu2 = S2.mean(axis=-1, keepdims=True)
    X1 = S1 - mu1
    X2 = S2 - mu2

    # 2. Compute variance of X1 used for scale.
    var1 = torch.sum(X1**2, dim=1).sum(dim=1)

    # 3. The outer product of X1 and X2.
    K = X1.bmm(X2.permute(0,2,1))

    # 4. Solution that Maximizes trace(R'K) is R=U*V', where U, V are
    # singular vectors of K.
    U, s, V = torch.svd(K)

    # Construct Z that fixes the orientation of R to get det(R)=1.
    Z = torch.eye(U.shape[1], device=S1.device).unsqueeze(0)
    Z = Z.repeat(U.shape[0],1,1)
    Z[:,-1, -1] *= torch.sign(torch.det(U.bmm(V.permute(0,2,1))))

    # Construct R.
    R = V.bmm(Z.bmm(U.permute(0,2,1)))

    # 5. Recover scale.
    scale = torch.cat([torch.trace(x).unsqueeze(0) for x in R.bmm(K)]) / var1

    # 6. Recover translation.
    t = mu2 - (scale.unsqueeze(-1).unsqueeze(-1) * (R.bmm(mu1)))

    # 7. Error:
    S1_hat = scale.unsqueeze(-1).unsqueeze(-1) * R.bmm(S1) + t
    S1_hat = S1_hat.permute(0,2,1)

    M = torch.cat([scale.view([-1, 1, 1]) * R, t], axis=-1)

    return S1_hat, M


# def estimate_norm_torch(lmk, image_size=224):
#     S2 = torch.from_numpy(src_map[224]).cuda()
#     S1_hat_T, M3 = batch_compute_similarity_transform_torch(lmk.unsqueeze(0).repeat_interleave(5, dim=0), S2)
#     error = torch.sum(torch.sqrt(torch.sum((S1_hat_T - S2)**2, axis=2)), axis=1)
#     min_M = M3[error.argmin()].cpu().numpy()
#     dst = warpAffine(input_x, min_M * image_size / 224, output_y.size())

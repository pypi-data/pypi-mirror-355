import cv2
import numpy as np
import torch
from PIL import Image
from matplotlib import pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D
from ..utils import to_image, check_image_format, scale_min_max

# Run following command before using show() when using classic notebook
# %matplotlib notebook 

__all__ = ["img2display", "plot_3d_surfaces", "show"]


def img2display(img, format='CV_BGR', func=None, idx=0):
    auto_scaling = False
    preserve = False
    if func == 'scaling':
        auto_scaling = True
        func = None
    elif func == 'log':
        func = lambda x: np.log1p(np.abs(x))
    elif func is not None:
        preserve = True

    float_out = False
    multi_ch_out = True
    if preserve:
        pass
    elif format == 'CV_BGR':
        img = scale_min_max(img, 0, 255) if auto_scaling else img
        img = check_image_format(img)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    elif format == 'PIL':
        img = scale_min_max(img, 0, 255) if auto_scaling else img
        img = check_image_format(img)
    elif format == 'PATH':
        img = cv2.cvtColor(cv2.imread(img, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGR2RGB)
    elif format == 'TENSOR':
        img = scale_min_max(img, -1, 1) if auto_scaling else img
        img = to_image(img)
        img = img[idx] if isinstance(img, list) else img
    elif format == 'HEATMAP':
        float_out = True
        multi_ch_out = False

    img = func(img) if func else img
    img = check_image_format(img, allow_float=float_out)
    if multi_ch_out and img.shape[2] == 1:
        img = np.repeat(img, 3, axis=-1)
    return img

def show(images, figsize=None, row=0, col=0, format='CV_BGR', func=None, idx=0, colorbar=False, **kwargs):
    """Display interface using matplotlib

    Args:
        images(list/iterable):  list of image array to display
        format(str):            format of image arrays, supporting:
                                - CV_BGR:   OpenCV format BGR numpy array
                                - PIL:      RGB numpy array
                                - PATH:     image path string
                                - TENSOR:   PyTorch tensor, values in [-1, 1]
        figsize(list/tuple):    same with matplotlib
        row(int):               images shows in row x col grid
        col(int):               images shows in row x col grid
        func(callable/str):     custom function to process image, or 'scaling', 'log'
    """
    if len(images) > 100:
        raise ValueError('Display too many images (%d) is significant slow, please check inputs' % len(images))

    figsize = [6*(len(images)+1), 6*(len(images)+1)] if figsize is None else figsize

    plt.figure(figsize=figsize)
    if isinstance(images, (list, tuple, np.ndarray, torch.Tensor)):
        if row != 0:
            col = len(images) // row
        elif col != 0:
            row = len(images) // col
        if row*col != len(images):
            row = 1
            col = len(images)
        for i, img in enumerate(images):
            plt.subplot(row, col, i+1)
            plt.subplots_adjust(hspace=0, wspace=0)
            plt.imshow(img2display(img, format=format, func=func, idx=idx), **kwargs)
            plt.axis('off')
        if colorbar:
            plt.colorbar()
    else:
        raise TypeError("Error input args type: type(images)=%s, expected: images=[img1, img2]" % type(images))


def plot_3d_surfaces(images, names, cmap='rainbow', figsize=[8, 6]):
    '''
    Plot a set of 3D surface plots in a grid using the images provided.

    Args:
        images(list):       list of 2D numpy arrays,
                            each array is a [H, W] grayscale image
        names(list):        list of strings, the title for each plot
        cmap(str):          color map for the surface plot (default "rainbow")
        figsize(list):      list of float values [width, height],
                            specifying the size of the whole figure in inches

    Returns:
        None
    '''
    fig = plt.figure(figsize=figsize)
    num_images = len(images)
    num_rows = np.ceil(np.sqrt(num_images)).astype(int)
    num_cols = np.ceil(num_images / num_rows).astype(int)
    
    for idx, roi_image in enumerate(images):
        xx = np.arange(0, roi_image.shape[1], 1)
        yy = np.arange(0, roi_image.shape[0], 1)
        X, Y = np.meshgrid(xx, yy)
        ax = fig.add_subplot(num_rows, num_cols, idx+1, projection='3d')
        ax.plot_surface(X, Y, roi_image, cmap=cmap)
        ax.set_title(f'{names[idx]}')
    
    plt.tight_layout()
    plt.show()

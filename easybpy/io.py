import os
import bpy
import numpy as np
import warnings

from .external import minexr

def imread(file_path, get_depth=False):
    """a wrapper for bpy to act as skimage.io.imread()

    Notes
    -----
    bpy default ranges from 0 to 1, while converted to 0-255 as skimage performs

    Parameters
    ----------
    file_path : str,
        the full path of image

    Returns
    -------
    out : ndarray of shape (M,N,3) or (M,N,4)
        the numpy ndarray matrix of pixels

    """
    if os.path.exists(file_path):
        ext = os.path.splitext(file_path)[-1]
        if ext in [".JPG", ".jpg", ".JPEG", ".jpeg", ".PNG", ".png"]:
            return _blender_open_common_image(file_path)
        elif ext in [".exr", ".EXR"]:
            exr_data = _minexr_read_exr(file_path)
            if get_depth:
                return exr_data["rgba"], exr_data["depth"]
            else:
                return exr_data["rgba"]
    else:
        raise FileNotFoundError(f"Can not find image [{file_path}]")

def _blender_open_common_image(file_path):
    bpy_img = bpy.data.images.load(file_path, check_existing=True)
    bpy_img_np = (np.array(bpy_img.pixels) * 255).astype(np.uint8)
    img_w = bpy_img.size[0]
    img_h = bpy_img.size[1]
    img_d = int( len(bpy_img.pixels) / (img_w * img_h) )

    bpy_img_np = bpy_img_np.reshape(img_h, img_w, img_d)

    # it seems the blender coordinates zero is (bottom, left)
    # while python skimage / PIL ..., is (top, left)
    # so need flip
    return np.flip(bpy_img_np, axis=0)

def _minexr_read_exr(exr_path):
    # assume exr_already exists
    exr_data = {}
    with open(exr_path, "rb") as fp:
        reader = minexr.load(fp)

        exr_keys = reader.channel_map.keys()
        # read RGBA info
        rgba_key1 = ['Color.R','Color.G','Color.B','Color.A']
        rgba_key2 = ['R', "G", "B", "A"]
        if all(k in exr_keys for k in rgba_key1):
            rgba = reader.select(rgba_key1).copy().astype(np.float32)
        elif all(k in exr_keys for k in rgba_key2):
            rgba = reader.select(rgba_key2).copy().astype(np.float32)
        else:
            raise KeyError(
                f"Could not find RGBA info [Color.R, ..G, ..B, ..A] or [R, G, B, A] in Exr."
                f"keys -> [{exr_keys}]")

        exr_data["rgba"] = (rgba * 255).astype(np.uint8)

        # read depth info
        if "Depth.V" in exr_keys:
            depth = reader.select(["Depth.V"]).copy().squeeze()
        elif "Z" in exr_keys:
            depth = reader.select(["Z"]).copy().squeeze()
        else:
            raise KeyError(
                f"Could not find Depth info [Depth.V] or [Z] in Exr."
                f"keys -> [{exr_keys}]")

        limit_mask = depth < 6e4   # self.LIMIT_DEPTH
        exr_data["depth"] = depth * limit_mask

        return exr_data

def imwrite(img_np, file_path):
    """Save an image to file.

    Parameters
    ----------
    img_np : ndarray of shape (M,N,3) or (M,N,4)
        Image data
    file_path : str 
        Target filename.
    """
    imsave(img_np, file_path)


def imsave(img_np, file_path):
    """Save an image to file.

    Parameters
    ----------
    img_np : ndarray of shape (M,N,3) or (M,N,4)
        Image data
    file_path : str 
        Target filename.
    """
    # the blender coordinates zero is (bottom, left)
    # while python skimage / PIL ..., is (top, left)
    # also, pythonic use pixel 0-255, while blender use 0-1
    flip_img_np = np.flip(img_np, axis=0).astype(np.float16) / 255

    h, w, d = flip_img_np.shape
    if d == 4:
        alpha = True
    elif d == 3:
        alpha = False
    else:
        raise IndexError(f"Only 3 or 4 layer images are supported, not [{d}]")

    path, fname = os.path.split(file_path)
    fname, ext = os.path.splitext(fname)
    if not os.path.exists(path):
        warnings.warn(f"Create non exists folder [{path}]")
        os.makedirs(path)

    out_temp = bpy.data.images.new("easybpy_temp", alpha=alpha, width=w, height=h)

    if alpha:
        out_temp.alpha_mode = "STRAIGHT"

    out_temp.filepath_raw = file_path

    if ext in [".png", ".PNG"]:
        out_temp.file_format = 'PNG'
    elif ext in [".jpg", ".JPG", ".jpeg", ".JPEG"]:
        out_temp.file_format = "JPEG"
    elif ext in [".tif", ".TIF", ".tiff", ".TIFF"]:
         out_temp.file_format = "TIFF"

    out_temp.pixels = flip_img_np.ravel()

    out_temp.save()
    
    bpy.data.images.remove(bpy.data.images["easybpy_temp"], do_unlink=True)

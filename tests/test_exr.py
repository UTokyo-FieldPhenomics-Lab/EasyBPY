import pytest
import easybpy as ebpy

def test_read_exr():
    exr_path = r"tests\data\exr\tmp6pzanz9x.exr"
    rgba, depth = ebpy.io.imread(exr_path, get_depth=True)

    assert rgba.shape == (1080, 1920, 4)
    assert depth.shape == (1080, 1920)
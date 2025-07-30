# import numpy as np
import pyvista as pv
# import pytest
from pyviewfactor import get_visibility
from pyviewfactor import get_obstruction
from pyviewfactor import is_ray_obstructed
from pyviewfactor import batch_ray_obstruction

import numpy as np

# two parallel triangles facing each other
tri1 = pv.Triangle([[0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0]])

tri2 = pv.Triangle([[0.0, 0.0, 1.0],
                    [0.0, 1.0, 1.0],
                    [1.0, 0.0, 1.0]])

triP = pv.Triangle([[0.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0],
                    [1.0, 0.0, 0.0]])

triP.translate([0.0, 0.0, -0.25], inplace=True)

# obstacle blocking in between
obs = pv.Plane(i_size=2, j_size=2, i_resolution=1, j_resolution=1)
obs.translate([0.0, 0.0, 0.5], inplace=True)
obs3 = obs.copy()
obs3.translate([1.7, 0.0, 0.0], inplace=True)

obs_multi = pv.Plane(i_size=2, j_size=2, i_resolution=5, j_resolution=5)
obs_multi.translate([0, 0, 0.5], inplace=True)
obs_multi2 = obs_multi.copy()
obs_multi2.translate([1.7, 0.0, 0.0], inplace=True)

def test_visibility_strict_true():
    vis, warn = get_visibility(tri1, tri2, strict=True)
    assert vis and warn == ""


def test_visibility_not_strict_true():
    vis, warn = get_visibility(tri1, tri2, strict=False)
    assert vis and warn == ""


def test_visibility_strict_false():
    # flip tri2 so normals face away
    tri3 = tri2.copy()
    tri3.flip_faces(inplace=True)
    vis, warn = get_visibility(tri1, tri3, strict=False)
    assert not vis and warn == ""


def test_visibility_strict_false_warn():
    # flip tri2 so normals face away
    tri3 = tri2.copy()
    tri3.flip_faces(inplace=True)
    vis, warn = get_visibility(tri1, tri3, strict=False, print_warning=True)
    assert not vis and warn == ""

def test_visibility_not_strict_false():
    # flip tri2 so normals face away
    tri3 = tri2.copy()
    tri3.flip_faces(inplace=True)
    vis, warn = get_visibility(tri1, tri3, strict=True)
    assert not vis and warn == ""


def test_visibility_partial_strict_true():
    vis, warn = get_visibility(tri1, triP, strict=True)
    assert not vis and "[PVF-Warning-1]" in warn

def test_visibility_partial_strict_true_debug():
    vis, warn = get_visibility(tri1, triP, strict=True, print_warning=True)
    assert not vis and "[PVF-Warning-1]" in warn

def test_visibility_partial_strict_false():
    vis, warn = get_visibility(tri1, triP, strict=False)
    assert vis and "[PVF-Warning-2]" in warn

def test_visibility_partial_strict_false_debug():
    vis, warn = get_visibility(tri1, triP, strict=False, print_warning=True)
    assert vis and "[PVF-Warning-2]" in warn
    
def test_obstruction_strict_true():
    # obstacle sits between tri1 and tri2
    vis, warn = get_obstruction(tri1, tri2, obs, strict=True)
    assert not vis and warn == ""


def test_obstruction_strict_false():
    # obstacle sits between tri1 and tri2
    vis, warn = get_obstruction(tri1, tri2, obs, strict=False)
    assert not vis and warn == ""


def test_partial_obstruction_strict_false():
    vis, warn = get_obstruction(tri1, tri2, obs3, strict=False)
    assert vis and warn == ""


def test_partial_obstruction_strict_true():
    vis, warn = get_obstruction(tri1, tri2, obs3, strict=True)
    assert not vis and "[PVF-Warning-4]" in warn




def test_obstruction_multi_strict_true():
    # obstacle sits between tri1 and tri2
    vis, warn = get_obstruction(tri1, tri2, obs_multi, strict=True)
    assert not vis and warn == ""


def test_obstruction_multi_strict_false():
    # obstacle sits between tri1 and tri2
    vis, warn = get_obstruction(tri1, tri2, obs_multi, strict=False)
    assert not vis and warn == ""


def test_partial_multi_obstruction_strict_false():
    vis, warn = get_obstruction(tri1, tri2, obs_multi2, strict=False)
    assert vis and warn == ""


def test_partial_multi_obstruction_strict_true():
    vis, warn = get_obstruction(tri1, tri2, obs_multi2, strict=True)
    assert not vis and "[PVF-Warning-4]" in warn


def test_batch_ray_obstruction_hits_and_misses():
    tri_arr = np.array([[[0,0,0],[1,0,0],[0,1,0]]], dtype=np.float64)
    # one ray misses, one hits
    starts = np.array([[2,2,1.0],[0.2,0.2,1.0]], dtype=np.float64)
    ends   = np.array([[2,2,-1.0],[0.2,0.2,-1.0]], dtype=np.float64)
    mask = batch_ray_obstruction.py_func(starts, ends, tri_arr)
    assert mask.tolist() == [True, False]
# import numpy as np
import pyvista as pv
# import pytest
import pyviewfactor as pvf

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


# VISIBILITY TESTS


def test_visibility_strict_true():
    vis, warn = pvf.get_visibility(tri1, tri2, strict=True)
    assert vis and warn == ""


def test_visibility_not_strict_true():
    vis, warn = pvf.get_visibility(tri1, tri2, strict=False)
    assert vis and warn == ""


def test_visibility_strict_false():
    # flip tri2 so normals face away
    tri3 = tri2.copy()
    tri3.flip_faces(inplace=True)
    vis, warn = pvf.get_visibility(tri1, tri3, strict=False)
    assert not vis and warn == ""


def test_visibility_strict_false_warn():
    # flip tri2 so normals face away
    tri3 = tri2.copy()
    tri3.flip_faces(inplace=True)
    vis, warn = pvf.get_visibility(tri1, tri3, strict=False, print_warning=True)
    assert not vis and warn == ""


def test_visibility_not_strict_false():
    # flip tri2 so normals face away
    tri3 = tri2.copy()
    tri3.flip_faces(inplace=True)
    vis, warn = pvf.get_visibility(tri1, tri3, strict=True)
    assert not vis and warn == ""


def test_visibility_partial_strict_true():
    vis, warn = pvf.get_visibility(tri1, triP, strict=True)
    assert not vis and "[PVF Visibility]" in warn


def test_visibility_partial_strict_true_debug():
    vis, warn = pvf.get_visibility(tri1, triP, strict=True, print_warning=True)
    assert not vis and "[PVF Visibility]" in warn


def test_visibility_partial_strict_false():
    vis, warn = pvf.get_visibility(tri1, triP, strict=False)
    assert vis and "[PVF Visibility]" in warn


def test_visibility_partial_strict_false_debug():
    vis, warn = pvf.get_visibility(tri1, triP, strict=False, print_warning=True)
    assert vis and "[PVF Visibility]" in warn


# OBSTRUCTION TESTS


def test_obstruction_strict_true():
    # obstacle sits between tri1 and tri2
    vis, warn = pvf.get_obstruction(tri1, tri2, obs, strict=True)
    assert not vis and warn == ""


def test_obstruction_strict_false():
    # obstacle sits between tri1 and tri2
    vis, warn = pvf.get_obstruction(tri1, tri2, obs, strict=False)
    assert not vis and warn == ""


def test_partial_obstruction_strict_false():
    vis, warn = pvf.get_obstruction(tri1, tri2, obs3, strict=False)
    assert vis and warn == ""


def test_partial_obstruction_strict_true():
    vis, warn = pvf.get_obstruction(tri1, tri2, obs3, strict=True)
    assert not vis


def test_obstruction_multi_strict_true():
    # obstacle sits between tri1 and tri2
    vis, warn = pvf.get_obstruction(tri1, tri2, obs_multi, strict=True)
    assert not vis and warn == ""


def test_obstruction_multi_strict_false():
    # obstacle sits between tri1 and tri2
    vis, warn = pvf.get_obstruction(tri1, tri2, obs_multi, strict=False)
    assert not vis and warn == ""


def test_partial_multi_obstruction_strict_false():
    vis, warn = pvf.get_obstruction(tri1, tri2, obs_multi2, strict=False)
    assert vis and warn == ""


def test_partial_multi_obstruction_strict_true():
    vis, warn = pvf.get_obstruction(tri1, tri2, obs_multi2, strict=True)
    assert not vis and "" in warn


def test_batch_ray_obstruction_hits_and_misses():
    tri_arr = np.array([[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0],
                       [0.0, 1.0, 0.0]]], dtype=np.float64)
    # one ray misses, one hits
    starts = np.array([[2.0, 2.0, 1.0], [0.2, 0.2, 1.0]], dtype=np.float64)
    ends = np.array([[2.0, 2.0, -1.0], [0.2, 0.2, -1.0]], dtype=np.float64)
    mask = pvf.ray_intersects_triangle(starts, ends, tri_arr[0], tri_arr[1], tri_arr[2])
    assert mask.tolist() == [True, False]


def test_is_ray_obstructed_hit_and_miss_no_skip():
    # A single triangle at z=0
    blocker = pv.Triangle([[0,0,0],[1,0,0],[0,1,0]])
    # Ray from above → below, passing through (0.2,0.2)
    start = np.array([0.2, 0.2,  1.0])
    end   = np.array([0.2, 0.2, -1.0])
    # Without skip, it must be blocked
    assert pvf.is_ray_blocked(start, end, blocker, eps=1e-6, print_debug=False) is True

    # Ray that misses (offset in x)
    start2 = np.array([2.0, 2.0, 1.0])
    end2   = np.array([2.0, 2.0,-1.0])
    assert pvf.is_ray_blocked(start2, end2, blocker) is False


def test_get_obstruction_non_strict_centroid():
    # Two triangles facing each other at z=±1, no obstacle in between → always visible
    tri1 = pv.Triangle([[0,0,-1],[1,0,-1],[0,1,-1]])
    tri2 = pv.Triangle([[0,0, 1],[1,0, 1],[0,1, 1]])
    # Use an obstacle that is far away (so no intersection)
    far_blocker = pv.Triangle([[10,10,10],[11,10,10],[10,11,10]])
    vis, warn = pvf.get_obstruction(tri1, tri2, far_blocker, strict=False)
    assert vis is True
    assert warn == ""


def test_get_obstruction_non_strict_self_obstacle():
    # If obstacle=face1 itself (triangle), centroid test should skip it and remain visible
    tri1 = pv.Triangle([[0,0,0],[1,0,0],[0,1,0]])
    tri2 = pv.Triangle([[0,0,1],[1,0,1],[0,1,1]])
    # obstacle is exactly tri1: non-strict should skip same‐triangle
    vis, warn = pvf.get_obstruction(tri1, tri2, tri1, strict=False)
    assert vis is True
    assert warn == ""


def test_get_obstruction_strict_full_block():
    # Now obstacle sits exactly between centroids as well as corners
    tri1 = pv.Triangle([[0,0,0],[1,0,0],[0,1,0]])
    tri2 = pv.Triangle([[0,0,1],[1,0,1],[0,1,1]])
    # A square (as two triangles) at z=0.5 that fully covers the XY-span [0,1]
    blocker = pv.Rectangle([[0,0,0.5],[1,0,0.5],[0,1,0.5]])
    blocker.triangulate(inplace=True)
    vis, warn = pvf.get_obstruction(tri1, tri2, blocker, strict=True, print_debug=False)
    assert vis is False
    assert warn == ""
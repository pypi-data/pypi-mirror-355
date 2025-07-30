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


obs4 = obs.copy()
obs4.translate([5.0, 0.0, 0.0], inplace=True)

obs_multi = pv.Plane(i_size=2, j_size=2, i_resolution=5, j_resolution=5)
obs_multi.translate([0, 0, 0.5], inplace=True)
obs_multi2 = obs_multi.copy()
obs_multi2.translate([1.7, 0.0, 0.0], inplace=True)


# VISIBILITY TESTS

def test_visibility_strict_true(capsys):
    vis, warn = pvf.get_visibility(tri1, tri2, strict=True, verbose=True)
    captured = capsys.readouterr()
    msg = "[PVF] [Visibility] Cells are visible"
    assert msg in captured.out 
    assert vis and warn == msg


def test_visibility_strict_false(capsys):
    # flip tri2 so normals face away
    tri3 = tri2.copy()
    tri3.flip_faces(inplace=True)
    msg = "[PVF] [Visibility] Cells are not visible"
    vis, warn = pvf.get_visibility(tri1, tri3, strict=False, verbose=True)
    captured = capsys.readouterr()
    assert not vis and warn == msg
    assert msg in captured.out 


def test_visibility_strict_false1(capsys):
    # flip tri2 so normals face away
    tri3 = tri2.copy()
    tri3.flip_faces(inplace=True)
    msg = "[PVF] [Visibility] Cells are not visible"
    vis, warn = pvf.get_visibility(tri1, tri3, strict=True, verbose=True)
    captured = capsys.readouterr()
    assert not vis and warn == msg
    assert msg in captured.out 


def test_visibility_strict_false_warn2(capsys):
    # flip tri2 so normals face away
    tri3 = tri2.copy()
    tri3.flip_faces(inplace=True)
    vis, warn = pvf.get_visibility(tri1, tri3, strict=True, verbose=True)
    msg = "[PVF] [Visibility] Cells are not visible"
    captured = capsys.readouterr()
    assert not vis and warn == msg
    assert msg in captured.out


def test_visibility_partial_strict_true(capsys):
    vis, warn = pvf.get_visibility(tri1, triP, strict=True, verbose = True)
    msg = "[PVF] [Visibility] strict=True, Cells are considered not visible, but partially are"
    captured = capsys.readouterr()
    assert not vis and msg in warn
    assert msg in captured.out


def test_visibility_partial_strict_false(capsys):
    vis, warn = pvf.get_visibility(tri1, triP, strict=False, verbose = True)
    msg = "[PVF] [Visibility] strict=False, Cells are considered visible, but are only partially"
    captured = capsys.readouterr()
    assert vis and msg in warn
    assert msg in captured.out


def test_get_visibility_from_cache_simple(capsys):
    """
    Test get_visibility_from_cache on two well-separated triangles facing each other.
    """
    # Two triangles facing each other along z
    tri1 = pv.Triangle([[0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0]])
    tri2 = pv.Triangle([[0.0, 0.0, 1.0],
                    [1.0, 0.0, 1.0],
                    [0.0, 1.0, 1.0]])
    mesh = pv.PolyData()
    mesh.points = np.vstack([tri1.points, tri2.points])
    # Add faces (as triangle cells)
    faces = np.array([
        3, 0, 1, 2,  # tri1
        3, 3, 4, 5   # tri2
    ], dtype=np.int32)
    mesh.faces = faces

    cache = pvf.ProcessedGeometry(mesh)

    # Indices: 0 (tri1), 1 (tri2)
    vis, warn = pvf.get_visibility_from_cache(0, 1, cache, strict=False, verbose = True)
    msg = "[PVF] [Visibility] Cells are not visible"
    captured = capsys.readouterr()
    assert not vis
    assert msg in warn
    assert msg in captured.out


def test_get_visibility_from_cache_simple1(capsys):
    """
    Test get_visibility_from_cache on two well-separated triangles facing each other.
    """
    # Two triangles facing each other along z
    tri1 = pv.Triangle([[0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0]])
    tri2 = pv.Triangle([[0.0, 0.0, 1.0],
                    [1.0, 0.0, 1.0],
                    [0.0, 1.0, 1.0]])
    mesh = pv.PolyData()
    mesh.points = np.vstack([tri1.points, tri2.points])
    # Add faces (as triangle cells)
    faces = np.array([
        3, 0, 1, 2,  # tri1
        3, 3, 4, 5   # tri2
    ], dtype=np.int32)
    mesh.faces = faces

    cache = pvf.ProcessedGeometry(mesh)
    # If we flip one triangle, they will not be mutually visible
    # Reverse the normal of tri2 by flipping vertex order
    mesh.points[3:6] = mesh.points[3:6][::-1]
    cache2 = pvf.ProcessedGeometry(mesh)
    vis2, warn2 = pvf.get_visibility_from_cache(0, 1, cache2, strict=False, verbose = True)
    msg = "[PVF] [Visibility] Cells are visible"
    captured = capsys.readouterr()
    assert vis2 == True
    assert  msg in warn2
    assert msg in captured.out


def test_get_visibility_from_cache_partial(capsys):
    """
    Test get_visibility_from_cache on two well-separated triangles facing each other.
    """
    # Two triangles facing each other along z
    tri1 = pv.Triangle([[0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0]])


    triP = pv.Triangle([[0.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0],
                        [1.0, 0.0, 0.0]])
    triP.translate([0.0, 0.0, -0.25], inplace=True)
    mesh = pv.PolyData()
    mesh.points = np.vstack([tri1.points, triP.points])

    faces = np.array([
        3, 0, 1, 2,  # tri1
        3, 3, 4, 5   # tri2
    ], dtype=np.int32)
    mesh.faces = faces

    cache = pvf.ProcessedGeometry(mesh)
    vis, warn = pvf.get_visibility_from_cache(0, 1, cache, strict=False, verbose = True)
    msg = "[PVF] [Visibility] strict=False, Cells are considered visible, but are only partially"
    captured = capsys.readouterr()
    assert vis == True
    assert  msg in warn
    assert msg in captured.out


def test_get_visibility_from_cache_partial1(capsys):
    """
    Test get_visibility_from_cache on two well-separated triangles facing each other.
    """
    # Two triangles facing each other along z
    tri1 = pv.Triangle([[0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0]])


    triP = pv.Triangle([[0.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0],
                        [1.0, 0.0, 0.0]])
    triP.translate([0.0, 0.0, -0.25], inplace=True)
    mesh = pv.PolyData()
    mesh.points = np.vstack([tri1.points, triP.points])

    faces = np.array([
        3, 0, 1, 2,  # tri1
        3, 3, 4, 5   # tri2
    ], dtype=np.int32)
    mesh.faces = faces

    cache = pvf.ProcessedGeometry(mesh)
    vis, warn = pvf.get_visibility_from_cache(0, 1, cache, strict=True, verbose = True)
    msg = "[PVF] [Visibility] strict=True, Cells are considered not visible, but partially are"
    captured = capsys.readouterr()
    assert not vis 
    assert  msg in warn
    assert msg in captured.out



# OBSTRUCTION TESTS


def test_is_ray_obstructed_hit_and_miss_no_skip():
    # A single triangle at z=0
    blocker = np.array([[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0],
                       [0.0, 1.0, 0.0]]], dtype=np.float64)
    # Ray from above → below, passing through (0.2,0.2)
    start = np.array([0.2, 0.2,  1.0])
    end   = np.array([0.2, 0.2, -1.0])
    # Without skip, it must be blocked
    assert pvf.is_ray_blocked.py_func(start, end, blocker, eps=1e-6) is True

    # Ray that misses (offset in x)
    start2 = np.array([2.0, 2.0, 1.0])
    end2   = np.array([2.0, 2.0,-1.0])
    assert pvf.is_ray_blocked.py_func(start2, end2, blocker) is False


def test_batch_ray_obstruction_misses():
    tri_arr = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0],
                       [0.0, 1.0, 0.0]], dtype=np.float64)
    # one ray misses, one hits
    starts = np.array([2.0, 2.0, 1.0], dtype=np.float64)
    ends = np.array([2.0, 2.0, -1.0], dtype=np.float64)
    mask = pvf.ray_intersects_triangle.py_func(starts, ends, tri_arr[0], tri_arr[1], tri_arr[2])
    assert mask == False


def test_batch_ray_obstruction_hit():
    tri_arr = np.array([[0.0, 0.0, 0.0], [10.0, 0.0, 0.0],
                       [0.0, 10.0, 0.0]], dtype=np.float64)
    # one ray misses, one hits
    starts = np.array([2.0, 2.0, 1.0], dtype=np.float64)
    ends = np.array([2.0, 2.0, -1.0], dtype=np.float64)
    mask = pvf.ray_intersects_triangle.py_func(starts, ends, tri_arr[0], tri_arr[1], tri_arr[2])
    assert mask == True



def test_obstruction_strict_true(capsys):
    # obstacle sits between tri1 and tri2
    vis, warn = pvf.get_obstruction(tri1, tri2, obs4, strict=False, verbose=True)
    msg = "[PVF] [Obstruction] Unobstructed (no candidate within c1-c2 AABB)"
    captured = capsys.readouterr()
    assert vis == True
    assert  msg in warn
    assert msg in captured.out



def test_obstruction_strict_false(capsys):
    # obstacle sits between tri1 and tri2
    vis, warn = pvf.get_obstruction(tri1, tri2, obs, strict=False, verbose = True)
    msg = "[PVF] [Obstruction] strict=False, cells obstructed (centroid to centroid)"
    captured = capsys.readouterr()
    assert not vis
    assert  msg in warn
    assert msg in captured.out


def test_partial_obstruction_strict_false(capsys):
    vis, warn = pvf.get_obstruction(tri1, tri2, obs3, strict=False, verbose = True)
    msg = "[PVF] [Obstruction] strict=False, cells not obstructed (centroid to centroid)"
    captured = capsys.readouterr()
    assert vis == True
    assert msg in warn
    assert msg in captured.out


def test_partial_obstruction_strict_true(capsys):
    vis, warn = pvf.get_obstruction(tri1, tri2, obs3, strict=True, verbose = True)
    msg = "[PVF] [Obstruction] strict=True, cells obstructed (at least one vertex to vertex ray)"
    captured = capsys.readouterr()
    assert not vis
    assert msg in warn
    assert msg in captured.out






def test_get_obstruction_from_cache_simple_block(capsys):
    """
    Test get_obstruction_from_cache: triangle faces are blocked by a plane in between.
    """
    # Triangles facing each other
    tri1 = pv.Triangle([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    tri2 = pv.Triangle([[0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [0.0, 1.0, 1.0]])
    mesh = pv.PolyData()
    mesh.points = np.vstack([tri1.points, tri2.points])
    mesh.faces = np.array([3, 0, 1, 2, 3, 3, 4, 5], dtype=np.int32)
    cache = pvf.ProcessedGeometry(mesh)

    # Obstacle: a square at z=0.5
    rect = pv.Rectangle([[10.0, 10.0, 10.0], [11.0, 10.0, 10.0], [11.0, 11.0, 10.0]])
    rect.points = rect.points.astype(np.float64)
    rect.triangulate(inplace=True)
    obs_pre = pvf.FaceMeshPreprocessor(rect)

    # Should be blocked (strict or not)
    vis, warn = pvf.get_obstruction_from_cache(0, 1, cache, obs_pre, strict=False, verbose=True)
    captured = capsys.readouterr()
    msg = "[PVF] [Obstruction] Unobstructed (no candidate within c1-c2 AABB)"
    assert vis is True
    assert msg in warn
    assert msg in captured.out


def test_get_obstruction_from_cache_simple_block2(capsys):
    """
    Test get_obstruction_from_cache: triangle faces are blocked by a plane in between.
    """
    # Triangles facing each other
    tri1 = pv.Triangle([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    tri2 = pv.Triangle([[0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [0.0, 1.0, 1.0]])
    mesh = pv.PolyData()
    mesh.points = np.vstack([tri1.points, tri2.points])
    mesh.faces = np.array([3, 0, 1, 2, 3, 3, 4, 5], dtype=np.int32)
    cache = pvf.ProcessedGeometry(mesh)

    # Obstacle: a square at z=0.5
    rect = pv.Rectangle([[0.0, 0.0, 0.5], [0.0, 10.0, 0.5], [10.0, 10.0, 0.5]])
    rect.points = rect.points.astype(np.float64)
    rect.triangulate(inplace=True)
    obs_pre = pvf.FaceMeshPreprocessor(rect)

    # Should be blocked (strict or not)
    vis, warn = pvf.get_obstruction_from_cache(0, 1, cache, obs_pre, strict=False, verbose=True)
    captured = capsys.readouterr()
    msg = "[PVF] [Obstruction] strict=False, cells obstructed (centroid to centroid)"
    assert vis is False
    assert msg in warn
    assert msg in captured.out


def test_get_obstruction_from_cache_simple_block3(capsys):
    """
    Test get_obstruction_from_cache: triangle faces are blocked by a plane in between.
    """
    # Triangles facing each other
    tri1 = pv.Triangle([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    tri2 = pv.Triangle([[0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [0.0, 1.0, 1.0]])
    mesh = pv.PolyData()
    mesh.points = np.vstack([tri1.points, tri2.points])
    mesh.faces = np.array([3, 0, 1, 2, 3, 3, 4, 5], dtype=np.int32)
    cache = pvf.ProcessedGeometry(mesh)

    # Obstacle: a square at z=0.5
    rect = pv.Rectangle([[0.1, 0.1, 0.1], [0.1, 0.8, 0.1], [0.1, 0.8, 0.8]])
    rect.points = rect.points.astype(np.float64)
    rect.triangulate(inplace=True)
    obs_pre = pvf.FaceMeshPreprocessor(rect)

    # Should be blocked (strict or not)
    vis, warn = pvf.get_obstruction_from_cache(0, 1, cache, obs_pre, strict=False, verbose=True)
    captured = capsys.readouterr()
    msg = "[PVF] [Obstruction] strict=False, cells not obstructed (centroid to centroid)"
    assert vis is True
    assert msg in warn
    assert msg in captured.out



def test_get_obstruction_from_cache_simple_block5(capsys):
    """
    Test get_obstruction_from_cache: triangle faces are blocked by a plane in between.
    """
    # Triangles facing each other
    tri1 = pv.Triangle([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    tri2 = pv.Triangle([[0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [0.0, 1.0, 1.0]])
    mesh = pv.PolyData()
    mesh.points = np.vstack([tri1.points, tri2.points])
    mesh.faces = np.array([3, 0, 1, 2, 3, 3, 4, 5], dtype=np.int32)
    cache = pvf.ProcessedGeometry(mesh)

    # Obstacle: a square at z=0.5
    rect = pv.Rectangle([[0.0, 0.0, 0.5], [0.0, 10.0, 0.5], [10.0, 10.0, 0.5]])
    rect.points = rect.points.astype(np.float64)
    rect.triangulate(inplace=True)
    obs_pre = pvf.FaceMeshPreprocessor(rect)

    # Should be blocked (strict or not)
    vis, warn = pvf.get_obstruction_from_cache(0, 1, cache, obs_pre, strict=True, verbose=True)
    captured = capsys.readouterr()
    msg = "[PVF] [Obstruction] strict=True, cells obstructed (at least one vertex to vertex ray)"
    assert vis is False
    assert msg in warn
    assert msg in captured.out
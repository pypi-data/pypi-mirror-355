"""PVF tests geometrical preprocessfunctions"""

import numpy as np
import pyvista as pv
import pytest
from pyviewfactor import (
    fc_unstruc2poly, face_to_array, face_normal_numpy, polygon_area,
    polygon_centroid, tri_overlaps_aabb, ProcessedGeometry, FaceMeshPreprocessor
)


def test_fc_unstruc2poly_roundtrip():
    sphere = pv.Sphere(radius=0.5)
    ug = sphere.cast_to_unstructured_grid()
    poly = fc_unstruc2poly(ug)
    # Should be PolyData with same number of cells
    assert isinstance(poly, pv.PolyData)
    assert poly.n_cells == ug.n_cells


def test_face_to_array():
    tri1 = pv.Triangle([[0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0]])
    arr = face_to_array(tri1)
    assert arr.shape[1] == 3
    assert arr.shape[0] == tri1.n_points


def test_face_normal_numpy():
    # Standard xy triangle
    tri = np.array([[0,0,0],[1,0,0],[0,1,0]])
    n = face_normal_numpy.py_func(tri)
    np.testing.assert_allclose(n, [0,0,1])
    # Degenerate
    deg = np.array([[0,0,0],[0,0,0],[0,0,0]])
    n2 = face_normal_numpy.py_func(deg)
    np.testing.assert_allclose(n2, [0,0,1])


def test_polygon_area_triangle_and_quad():
    tri = np.array([[0,0,0],[1,0,0],[0,1,0]])
    quad = np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0]])
    assert np.isclose(polygon_area(tri), 0.5)
    assert np.isclose(polygon_area(quad), 1.0)


def test_polygon_centroid_triangle_and_quad():
    tri = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    quad = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0],
                    [1.0, 1.0, 0.0], [0.0, 1.0, 0.0]])
    deg_tri = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
    c_tri = polygon_centroid(tri)
    c_quad = polygon_centroid(quad)
    np.testing.assert_allclose(c_tri, [1/3, 1/3, 0.0])
    np.testing.assert_allclose(c_quad, [0.5, 0.5, 0.0])


def test_tri_overlaps_aabb_basic():
    tri = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    aabb_min = np.array([-0.1, -0.1, -0.1])
    aabb_max = np.array([0.5, 0.5, 0.1])
    assert tri_overlaps_aabb.py_func(tri, aabb_min, aabb_max)
    # No overlap
    aabb_min = np.array([2.0, 2.0, 2.0])
    aabb_max = np.array([3.0, 3.0, 3.0])
    assert not tri_overlaps_aabb(tri, aabb_min, aabb_max)


def test_ProcessedGeometry_methods():
    mesh = pv.Triangle([[0.0, 0.0, 0.0],
                       [1.0, 0.0, 0.0],
                       [0.0, 1.0, 0.0]])
    pg = ProcessedGeometry(mesh)
    assert pg.N == 1
    pts = pg.get_face(0)
    assert pts.shape[1] == 3
    nrm = pg.get_normal(0)
    ctd = pg.get_centroid(0)
    area = pg.get_area(0)
    size = pg.get_size(0)
    assert isinstance(area, float)
    assert isinstance(size, float)
    assert np.linalg.norm(nrm) - 1 < 1e-8


def test_FaceMeshPreprocessor_methods():
    mesh = pv.Plane(i_size=1, j_size=1)
    fmp = FaceMeshPreprocessor(mesh)
    # There should be triangles
    assert fmp.triangles.shape[1:] == (3, 3)
    # aabb_filter should reduce for a small box
    tri = fmp.triangles[0]
    box_min = np.min(tri, axis=0) - 0.01
    box_max = np.max(tri, axis=0) + 0.01
    filtered = fmp.aabb_filter(box_min, box_max)
    assert len(filtered) >= 1
    # exclude_exact_match removes exact matches
    removed = fmp.exclude_exact_match(fmp.triangles[0], fmp.triangles[1], fmp.triangles)
    # Should not include triangle 0 or 1 in result
    for tri_out in removed:
        assert not np.allclose(tri_out, fmp.triangles[0])
        assert not np.allclose(tri_out, fmp.triangles[1])


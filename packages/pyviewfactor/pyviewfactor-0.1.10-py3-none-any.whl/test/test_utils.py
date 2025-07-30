""" PVF tests utility functions"""

import numpy as np
import pyvista as pv
import pytest
import pyviewfactor as pvf


def test_trunc_scalar():
    assert pvf.trunc(1.234567, 2) == pytest.approx(1.23)


def test_trunc_array():
    arr = np.array([1.2345, 2.3456])
    out = pvf.trunc(arr, 3)
    assert np.allclose(out, [1.234, 2.345])


def test_fc_unstruc2poly_roundtrip():
    sphere = pv.Sphere(radius=0.5)
    ug = sphere.cast_to_unstructured_grid()
    poly = pvf.fc_unstruc2poly(ug)
    # Should be PolyData with same number of cells
    assert isinstance(poly, pv.PolyData)
    assert poly.n_cells == ug.n_cells


def test_plotter_runs_and_returns_plotter():
    # Create a minimal mesh with 2 cells
    mesh = pv.PolyData()
    pts = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0],
                   [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    # two triangles sharing a point
    faces = np.hstack([[3, 0, 1, 2], [3, 0, 2, 3]])
    mesh.points = pts
    mesh.faces = faces

    # Dummy VF vector of length n_cells
    vf = np.array([[0.3, 0.7], [0.2, 0.8]])

    # Should not raise and should return a Plotter
    pl = pvf.plot_viewfactor(mesh, vf, cell_id=1, show=False)
    assert isinstance(pl, pv.Plotter)

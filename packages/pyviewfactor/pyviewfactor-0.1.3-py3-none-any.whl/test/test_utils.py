""" PVF tests utility functions"""

import numpy as np
import pyvista as pv
import pytest
from pyviewfactor import trunc, fc_unstruc2poly


def test_trunc_scalar():
    assert trunc(1.234567, 2) == pytest.approx(1.23)


def test_trunc_array():
    arr = np.array([1.2345, 2.3456])
    out = trunc(arr, 3)
    assert np.allclose(out, [1.234, 2.345])


def test_fc_unstruc2poly_roundtrip():
    sphere = pv.Sphere(radius=0.5)
    ug = sphere.cast_to_unstructured_grid()
    poly = fc_unstruc2poly(ug)
    # Should be PolyData with same number of cells
    assert isinstance(poly, pv.PolyData)
    assert poly.n_cells == ug.n_cells

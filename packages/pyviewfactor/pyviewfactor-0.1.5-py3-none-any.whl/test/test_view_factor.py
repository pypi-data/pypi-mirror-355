# import numpy as np
import pyvista as pv
import pytest
from pyviewfactor import compute_viewfactor

# two identical parallel unit squares 1 unit apart → known VF = 1/(π)
pointa = [1.0, 0.0, 0.0]
pointb = [1.0, 1.0, 0.0]
pointc = [0.0, 1.0, 0.0]
rectangle1 = pv.Rectangle([pointa, pointb, pointc])

pointa = [1.0, 0.0, 1.0]
pointb = [1.0, 1.0, 1.0]
pointc = [0.0, 1.0, 1.0]
rectangle2 = pv.Rectangle([pointc, pointb, pointa])


def test_compute_viewfactor_basic():
    vf = compute_viewfactor(rectangle2, rectangle1)
    assert vf == pytest.approx(0.199824, rel=1e-5)


# Ajouter tests pour quand 2 carrés perpendicualires se touchent
# FF = 0.1493 (à confirmer)


# two identical parallel unit squares 1 unit apart → known VF = 1/(π)

# sq1 = pv.Plane(i_size=1, j_size=1, i_resolution=1, j_resolution=1)
# sq2 = sq1.copy()
# sq2.translate([0,0,1], inplace=True)


# def test_reciprocity_property():
    # F = compute_viewfactor_matrix(pv.MultiBlock([sq1, sq2]), n_jobs=1)
    # A1 = sq1.compute_cell_sizes(area=True)['Area'][0]
    # A2 = A1
    # F12 * A1 ≈ F21 * A2
    # assert (F[0,1]*A1) == pytest.approx(F[1,0]*A2)


# def test_matrix_size():
    # mesh = pv.Sphere(theta_resolution=8, phi_resolution=8).triangulate()
    # F = compute_viewfactor_matrix(mesh, n_jobs=1)
    # assert F.shape == (mesh.n_cells, mesh.n_cells)
    # assert np.all(F >= 0) and np.all(F <= 1)

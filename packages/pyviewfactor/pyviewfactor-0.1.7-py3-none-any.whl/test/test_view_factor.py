# import numpy as np
import pyvista as pv
import pytest
import pyviewfactor as pvf
import numpy as np
from pyviewfactor.pyviewfactor import _compute_viewfactor_fixed
from pyviewfactor.pyviewfactor import _integrand_gauss_legendre
from pyviewfactor.pyviewfactor import _integrand_dblquad

def test_integrand_raw_kernel():
    # at (0,0) → log(nqp)*spq
    v = pvf.integrand_dblquad.py_func(0.0,0.0, 2.0,3.0, 0.0,0.0, 5.0, 4.0)
    assert v == pytest.approx(np.log(4.0)*5.0)


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
    vf = pvf.compute_viewfactor(rectangle2, rectangle1)
    assert vf == pytest.approx(0.199824, rel=1e-5)


rect1 = pv.Rectangle([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
rect2 = pv.Rectangle([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 1.0, 1.0]])


def test_compute_viewfactor_common_edge_basic():
    vf = pvf.compute_viewfactor(rect1, rect2, epsilon=0.000001)
    assert vf == pytest.approx(0.20004, rel=1e-4)


def test_closed_geometry_parrallel():
    # create a raw sphere with pyvista
    sphere = pv.Sphere(radius=10, center=(0, 0, 0), direction=(0, 0, 1),
                       theta_resolution=5, phi_resolution=5,
                       start_theta=0, end_theta=360,
                       start_phi=0, end_phi=180)
    # triangulate
    sphere.triangulate(inplace=True)
    # and put the normals inwards please
    sphere.flip_faces(inplace=True)

    # let us chose a cell to compute view factors to
    cell_extracted_id = 2
    # let us chose a cell to compute view factors to
    chosen_face = sphere.extract_cells(cell_extracted_id)
    # convert to PolyData
    chosen_face = pvf.fc_unstruc2poly(chosen_face)
    
    F = pvf.compute_viewfactor_matrix(
        sphere,
        skip_visibility=True,
        skip_obstruction=True,
        compute_kwargs={"epsilon": 1e-4, "rounding_decimal": 8},
        n_jobs=2
    )
    sum_vf = F[:, cell_extracted_id].sum()
    assert sum_vf == pytest.approx(1.0, rel=1e-3)



def test_skip_obstruction_flag_respected():
    # use the same two‐triangle mesh and place an obstacle that blocks only 1→0
    pts = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ], float)
    # triangle 0: pts[0,1,2], triangle 1: pts[0,2,3]
    faces = np.hstack([[3,0,1,2], [3,0,2,3]])
    mesh = pv.PolyData(pts, faces)
    mesh.triangulate(inplace=True)
    tri0 = mesh.extract_cells(0)
    tri1 = mesh.extract_cells(1)
    # obstacle: a small triangle between centroids
    obs = tri0.translate([0.1,0.0,0.3])
    obs = pvf.fc_unstruc2poly(obs)
    # compute with obstruction
    F_blocked = pvf.compute_viewfactor_matrix(
        mesh,
        obstacle=obs,
        skip_visibility=True,
        skip_obstruction=False,
        visibility_kwargs={"strict": True},
        obstruction_kwargs={"strict": True},
        compute_kwargs={"epsilon":1e-6, "rounding_decimal":6},
        n_jobs=1
    )
    # compute with skip_obstruction=True
    F_no_block = pvf.compute_viewfactor_matrix(
        mesh,
        obstacle=obs,
        skip_visibility=True,
        skip_obstruction=True,
        visibility_kwargs={"strict": False},
        obstruction_kwargs={"strict": False},
        compute_kwargs={"epsilon":1e-6, "rounding_decimal":6},
        n_jobs=1
    )
    # now only in the first case do we zero out the blocked direction
    assert F_blocked[0, 1] == pytest.approx(0.0)
    assert F_no_block[0, 1] > 0.0
# tests avec plusieurs cioeurs
#tests avec un full mesh

def test_compute_matrix_against_individual_calls():
    pts = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ], float)
    # triangle 0: pts[0,1,2], triangle 1: pts[0,2,3]
    faces = np.hstack([[3, 0, 1, 2], [3, 0, 2, 3]])
    mesh = pv.PolyData(pts, faces)
    mesh.triangulate(inplace=True)
    from pyviewfactor import compute_viewfactor_matrix
    from pyviewfactor import compute_viewfactor
    from pyviewfactor import fc_unstruc2poly

    F = compute_viewfactor_matrix(
        mesh,
        skip_visibility=True,
        skip_obstruction=True,
        compute_kwargs={'epsilon':1e-6, 'rounding_decimal':6},
        n_jobs=1
    )

    # convert to PolyData
    from pyviewfactor import fc_unstruc2poly
    f0 = fc_unstruc2poly(mesh.extract_cells(0))
    f1 = fc_unstruc2poly(mesh.extract_cells(1))
    direct = compute_viewfactor(f0, f1, epsilon=1e-6, rounding_decimal=6)
    assert F[0, 1] == pytest.approx(direct)


def test_compute_viewfactor_fixed_nonzero_overlap():
    # Two identical triangles, coplanar but offset in x so they partially face each other
    pts1 = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0],[0.0, 1.0, 0.0]], float)
    # shift only in x by 0.5: they “face” each other partially
    pts2 = pts1 + np.array([0.5, 0.0, 1.0])
    pts2 = pts2[::-1]
    constante = 4.0 * np.pi * 0.5
    vf = _compute_viewfactor_fixed.py_func(pts1, pts2, constante)
    # Should be positive but <1
    assert vf > 0.0
    assert vf < 1.0


def test_fast_integrand_zero_when_scal_pq_zero():
    """
    If scal_pq==0, then integrand = log(expr)*0 == 0 everywhere,
    so the fixed‐order quadrature must return exactly 0.
    """
    # pick arbitrary positive parameters for everything else
    nq = 2.3
    np_ = 1.7
    sqpq = -0.5
    sqpp = 0.8
    nqp  = 10.0
    val = _fast_integrand.py_func(nq, np_, sqpq, sqpp, 0.0, nqp)
    assert val == pytest.approx(0.0, abs=0.0)


def test_compute_matrix_len3_visibility_cull():
    # Build two triangles whose normals both point +Z
    tri1 = pv.Triangle([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])   # at z=0
    tri2 = pv.Triangle([[0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [0.0, 1.0, 1.0]])   # at z=1, same orientation

    # Merge them into one mesh
    mesh = tri1.merge(tri2)
    mesh.triangulate(inplace=True)

    # Compute with visibility culling ON (default) and no obstruction cull
    F = pvf.compute_viewfactor_matrix(
        mesh,
        skip_visibility=False,
        skip_obstruction=True,
        n_jobs=1
    )

    # We only have 2 cells
    assert F.shape == (2, 2)

    # Since their normals face the same way, the centroid‐visibility test fails,
    # so _compute_pair returns (i,j,0.0) -> len(res)==3 branch.
    # That sets F[0,1] = 0.0, and F[1,0] is untouched (stays 0.0).
    assert F[0, 1] == pytest.approx(0.0)
    assert F[1, 0] == pytest.approx(0.0)

    # And obviously self‐view is zero
    assert F[0,0] == pytest.approx(0.0)
    assert F[1,1] == pytest.approx(0.0)
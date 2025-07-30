# #######
# Imports
# #######

from numba import njit, prange, set_num_threads
import numpy as np
import pyvista as pv
from joblib import Parallel, delayed
from tqdm import tqdm
from numpy.polynomial.legendre import leggauss
import scipy.integrate
from functools import partial


# #################
# JIT Warmup
# #################

def jit_warmup():
    """
    "Touch" each JIT‐compiled function to compile before real use.

    Calls:
      - _compute_viewfactor_gauss_legendre
      - _integrand_gauss_legendre
      - _integrand_dblquad
      - batch_ray_obstruction  (if defined)
      - _batch_compute_viewfactors
    """
    # Warm up GL integrator
    pts = np.array([[0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0]], dtype=np.float64)
    const_dummy = 4.0 * np.pi * 0.5
    _ = _compute_viewfactor_gauss_legendre(pts, pts + np.array([0, 0, 1.0]), const_dummy)

    # Warm up GL integrand
    _ = _integrand_gauss_legendre(
        1.0,   # norm_q
        1.0,   # norm_p
        0.1,   # scal_qpq
        0.2,   # scal_qpp
        0.3,   # scal_pq
        1.0    # norm_qp
    )

    # Warm up dblquad integrand
    _ = _integrand_dblquad(
        0.5,   # x
        0.5,   # y
        1.0,   # norm_q_carree
        1.0,   # norm_p_carree
        0.1,   # scal_qpq
        0.2,   # scal_qpp
        0.3,   # scal_pq
        1.0    # norm_qp_carree
    )

    # Warm up batch ray obstruction if present
    try:
        tiny_tri = np.array([[[0.0, 0.0, 0.0],
                              [1.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0]]], dtype=np.float64)
        tiny_starts = np.zeros((1, 3), dtype=np.float64)
        tiny_ends   = np.zeros((1, 3), dtype=np.float64)
        tiny_ends[0, 2] = -1.0
        _ = batch_ray_obstruction(tiny_starts, tiny_ends, tiny_tri, eps=1e-6)
    except NameError:
        pass

    # Warm up batch GL
    try:
        dummy_pts1_arr = np.zeros((1, 3, 3), dtype=np.float64)
        dummy_pts2_arr = np.zeros((1, 3, 3), dtype=np.float64)
        dummy_const_arr = np.array([1.0], dtype=np.float64)
        _batch_compute_viewfactors(dummy_pts1_arr, dummy_pts2_arr, dummy_const_arr)
    except NameError:
        pass


# #################
# Utility functions
# #################

# Mesh/Cell conversion
def fc_unstruc2poly(mesh_unstruc):
    """Convenience conversion function from UnstructuredGrid to PolyData

    Parameters
    ----------
    * **mesh_unstruc**: *pyvista.UnstructuredGrid*

        > Unstructured Pyvista Grid.

    Returns
    -------
    * *pyvista.PolyData*

        > The same mesh converted to a surface pyvista.PolyData.

    Examples
    --------
    >>> import pyviewfactor as pvf
    >>> import pyvista as pv
    >>> sphere = pv.Sphere(radius=0.5, center=(0, 0, 0))
    >>> subset = sphere.extract_cells(10)
    >>> subsetPoly = fc_unstruc2poly(subset)
    >>> subsetPoly
    PolyData (0x1fdd9786040)
      N Cells:    1
      N Points:    3
      X Bounds:    -5.551e-17, 3.617e-02
      Y Bounds:    0.000e+00, 4.682e-02
      Z Bounds:    -5.000e-01, -4.971e-01
      N Arrays:    0

    """

    # Get the points and cells
    points = mesh_unstruc.points
    faces = mesh_unstruc.cells
    # Return the same geometry as a pv.PolyData mesh
    return pv.PolyData(points, faces)


# Truncature
def trunc(values, decs=0):
    """
    Truncate numeric values to a fixed number of decimals.

    Parameters
    ----------
    * **values**: *float* or *ndarray*

        > Float or array of floats to truncate.

    * **decs**: *int*, optional

        > Number of decimals to keep (default=0).

    Returns
    -------
    * **float** or **ndarray**

        > Truncated values.

    Examples
    --------
    >>> trunc(1.234567, 2)
    1.23
    >>> import pyvista as pv
    >>> tri = pv.Triangle([[0.111111, 1.111111, 1.111111],
    ...                   [1.222222, 1.222222, 1.222222],
    ...                   [1.333333, 0.333333, 1.333333]])
    >>> trunc(tri.points, 2)
    array([[0.11, 1.11, 1.11],
           [1.22, 1.22, 1.22],
           [1.33, 0.33, 1.33]])
    """
    factor = 10 ** decs
    return np.trunc(values * factor) / factor


def face_normal_numpy(pts: np.ndarray) -> np.ndarray:
    """
    Compute a unit normal for a planar polygon with vertex coords in pts (n×3).

    Even if n>3, any three non‐colinear pts lie in the plane.
    We loop until we find a nonzero cross-product.

    If truly degenerate, fallback to [0,0,1].

    Parameters
    ----------
    pts : ndarray, shape (n,3)
        Planar polygon vertex coordinates.

    Returns
    -------
    ndarray, shape (3,)
        Unit normal vector.
    """
    n = pts.shape[0]
    if n < 3:
        raise ValueError("Need at least 3 vertices to compute a normal.")
    for i in range(1, n - 1):
        e1 = pts[i] - pts[0]
        e2 = pts[i + 1] - pts[0]
        cr = np.cross(e1, e2)
        norm = np.linalg.norm(cr)
        if norm > 1e-12:
            return cr / norm
    raise ValueError("Cell is degenerate")


def polygon_centroid(pts: np.ndarray) -> np.ndarray:
    """
    Compute the area centroid (parametric) of a planar polygon in 3D.

    Uses fan triangulation around pts[0]. If polygon is degenerate,
    returns the arithmetic mean of pts.

    Parameters
    ----------
    pts : ndarray, shape (n,3)
        Ordered vertex coordinates.

    Returns
    -------
    ndarray, shape (3,)
        Area centroid.
    """
    n = pts.shape[0]
    if n < 3:
        raise ValueError("Need at least 3 points to form a polygon.")
    v0 = pts[0]
    total_area = 0.0
    weighted_sum = np.zeros(3, dtype=np.float64)
    for i in range(1, n - 1):
        v1 = pts[i]
        v2 = pts[i + 1]
        e1 = v1 - v0
        e2 = v2 - v0
        cross_prod = np.cross(e1, e2)
        tri_area = 0.5 * np.linalg.norm(cross_prod)
        if tri_area <= 0.0:
            continue
        tri_centroid = (v0 + v1 + v2) / 3.0
        total_area += tri_area
        weighted_sum += tri_area * tri_centroid
    if total_area <= 0.0:
        return pts.mean(axis=0)
    return weighted_sum / total_area
# #########################
# Visibility / Obstrucitons
# #########################

# Visibility
def get_visibility(c1, c2, strict=False, print_warning=False, rounding_decimal=6):
    """
    A test to check if two facets can "see" each other,
    taking the normals into consideration
    (no obstruction tests, only normals orientations).

    Parameters
    ----------
    * **c1**: *pyvista.PolyData*

        > PolyData facet (`pyvista` format).

    * **c2**: *pyvista.PolyData*

        > PolyData facet (`pyvista` format).

    * **strict**: *bool*

        > If **True**, checks all the points are able to see each other
          (considering the face normal) and then continue. If some points are
          "begind the other faces, it will return *False*,

        > If **False** compute the centroids visibility, and might print a warning if
          some points are "behind".

    * **print_warning**: *Bool*

        > If *True*, warning messages will be printed in addition to be returned

    * **rounding_decimal**: *int*

        > Number of decimals at which rounding shall be done for the points
          coordinates. This is to avoid numeric issues when the points
          coordinates are given as for instance 1.234e-13 instead of 0.

    Returns
    -------
    * **bool**

        > True when the facets "see" each other,

        > False else.

    * **str**

        > Warning message if any (empty string if no warning).

    Examples
    --------
    >>> import pyvista as pv
    >>> import pyviewfactor as pvf
    >>> tri1 = pv.Triangle([[0.0, 1.0, 1.0],[1.0, 1.0, 1.0],[1.0, 0.0, 1.0]])
    >>> tri2 = pv.Triangle([[1.0, 0.0, 0.0],[1.0, 1.0, 0.0],[0.0, 1.0, 0.0]])
    >>> pvf.get_visibility(tri1, tri2,strict=False, print_warning=True)
    """
    center1 = c1.cell_centers().points[0]
    center2 = c2.cell_centers().points[0]
    v21 = center1 - center2

    n1 = c1.cell_normals[0]
    n2 = c2.cell_normals[0]

    pos_dot_prod = np.dot(v21, n2)
    neg_dot_prod = np.dot(v21, n1)

    if not (pos_dot_prod > 0 and neg_dot_prod < 0):
        return False, ""

    if strict:
        for cel_i, cel_j in [(c1, c2), (c2, c1)]:
            base_center = cel_j.cell_centers().points[0]
            normal = cel_j.cell_normals[0]
            vectors = np.round(cel_i.points - base_center, rounding_decimal)
            dot_products = np.dot(vectors, normal)
            if np.any(dot_products > 0) and np.any(dot_products < 0):
                warning_str = (
                    "[PVF-Warning-1] strict argument is set to True, "
                    "cells are considered not visible although they partially are"
                )
                if print_warning:
                    print(warning_str)
                return False, warning_str
    else:
        for cel_i, cel_j in [(c1, c2), (c2, c1)]:
            base_center = cel_j.cell_centers().points[0]
            normal = cel_j.cell_normals[0]
            vectors = np.round(cel_i.points - base_center, rounding_decimal)
            dot_products = np.dot(vectors, normal)
            if np.any(dot_products > 0) and np.any(dot_products < 0):
                warning_str = (
                    "[PVF-Warning-2] strict argument is set to False, "
                    "cells are considered visible although they are only partially"
                )
                if print_warning:
                    print(warning_str)
                return True, warning_str

    return True, ""


# Utility function for obstruction tests
@njit
def batch_ray_obstruction(ray_starts, ray_ends, triangles, eps=1e-6):
    """
    Batch-ray intersection test (Möller–Trumbore) for multiple rays.

    Parameters
    ----------
    * **ray_starts**: *ndarray*, shape (nrays,3)

        > Ray origin points.

    * **ray_ends**: *ndarray*, shape (nrays,3)

        > Ray end points.

    * **triangles**: *ndarray*, shape (ntri,3,3)

        > Vertex coords for each triangle.

    * **eps**: *float*, optional

        > *epsilon* to skip near-origin hits (default=1e-6).

    Returns
    -------
    * **mask**: *ndarray* (bool), *shape* (nrays,)

        > **True** if unobstructed,

        > **False** if any intersection.

    Examples
    --------
    >>> starts = np.array([[0,0,0]])
    >>> ends = np.array([[0,0,1]])
    >>> tri = np.array([[[0,0,0.5],[1,0,0.5],[0,1,0.5]]])
    >>> batch_ray_obstruction(starts, ends, tri)
    array([False])
    """
    n_rays = ray_starts.shape[0]
    n_tri = triangles.shape[0]
    mask = np.ones(n_rays, dtype=np.bool_)
    for r in range(n_rays):
        s = ray_starts[r]
        d = ray_ends[r] - s
        L = np.linalg.norm(d)
        for t in range(n_tri):
            v0, v1, v2 = triangles[t]
            e1 = v1 - v0
            e2 = v2 - v0
            h = np.cross(d, e2)
            a = np.dot(e1, h)
            if abs(a) < eps:
                continue
            f = 1.0 / a
            sv = s - v0
            u = f * np.dot(sv, h)
            if u < 0 or u > 1:
                continue
            q = np.cross(sv, e1)
            v = f * np.dot(d, q)
            if v < 0 or u + v > 1:
                continue
            th = f * np.dot(e2, q)
            if eps < th < L - eps:
                mask[r] = False
                break
    return mask


def face_vertex_set(face_poly, decimals=8):
    """
    Build a canonical set of vertex‐tuples for a single‐cell polygon.

    Rounds each vertex coordinate to the given number of decimals,
    then returns a Python set of all (x, y, z) tuples. Works for triangles,
    quads, or any planar polygon.

    Parameters
    ----------
    * **face_poly** : *pyvista.PolyData*

        > PolyData containing exactly one cell (facet). Its `get_cell(0).points`
          are the vertex coordinates of the polygon.

    * **decimals** : *int*, optional

        > Number of decimal places to round each coordinate before building tuples.
          Default is 8.

    Returns
    -------
    * **set** of **tuple**: *(float, float, float)*

        > A set of rounded (x, y, z) coordinates for every vertex in `face_poly`.
    """
    # Get the raw points (n×3) for that one cell
    raw_pts = face_poly.get_cell(0).points.astype(np.float64)  # → shape (n,3)
    raw_pts = np.round(raw_pts, decimals)  # eliminate tiny float noise

    # Convert each row into a Python tuple (x,y,z) and insert into a set
    vert_set = {(raw_pts[i, 0], raw_pts[i, 1], raw_pts[i, 2])
                for i in range(raw_pts.shape[0])}
    return vert_set


# Utility function for obstruction tests
def is_ray_obstructed(start, end, obstacle,
                      eps=1e-6, print_debug=False,
                      skip_vertex_sets=None):
    """
    Determine whether a line‐segment from `start` → `end` intersects any triangle
    in `obstacle`, optionally ignoring triangles whose vertex‐sets lie entirely
    within one of two provided sets.

    Implements the Möller–Trumbore ray‐triangle intersection test in pure Python/NumPy,
    skipping any triangle whose three vertices are all contained in one of the two
    "skip" sets. Returns True as soon as any non‐skipped triangle blocks the ray.

    Parameters
    ----------
    * **start**: *array‐like (3,) float*

        > 3D coordinates of the ray origin (x, y, z).

    * **end**: *array‐like (3,) float*

        > 3D coordinates of the ray endpoint (x, y, z). The ray is the segment from
          `start` to `end`.

    * **obstacle**: *pyvista.PolyData*

        > A (possibly multi‐triangle) mesh to test for intersections.
          Must be all triangles (if not, callers should have called
          `obstacle.triangulate(inplace=True)` first).

    * **eps**: *float*, optional

        > Small tolerance for determinant‐check and ray‐parameter (`t`) comparisons.
          Default is 1e-6.

    * **print_debug**: *bool*, optional

        > If True, prints a message each time it skips a triangle
          (because all of its vertices are in one of the skip sets)
          or each time a non‐skipped triangle intersects the ray.

    * **skip_vertex_sets**: *tuple of two sets or None*

        > If not None, should be `(vs1, vs2)` where each `vsX` is
          a Python set of 3‐tuples `(x,y,z)` for one face’s vertices.
          Any obstacle triangle whose three rounded vertices all lie
          in `vs1` or all lie in `vs2` is skipped (never tested).

    Returns
    -------
    * **bool**

        > **True** if any (non‐skipped) obstacle triangle intersects the open segment
          `(start, end)` (i.e. `t` strictly between `eps` and `||end-start|| - eps`).

        > ** False** otherwise.
    """
    ray_dir = end - start
    ray_length = np.linalg.norm(ray_dir)

    vs1, vs2 = (None, None)
    if skip_vertex_sets is not None:
        vs1, vs2 = skip_vertex_sets

    for idx in range(obstacle.n_cells):
        pts = obstacle.get_cell(idx).points.astype(np.float64)
        pts = np.round(pts, 8)
        tri_set = {(pts[j, 0], pts[j, 1], pts[j, 2]) for j in range(3)}

        # If this tri’s 3 points are all in vs1 or all in vs2, skip it
        if skip_vertex_sets is not None and \
           (tri_set.issubset(vs1) or tri_set.issubset(vs2)):
            if print_debug:
                print(f"Skipping obstacle cell {idx} because all 3" +
                      "vertices lie in a source face.")
            continue

        # …perform Möller–Trumbore intersection test on (pts[0],pts[1],pts[2])…
        v0, v1, v2 = pts[0], pts[1], pts[2]
        edge1 = v1 - v0
        edge2 = v2 - v0
        h = np.cross(ray_dir, edge2)
        a = np.dot(edge1, h)
        if abs(a) < eps:
            continue
        f = 1.0 / a
        s = start - v0
        u = f * np.dot(s, h)
        if u < 0.0 or u > 1.0:
            continue
        q = np.cross(s, edge1)
        v = f * np.dot(ray_dir, q)
        if v < 0.0 or (u + v) > 1.0:
            continue
        t_hit = f * np.dot(edge2, q)
        if t_hit < eps or t_hit > 1.0:
            continue

        # Found a genuine intersection with a "non‐self" triangle
        if print_debug:
            print(f"Obstructed by obstacle cell {idx}, t={t_hit:.6g}")
        return True

    return False


def _tri_overlaps_aabb(tri_pts, aabb_min, aabb_max):
    """
    Return True if the triangle given by tri_pts (shape (3,3)) has any overlap
    with the axis-aligned bounding box [aabb_min, aabb_max].
    aabb_min and aabb_max are both length-3 arrays or sequences.
    """
    tri_min = np.min(tri_pts, axis=0)
    tri_max = np.max(tri_pts, axis=0)
    return (
        (tri_max[0] >= aabb_min[0] and tri_min[0] <= aabb_max[0]) and
        (tri_max[1] >= aabb_min[1] and tri_min[1] <= aabb_max[1]) and
        (tri_max[2] >= aabb_min[2] and tri_min[2] <= aabb_max[2])
    )


def get_obstruction(face1, face2, obstacle, strict=False, print_debug=False):
    """
    Determine if two facets (face1, face2) see each other in free‐space or are
    blocked by an occluder mesh, but only test those obstacle triangles whose
    bounding boxes overlap the AABB of face1∪face2.

    Triangulates `obstacle` internally if needed, then:
      - In *strict mode*: fires one ray per (vertex_i of face1) → (vertex_j of face2),
        but only for obstacle triangles inside the combined AABB.  If all corner‐rays
        pass, returns True. Otherwise, tests the centroid‐to‐centroid ray (again skipping
        any self‐triangles and any obstacles outside the AABB) and, if that ray is unblocked,
        emits a warning but still returns False.
      - In *non‐strict mode*: fires only the centroid→centroid ray (skipping any obstacle
        triangle whose vertices lie entirely in face1 or face2) but only among those triangles
        whose own AABB intersects the face-pair’s AABB.

    Parameters
    ----------
    * **face1** : *pyvista.PolyData*
        > The first single‐cell facet (receiver). Must contain exactly one polygon cell.

    * **face2** : *pyvista.PolyData*
        > The second single‐cell facet (emitter). Must contain exactly one polygon cell.

    * **obstacle** : *pyvista.PolyData*
        > Occluder mesh (can have multiple triangles). Will be triangulated
        > in place if not already all‐triangles.

    * **strict** : *bool*, optional
        > If **True**, performs full vertex‐to‐vertex checks
          (strict partial‐visibility rules).
        > If **False**, only checks centroid→centroid (faster, no partial checks).

    * **print_debug** : *bool*, optional
        > If True, prints messages when skipping “self” triangles,
          obstacle cells outside the AABB, or detecting obstruction.

    Returns
    -------
    * **visible** : *bool*
        > **True** if `face1` and `face2` see each other under the specified mode
          (strict vs. non‐strict).
          False otherwise.

    * **warning_str** : *str*
        > If `strict=True` and some but not all corner‐rays are
          blocked (partial block), returns a warning message:
          `[PVF-Warning-4] strict=True: vertices indicate partial visibility
          but treated as obstructed.`
          In all other cases (fully blocked, fully clear, or non‐strict),
          returns an empty string.
    """
    if not obstacle.is_all_triangles:
        obstacle.triangulate(inplace=True)
    eps = 1e-6
    vs1 = face_vertex_set(face1, decimals=8)
    vs2 = face_vertex_set(face2, decimals=8)
    pts1_all = face1.get_cell(0).points.astype(np.float64)
    pts2_all = face2.get_cell(0).points.astype(np.float64)
    all_pts = np.vstack((pts1_all, pts2_all))
    aabb_min = np.min(all_pts, axis=0)
    aabb_max = np.max(all_pts, axis=0)

    # 5) Now branch on strict vs. non-strict
    if strict:
        tri_list = []
        for i in range(obstacle.n_cells):
            raw_pts = obstacle.get_cell(i).points.astype(np.float64)
            raw_pts = np.round(raw_pts, 8)
            tri_set = {(raw_pts[j, 0], raw_pts[j, 1], raw_pts[j, 2]) for j in range(3)}
            if tri_set.issubset(vs1) or tri_set.issubset(vs2):
                if print_debug:
                    print(f"Skipping obstacle cell {i} as ‘self’ (strict mode).")
                continue
            if not _tri_overlaps_aabb(raw_pts, aabb_min, aabb_max):
                if print_debug:
                    print(f"Skipping obstacle cell {i} (outside AABB).")
                continue
            tri_list.append(raw_pts)
        if len(tri_list) > 0:
            tri_array = np.array(tri_list)
        else:
            tri_array = np.empty((0, 3, 3), dtype=np.float64)
        m = pts1_all.shape[0]
        n = pts2_all.shape[0]
        ray_starts = np.repeat(pts1_all, n, axis=0)
        ray_ends   = np.tile(pts2_all, (m, 1))
        if tri_array.shape[0] > 0:
            mask_hits = batch_ray_obstruction(ray_starts, ray_ends, tri_array, eps=eps)
        else:
            mask_hits = np.ones(m * n, dtype=np.bool_)
        if mask_hits.all():
            return True, ""
        c1 = polygon_centroid(pts1_all)
        c2 = polygon_centroid(pts2_all)
        cent_blocked = is_ray_obstructed(
            c1, c2, obstacle,
            eps=eps, print_debug=print_debug,
            skip_vertex_sets=(vs1, vs2)
        )
        if not cent_blocked:
            warning = "[PVF-Warning-4] strict=True: partial blocked, but centroids clear"
            if print_debug:
                print(warning)
            return False, warning
        return False, ""
    else:
        pts1_vertices = pts1_all
        pts2_vertices = pts2_all
        c1 = polygon_centroid(pts1_vertices)
        c2 = polygon_centroid(pts2_vertices)
        tri_list2 = []
        for i in range(obstacle.n_cells):
            raw_pts = obstacle.get_cell(i).points.astype(np.float64)
            raw_pts = np.round(raw_pts, 8)
            if not _tri_overlaps_aabb(raw_pts, aabb_min, aabb_max):
                continue
            tri_list2.append(raw_pts)
        if len(tri_list2) > 0:
            filt_pts = np.vstack(tri_list2)
            ntri = len(tri_list2)
            cells = []
            for t in range(ntri):
                cells.append(3)
                cells.append(3 * t + 0)
                cells.append(3 * t + 1)
                cells.append(3 * t + 2)
            filt_obs = pv.PolyData(filt_pts, np.array(cells, dtype=np.int64))
            filt_obs.triangulate(inplace=True)
        else:
            return True, ""
        blocked = is_ray_obstructed(
            c1, c2, filt_obs,
            eps=eps, print_debug=print_debug,
            skip_vertex_sets=(vs1, vs2)
        )
        return (not blocked), ""


# ########################
# View Factor Computations
# ########################



@njit
def _integrand_dblquad(x, y, norm_q_carree, norm_p_carree, scal_qpq,
                       scal_qpp, scal_pq, norm_qp_carree):
    """
    Represents the logarithmic integrand of the contour form‐factor integral
    for one edge‐pair between two facets.

    Used internally by `_compute_viewfactor_dblquad`.

    Core integrand function for SciPy dblquad contour integration.

    *Notes* : This function computes
        log(y²·norm_q_carree + x²·norm_p_carree
            − 2·y·scal_qpq + 2·x·scal_qpp − 2·x·y·scal_pq + norm_qp_carree)
        × scal_pq.

    Parameters
    ----------
    * **x**, **y**: *float*

        > Quadrature parameters in [0,1].

    * **norm_q_carree**: *float*

        > Squared length of one directed edge vector (facet1).

    * **norm_p_carree**: *float*

        > Squared length of the other directed edge vector (facet2).

    * **scal_qpq**: *float*

        > Dot(edge1, edge2) term coupling the two edges in the log.

    * **scal_qpp**: *float*

        > Dot(edge2, vector between vertices).

    * **scal_pq**: *float*

        >Dot(edge1, vector between vertices); also multiplies the log.

    * **norm_qp_carree**: *float*

        > Squared length of the inter‐vertex vector.

    Returns
    -------
    * **float**

        > Integrand for `_compute_viewfactor_dblquad()` function
    """
    integrand_function = np.log(y**2 * norm_q_carree
                                + x**2 * norm_p_carree
                                - 2 * y * scal_qpq
                                + 2 * x * scal_qpp
                                - 2 * x * y * scal_pq
                                + norm_qp_carree
                                ) * scal_pq
    return integrand_function



def _compute_viewfactor_dblquad(pts1, pts2, constante):
    """
    Robust fallback integrator using SciPy’s dblquad for contour integration.

    This method loops over every pair of directed edges from two facets
    and evaluates the exact contour integral via `scipy.integrate.dblquad`.

    It is used only in cases of shared edges or vertices.

    *Notes* : If the raw integral comes out negative due to numerical noise,
    it is clamped to zero.

    Parameters
    ----------
    * **pts1**: *ndarray*, shape (n1, 3)

        > Rounded vertex coordinates of the *receiving* facet.
    * **pts2**: *ndarray*, shape (n2, 3)

        > Rounded (and possibly epsilon-shifted) vertex coordinates of the
        *emitting* facet.

    * **constante**: *float*

        > Normalization constant = 4π × area of the emitting facet.

    Returns
    -------
    * **float**

        > The computed view factor from emitting→receiving (non-negative).

    """
    total = 0.0
    n1, n2 = len(pts1), len(pts2)
    v1 = np.roll(pts1, -1, axis=0) - pts1
    v2 = np.roll(pts2, -1, axis=0) - pts2
    norm1 = np.sum(v1 * v1, axis=1)
    norm2 = np.sum(v2 * v2, axis=1)
    scal = v1 @ v2.T

    for i in range(n1):
        nq = norm1[i]
        e1 = v1[i]
        for j in range(n2):
            np_ = norm2[j]
            e2 = v2[j]
            d = pts2[j] - pts1[i]
            nqp = np.dot(d, d)
            sqpq = np.dot(d, e1)
            sqpp = np.dot(d, e2)
            spq = scal[i, j]
            val, _ = scipy.integrate.dblquad(
                _integrand_dblquad,
                0.0, 1.0,
                lambda xx: 0.0, lambda xx: 1.0,
                args=(nq, np_, sqpq, sqpp, spq, nqp)
            )
            total += val
    vf = total / constante
    if vf > 0:
        return vf
    else:
        return 0.0


# Precompute 30×30 nodes & weights once
_GL_ORDER = 30
_nodes, _weights = leggauss(_GL_ORDER)
# map from [-1,1] → [0,1]
_GL_X = 0.5 * (_nodes + 1.0)
_GL_W = 0.5 * _weights



def set_quadrature_order(order: int):
    """
    Change the fixed‐order Gauss–Legendre quadrature rule at runtime.
    Must be called **before** any `compute_viewfactor()` calls.

    The default value before calling this function is `_GL_ORDER=30`.

    If modified during a session, `pvf` needs to be reloaded:
    ```python
    import importlib
    importlib.reload(pvf)
    ```

    Parameters
    ----------
    * **order**: *int*

        > The order of Gauss–Legendre integration

    Returns
    -------
    * *Nothing*

        > Changes internal variables.

    """
    global _GL_ORDER, _GL_X, _GL_W
    from numpy.polynomial.legendre import leggauss
    _GL_ORDER = order
    nodes, weights = leggauss(order)
    _GL_X = 0.5 * (nodes + 1.0)
    _GL_W = 0.5 * weights



@njit
def _integrand_gauss_legendre(norm_q, norm_p, scal_qpq, scal_qpp, scal_pq, norm_qp):
    """
    Fixed‐order Gauss–Legendre quadrature kernel for one edge‐pair.

    Internally used by `_compute_viewfactor_gauss_legendre` to sum
    over a `_GL_ORDER`×`_GL_ORDER` tensor product of nodes/weights on [0,1]×[0,1].

    *Notes*: Uses the precomputed arrays `_GL_X` and `_GL_W` of length `_GL_ORDER`.
    (dafault to `_GL_ORDER=30`).

    Parameters
    ----------
    * **norm_q**: *float*

        > Squared length of the directed edge from the receiving facet.

    * **norm_p**: *float*

        > Squared length of the directed edge from the emitting facet.

    * **scal_qpq**: *float*

        > Dot(edge_q, vector between vertices).

    * **scal_qpp**: *float*

        > Dot(edge_p, vector between vertices).

    * **scal_pq**: *float*

        > Dot(edge_q, edge_p).

    * **norm_qp**: *float*

        > Squared length of the vector between a vertex on facet1
        and a vertex on facet2.

    Returns
    -------
    * **float**

        > Contribution of this edge‐pair to the contour integral,
        > already multiplied by the Gauss–Legendre weights.
    """
    total = 0.0
    for i in range(_GL_ORDER):
        xi = _GL_X[i]
        wi = _GL_W[i]
        for j in range(_GL_ORDER):
            yj = _GL_X[j]
            wj = _GL_W[j]
            expr = (yj * yj * norm_q
                    + xi * xi * norm_p
                    - 2.0 * yj * scal_qpq
                    + 2.0 * xi * scal_qpp
                    - 2.0 * xi * yj * scal_pq
                    + norm_qp)
            if expr > 0.0:
                total += wi * wj * np.log(expr) * scal_pq
    return total



@njit
def _compute_viewfactor_gauss_legendre(pts1, pts2, constante):
    """
    Fast Numba‐JITed contour integrator using fixed‐order Gauss–Legendre.

    This routine evaluates the view‐factor contour integral by looping
    over every pair of directed edges on two convex planar facets,
    approximating the double integral with a 10×10 Gauss–Legendre rule
    (or _GL_ORDER value is modified).

    *Notes*:

    - Precomputed arrays `_GL_X` and `_GL_W` of length `_GL_ORDER` are used.
    - Once jitted, this requires no external dependencies (very fast).
    - See `_integrand_gauss_legendre` for the per‐edge integrand.

    Parameters
    ----------
    * **pts1**: *ndarray*, shape (n1,3)

        > Ordered vertex coordinates of the *receiving* facet.

    * **pts2**: *ndarray*, shape (n2,3)

        > Ordered (and possibly shifted) vertex coordinates of the *emitting* facet.

    * **constante** : *float*

        > Normalization constant = 4π × area of the emitting facet.

    Returns
    -------
    * **float**

        > The view factor F_2→1, clamped to ≥0.
    """
    n1 = pts1.shape[0]
    n2 = pts2.shape[0]
    v1 = np.empty((n1, 3))
    for k in range(n1 - 1):
        v1[k, 0] = pts1[k + 1, 0] - pts1[k, 0]
        v1[k, 1] = pts1[k + 1, 1] - pts1[k, 1]
        v1[k, 2] = pts1[k + 1, 2] - pts1[k, 2]
    # last edge back to first point
    v1[n1 - 1, 0] = pts1[0, 0] - pts1[n1 - 1, 0]
    v1[n1 - 1, 1] = pts1[0, 1] - pts1[n1 - 1, 1]
    v1[n1 - 1, 2] = pts1[0, 2] - pts1[n1 - 1, 2]

    v2 = np.empty((n2, 3))
    for k in range(n2 - 1):
        v2[k, 0] = pts2[k + 1, 0] - pts2[k, 0]
        v2[k, 1] = pts2[k + 1, 1] - pts2[k, 1]
        v2[k, 2] = pts2[k + 1, 2] - pts2[k, 2]
    v2[n2 - 1, 0] = pts2[0, 0] - pts2[n2 - 1, 0]
    v2[n2 - 1, 1] = pts2[0, 1] - pts2[n2 - 1, 1]
    v2[n2 - 1, 2] = pts2[0, 2] - pts2[n2 - 1, 2]
    # precompute norms & dot‐products
    norm1 = np.sum(v1 * v1, axis=1)
    norm2 = np.sum(v2 * v2, axis=1)
    scal = v1 @ v2.T

    total = 0.0
    for i in range(n1):
        nq = norm1[i]
        e1 = v1[i]
        for j in range(n2):
            np_ = norm2[j]
            e2 = v2[j]
            d = pts2[j] - pts1[i]
            nqp = np.dot(d, d)
            sqpq = np.dot(d, e1)
            sqpp = np.dot(d, e2)
            spq = scal[i, j]
            total += _integrand_gauss_legendre(nq, np_, sqpq, sqpp, spq, nqp)
    vf = total / constante
    if vf > 0:
        return vf
    else:
        return 0.0



@njit(parallel=True)
def _batch_compute_viewfactors(
        pts1_arr: np.ndarray,  # shape (Kd, max_v1, 3)
        pts2_arr: np.ndarray,  # shape (Kd, max_v2, 3)
        const_arr: np.ndarray  # shape (Kd,)
    ) -> np.ndarray:
    """
    Numba-parallel core for all “disconnected” pairs.  For each k in prange(0..Kd-1):
        out[k] = _compute_viewfactor_fixed(pts1_arr[k], pts2_arr[k], const_arr[k])
    """
    K = pts1_arr.shape[0]
    out = np.zeros(K, dtype=np.float64)
    for k in prange(K):
        out[k] = _compute_viewfactor_gauss_legendre(pts1_arr[k], pts2_arr[k], const_arr[k])
    return out


def compute_viewfactor(cell1, cell2, *, epsilon=1e-6, rounding_decimal=6):
    """
    Compute the view factor between two planar facets, choosing the best integrator.

    By default, non‐adjacent facets are handled by a fast fixed‐order
    *Gauss–Legendre quadrature* (`_compute_viewfactor_gauss_legendre`), while
    any pair sharing vertices or edges is bumped by `epsilon` and passed to
    the robust *SciPy dblquad integrator* (`_compute_viewfactor_dblquad`).

    Parameters
    ----------
    * **cell1**: *pyvista.PolyData*

        > The *receiving* single‐cell facet.

    * **cell2**: *pyvista.PolyData*

        > The *emitting* single‐cell facet.

    * **epsilon**: *float*, optional

        > Small shift distance along the centroid‐to‐centroid direction
        when facets share any vertex (default=1e-6).

    * **rounding_decimal**: *int*, optional

        > Number of decimals to which vertex coordinates are rounded
        for numeric stability (default=6).

    Returns
    -------
    * **float**

        > The view factor F<sub>2→1</sub>, clamped to ≥0.

    Examples
    --------
    >>> import pyvista as pv
    >>> import pyviewfactor as pvf
    >>> tri1 = pv.Triangle([[0,0,0],[1,0,0],[0,1,0]])
    >>> tri2 = pv.Triangle([[0,0,1],[1,0,1],[0,1,1]])
    >>> vf = pvf.compute_viewfactor(tri1, tri2)
    >>> 0.0 < vf < 1.0
    """
    cells1 = cell1.faces
    n1 = int(cells1[0])
    idxs1 = cells1[1 : 1 + n1]
    pts1 = np.round(cell1.points[idxs1], rounding_decimal)
    cells2 = cell2.faces
    n2 = int(cells2[0])
    idxs2 = cells2[1 : 1 + n2]
    pts2 = np.round(cell2.points[idxs2], rounding_decimal)
    set1 = {tuple(p) for p in pts1}
    set2 = {tuple(p) for p in pts2}
    if set1 & set2:
        c1 = polygon_centroid(pts1)
        c2 = polygon_centroid(pts2)
        direction = c2 - c1
        norm = np.linalg.norm(direction)
        if norm > 0.0:
            direction /= norm
            pts2 = pts2 + epsilon * direction
        use_dblquad = True
    else:
        use_dblquad = False
    area2 = cell2.compute_cell_sizes(area=True)["Area"][0]
    constante = 4.0 * np.pi * area2
    if use_dblquad:
        return _compute_viewfactor_dblquad(pts1, pts2, constante)
    else:
        return _compute_viewfactor_gauss_legendre(pts1, pts2, constante)


# ####################################
# View Factor Full Matrix Computations
# ####################################

# Helper function to compute VF matrix for a complete mesh
def _is_blocked(f_i, f_j, obstacles, obstruction_kwargs, skip_obstruction):
    """
    Check whether any obstacle mesh blocks the view between two facets.

    This helper is called by `compute_viewfactor_matrix()` to apply
    obstruction culling before performing any view‐factor integrations.

    Parameters
    ----------
    * **f_i**, **f_j**: *pyvista.PolyData*

        > Receiving and emitting facets, respectively.

    * **obstacles**: (list of) *pyvista.PolyData*

        > One or more occluder meshes to test.

    * **obstruction_kwargs**: *dict*

        > Keyword args forwarded to `get_obstruction(...)`.

    * **skip_obstruction**: *bool*

        > If **True**, skip all obstruction tests (always returns False).

    Returns
    -------
    * **bool**

        > **True** if any obstacle reports a block
        (i.e., faces do *not* see each other),
        > **False** otherwise.
    """
    if skip_obstruction or not obstacles:
        return False
    for obs in obstacles:
        vis_obs, _ = get_obstruction(f_i, f_j, obs, **(obstruction_kwargs or {}))
        if not vis_obs:
            return True
    return False


def _compute_pair(i, j,
                  faces, areas,
                  obstacles,
                  skip_visibility, skip_obstruction,
                  visibility_kwargs, obstruction_kwargs,
                  epsilon, rounding_decimal,
                  use_reciprocity):
    """
    Compute the view‐factor pair for two facets in a mesh.

    Applies optional visibility and obstruction culling, then computes
    F[i,j] (and F[j,i] via reciprocity or explicit integration).

    Parameters
    ----------
    * **i**, **j**: *int*

        > Indices of the two facets in the `faces` list.

    * **faces**: list of *pyvista.PolyData*

        > All single‐cell facets extracted from the mesh.

    * **areas**: list of *float*

        > Precomputed facet areas, matching `faces`.

    * **obstacles**: list of *pyvista.PolyData*

        > Occluder meshes.

    * **skip_visibility**: *bool*

        > If False, runs `get_visibility` and sets F=0 on fail.

    * **skip_obstruction**: *bool*

        > If False, runs `_is_blocked` and sets F=0 on fail.

    * **visibility_kwargs**: *dict*

        > Forwarded to `get_visibility`.

    * **obstruction_kwargs**: *dict*

        > Forwarded to `get_obstruction`.

    * **epsilon**: *float*

        > Infinitesimal shift for shared‐edge/vertex cases.

    * **rounding_decimal**: *int*

        > Decimal‐rounding for vertex coords.

    * **use_reciprocity**: *bool*

        > If True, uses the relation F[j,i] = (A_i/A_j)*F[i,j]
        otherwise computes both directions.


    Returns
    -------
    * **tuple** of (i, j, F_ij, F_ji)

        > Indices and computed view factors.  If culled by visibility or
        obstruction, returns zeros for both F_ij and F_ji.
    """
    f_i, f_j = faces[i], faces[j]

    # 1) Visibility
    if not skip_visibility:
        vis, _ = get_visibility(f_i, f_j, **visibility_kwargs)
        if not vis:
            return i, j, 0.0, 0.0

    # 2) Obstruction
    if _is_blocked(f_i, f_j, obstacles, obstruction_kwargs, skip_obstruction):
        return i, j, 0.0, 0.0

    # 3) View-factor
    F_ij = compute_viewfactor(f_i, f_j,
                              epsilon=epsilon,
                              rounding_decimal=rounding_decimal)
    if use_reciprocity:
        F_ji = F_ij * (areas[j] / areas[i])
    else:
        F_ji = compute_viewfactor(f_j, f_i,
                                  epsilon=epsilon,
                                  rounding_decimal=rounding_decimal)
    return i, j, F_ij, F_ji


def compute_viewfactor_matrix(
        mesh,
        obstacle=None,
        use_reciprocity=True,
        visibility_kwargs=None,
        obstruction_kwargs=None,
        compute_kwargs=None,
        skip_visibility=False,
        skip_obstruction=False,
        n_jobs=1
    ):
    """
    Compute the full view‐factor matrix for `mesh`.  Each face is a single‐cell
    PolyData.  We:
    
      1) Extract each face and compute its area once.
      2) Build a “vertex set” for each face (rounded to `rounding_decimal`).
      3) Partition all (i<j) into “touching” (share ≥1 vertex) vs. “disconnected”.
      4) For each pair:
         - Perform visibility and obstruction culling (skipped if flags say so).
         - Extract rounded vertex arrays pts1, pts2.
         - If pts1 ∩ pts2 ≠ ∅, shift pts2 by ε along (c2−c1) and call dblquad.
         - Otherwise, call Gauss–Legendre (in batch for disconnected pairs).
      5) Fill F[i,j] and (if use_reciprocity) F[j,i] via area‐ratio.
    
    Parameters
    ----------
    mesh : pyvista.PolyData
        Input mesh. Each mesh cell is a planar facet.
    obstacle : pyvista.PolyData or list[pyvista.PolyData], optional
        Occluder geometry(s). If None, no obstruction test is applied.
    use_reciprocity : bool, default=True
        If True, fill F[j,i] = (areas[i]/areas[j]) * F[i,j] instead of recomputing.
    visibility_kwargs : dict or None
        Passed to get_visibility(f_i, f_j, **visibility_kwargs).
    obstruction_kwargs : dict or None
        Passed to get_obstruction(f_i, f_j, obs, **obstruction_kwargs).
    compute_kwargs : dict or None
        Must contain:
          - "epsilon" (float)
          - "rounding_decimal" (int)
        Used for offset magnitude and rounding of vertex coords.
    skip_visibility : bool, default=False
        If True, skip all visibility tests.
    skip_obstruction : bool, default=False
        If True, skip all obstruction tests.
    n_jobs : int, default=1
        Number of parallel workers for the disconnected (GL) batch.

    Returns
    -------
    F : np.ndarray, shape (N, N)
        Full view‐factor matrix F[i,j] = VF from cell j → cell i.
    """
    # ---------------------------
    # 1) Sanitize inputs & defaults
    # ---------------------------
    visibility_kwargs = visibility_kwargs or {}
    obstruction_kwargs = obstruction_kwargs or {}
    compute_kwargs = compute_kwargs or {}
    epsilon = float(compute_kwargs.get("epsilon", 1e-6))
    rounding_decimal = int(compute_kwargs.get("rounding_decimal", 6))

    # Normalize obstacle(s) into a list
    if obstacle is None:
        obstacles = []
    elif isinstance(obstacle, (list, tuple)):
        obstacles = list(obstacle)
    else:
        obstacles = [obstacle]

    N = mesh.n_cells

    # ---------------------------
    # 2) Extract each face as single‐cell PolyData & compute its area
    # ---------------------------
    faces = []
    areas = np.zeros(N, dtype=np.float64)
    for i in range(N):
        raw = mesh.extract_cells(i)
        face = fc_unstruc2poly(raw)
        faces.append(face)
        areas[i] = float(face.compute_cell_sizes(area=True)["Area"][0])

    # ---------------------------
    # 3) Build a rounded vertex‐set for each face
    # ---------------------------
    face_vertex_sets = [None] * N
    for i in range(N):
        cells_i = faces[i].faces
        n_i = int(cells_i[0])
        idxs_i = cells_i[1 : 1 + n_i]
        pts_i = faces[i].points[idxs_i]
        pts_i_round = np.round(pts_i, rounding_decimal)
        face_vertex_sets[i] = {
            (float(x), float(y), float(z)) for x, y, z in pts_i_round
        }

    # ---------------------------
    # 4) Partition all unique pairs (i < j) into touching vs. disconnected
    # ---------------------------
    touching = []
    disconnected = []
    for i in range(N):
        Si = face_vertex_sets[i]
        for j in range(i + 1, N):
            Sj = face_vertex_sets[j]
            if Si & Sj:
                touching.append((i, j))
            else:
                disconnected.append((i, j))

    # ---------------------------
    # 5) Allocate result arrays
    # ---------------------------
    Ftouch = np.zeros(len(touching), dtype=np.float64)
    Fdisc = np.zeros(len(disconnected), dtype=np.float64)

    # ---------------------------
    # 6) Compute all “touching” pairs (vertex‐shared) via dblquad + ε offset
    # ---------------------------
    print("\n---> Handling connected pairs\n")
    for idx, (i, j) in tqdm(enumerate(touching), desc="> Computing with dblquad", total=len(touching)):
        cell1 = faces[i]
        cell2 = faces[j]
        # 5a) Visibility cull
        if not skip_visibility:
            vis, _ = get_visibility(cell1, cell2, **visibility_kwargs)
            if not vis:
                Ftouch[idx] = 0.0
                continue

        # 5b) Obstruction cull
        if not skip_obstruction and obstacles:
            blocked = False
            for obs in obstacles:
                vis_obs, _ = get_obstruction(cell1, cell2, obs, **obstruction_kwargs)
                if not vis_obs:
                    blocked = True
                    break
            if blocked:
                Ftouch[idx] = 0.0
                continue

        # 5c) Extract & round pts1, pts2
        cells1 = cell1.faces
        n1 = int(cells1[0])
        idxs1 = cells1[1 : 1 + n1]
        pts1 = np.round(cell1.points[idxs1], rounding_decimal)

        cells2 = cell2.faces
        n2 = int(cells2[0])
        idxs2 = cells2[1 : 1 + n2]
        pts2 = np.round(cell2.points[idxs2], rounding_decimal)

        # 5d) Compute centroids via polygon_centroid & offset pts2 by epsilon
        c1 = polygon_centroid(pts1)
        c2 = polygon_centroid(pts2)
        direction = c2 - c1
        norm_dir = np.linalg.norm(direction)
        if norm_dir > 0.0:
            direction /= norm_dir
            pts2 = pts2 + epsilon * direction

        # 5e) Compute normalization constant = 4π·area[j]
        constante = 4.0 * np.pi * areas[j]
    
        # 5f) Compute view factor via dblquad
        Ftouch[idx] = _compute_viewfactor_dblquad(pts1, pts2, constante)

    # ---------------------------
    # 7) Compute all “disconnected” pairs in batch via @njit‐parallel GL
    # ---------------------------
    Kd = len(disconnected)
    Fdisc = np.zeros(Kd, dtype=np.float64)
    print("\n---> Handling disconnected pairs\n")
    if Kd > 0:
        if n_jobs > 1:
            set_num_threads(n_jobs)
        else:
            set_num_threads(1)

        # 6a) Find maximum vertex counts among all disconnected faces
        max_v1 = 0
        max_v2 = 0
        for (i, j) in disconnected:
            v1_pts = faces[i].faces
            m1 = int(v1_pts[0])
            if m1 > max_v1: max_v1 = m1
            v2_pts = faces[j].faces
            m2 = int(v2_pts[0])
            if m2 > max_v2: max_v2 = m2

        pts1_arr  = np.zeros((Kd, max_v1, 3), dtype=np.float64)
        pts2_arr  = np.zeros((Kd, max_v2, 3), dtype=np.float64)
        const_arr = np.zeros(Kd, dtype=np.float64)
        keep_mask = np.ones(Kd, dtype=np.int8)

        # 6b) First pass: fill or mark for dblquad
        print("* Disconnected visbility and obstruction tests")
        for k, (i, j) in enumerate(disconnected):
            cell_i = faces[i]
            cell_j = faces[j]

            # 6b-i) Visibility cull
            if (not skip_visibility):
                vis, _ = get_visibility(cell_i, cell_j, **visibility_kwargs)
                if not vis:
                    keep_mask[k] = 0
                    Fdisc[k] = 0.0
                    continue

            # 6b-ii) Obstruction cull
            if (not skip_obstruction) and obstacles:
                blocked = False
                for obs in obstacles:
                    vis_obs, _ = get_obstruction(cell_i, cell_j, obs, **obstruction_kwargs)
                    if not vis_obs:
                        blocked = True
                        break
                if blocked:
                    keep_mask[k] = 0
                    Fdisc[k] = 0.0
                    continue
            cells_i = cell_i.faces
            n_i = int(cells_i[0])
            idxs_i = cells_i[1 : 1 + n_i]
            pts_i = np.round(cell_i.points[idxs_i], rounding_decimal)

            cells_j = cell_j.faces
            n_j = int(cells_j[0])
            idxs_j = cells_j[1 : 1 + n_j]
            pts_j = np.round(cell_j.points[idxs_j], rounding_decimal)
            
            
            area_j = areas[j]
            if area_j <= 0.0:
                keep_mask[k] = 0
                Fdisc[k] = 0.0
                continue
            
            # 6b‐v) Shared‐vertex test to catch “almost touching” after rounding:
            set_i = {tuple(p) for p in pts_i}
            set_j = {tuple(p) for p in pts_j}
            if set_i & set_j:
                # “touching” or numerically colliding → use dblquad with ε shift
                c_i = polygon_centroid(pts_i)
                c_j = polygon_centroid(pts_j)
                direction = c_j - c_i
                norm_dir = np.linalg.norm(direction)
                if norm_dir > 1e-12:
                    direction /= norm_dir
                    pts_j = pts_j + epsilon * direction
                # else: centroids coincide exactly (rare); still do dblquad
                constante = 4.0 * np.pi * area_j
                Fdisc[k] = _compute_viewfactor_dblquad(pts_i, pts_j, constante)
                keep_mask[k] = 0
                continue
            # else → truly disconnected

            # 6b‐vi) Pack for Gauss–Legendre batch
            m1 = pts_i.shape[0]
            m2 = pts_j.shape[0]
            pts1_arr[k, :m1, :] = pts_i
            pts2_arr[k, :m2, :] = pts_j
            const_arr[k] = 4.0 * np.pi * area_j
            # leave keep_mask[k] == 1, so that GL will calculate it

        print("* Computation")
        if n_jobs > 1:
            print("   * Using numba {} threads".format(n_jobs))
            Fvals = _batch_compute_viewfactors(pts1_arr, pts2_arr, const_arr)
            Fvals[keep_mask == 0] = 0.0
            Fdisc[:] = Fdisc + Fvals
        else:
            print("   * Using numba in sequential".format(n_jobs))
            for k in tqdm(range(Kd), desc="Computing disconnected pairs (one thread)"):
                if keep_mask[k]:
                    Fdisc[k] = _compute_viewfactor_gauss_legendre(
                        pts1_arr[k], pts2_arr[k], const_arr[k]
                    )
    else:
        Fdisc = np.zeros(0, dtype=np.float64)

    # ---------------------------
    # 8) Assemble the full NxN matrix with reciprocity
    # ---------------------------
    F = np.zeros((N, N), dtype=np.float64)

    # 8a) Fill “touching” results
    for idx, (i, j) in enumerate(touching):
        fij = Ftouch[idx]
        F[i, j] = fij
        if use_reciprocity:
            F[j, i] = fij * (areas[i] / areas[j])

    # 8b) Fill “disconnected” results
    for k, (i, j) in enumerate(disconnected):
        fij = Fdisc[k]
        F[i, j] = fij
        if use_reciprocity:
            F[j, i] = fij * (areas[i] / areas[j])

    return F


# Helper function to plot a mesh with view factor from one of the cells
# to all others.
def plot_viewfactor(mesh: pv.PolyData,
                    F: np.ndarray,
                    cell_id: int,
                    cmap: str = "viridis",
                    show: bool = True) -> pv.Plotter:
    """
    Render a mesh colored by the view‐factor distribution from one source cell.

    This helper attaches the row F[cell_id, :] as a new cell‐array
    `'ViewFactor'` and displays it via PyVista.

    Parameters
    ----------
    * **mesh**: *pyvista.PolyData*

        > Closed or open mesh whose cells correspond to both rows and columns of **F**.

    * **F**: *ndarray*, shape (n_cells, n_cells)

        > Precomputed view‐factor matrix.

    * **cell_id**: *int*

        > Index of the source cell whose F → others will be plotted.

    * **cmap** : *str*, optional

        > Name of a Matplotlib colormap (default=`"viridis"`).

    * **show**: *bool*, optional

        > If **True**, calls `pl.show()` before returning.
        If **False**, returns the `Plotter` for further customization.

    Returns
    -------
    * **pv.Plotter**
        The PyVista Plotter instance with the view‐factor plot.

    Raises
    ------
    * **ValueError**
        If `F.shape != (mesh.n_cells, mesh.n_cells)`.

    Examples
    --------
    >>> import pyvista as pv
    >>> import numpy as np
    >>> import pyviewfactor as pvf
    >>> sphere = pv.Sphere().triangulate()
    >>> F = np.random.rand(sphere.n_cells, sphere.n_cells)
    >>> pl = pvf.plot_viewfactor(sphere, F, cell_id=0, show=False)
    >>> pl.add_title("View factors from cell 0")
    >>> pl.show()
    """
    n = mesh.n_cells
    if F.shape != (n, n):
        raise ValueError(f"Expected F shape {(n,n)}, got {F.shape}")

    # Make a copy so we don’t overwrite the original cell_data
    mesh_pf = mesh.copy()
    mesh_pf.cell_data["ViewFactor"] = F[cell_id, :]

    pl = pv.Plotter()
    pl.add_mesh(
        mesh_pf,
        scalars="ViewFactor",
        cmap=cmap,
        show_edges=False,
        scalar_bar_args={"title": f"F from cell {cell_id}"}
    )
    pl.add_title(f"View Factors from cell {cell_id}")

    if show:
        pl.show()
    return pl


""" ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ End Of File ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ """

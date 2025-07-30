# ###########
# Lib imports
# ###########
from numba import njit
from numba import prange
from numba import set_num_threads
import pyvista as pv
import numpy as np
from numpy.polynomial.legendre import leggauss
import scipy.integrate
from functools import partial
from tqdm import tqdm


# ##########
# JIT Warmup


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



def polygon_centroid(pts: np.ndarray) -> np.ndarray:
    """
    Compute the area centroid ( area-weighted centroid) of a planar polygon in 3D.

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
    p0, p1, p2 = pts[0], pts[1], pts[2]
    v1 = p1 - p0
    v2 = p2 - p0
    normal = np.cross(v1, v2)
    normal /= np.linalg.norm(normal)
    u = v1 / np.linalg.norm(v1)
    w = np.cross(normal, u)
    proj = np.array([[np.dot(p - p0, u), np.dot(p - p0, w)] for p in pts])
    A = 0.0
    Cx = 0.0
    Cy = 0.0
    N = proj.shape[0]
    for i in range(N):
        x0, y0 = proj[i]
        x1, y1 = proj[(i + 1) % N]
        cross = x0 * y1 - x1 * y0
        A += cross
        Cx += (x0 + x1) * cross
        Cy += (y0 + y1) * cross
    A *= 0.5
    if np.abs(A) < 1e-12:
        return np.mean(pts, axis=0)
    centroid_2D = np.array([Cx / (6 * A), Cy / (6 * A)])
    return p0 + centroid_2D[0] * u + centroid_2D[1] * w


# #########################
# Visibility / Obstrucitons
# #########################

def get_visibility(cell1, cell2, strict=False, print_warning=False, rounding_decimal=6):
    """
    Visibility test between two planar faces.

    Parameters
    ----------
    cell1, cell2 : pyvista.PolyData
        Two single-cell planar faces.
    strict : bool
        If True, performs a full vertex‐to‐vertex check and rejects on any partial occlusion.
    print_warning : bool
        If True, prints a warning when partial visibility is detected (strict or non-strict).
    rounding_decimal : int
        Number of decimal places for intermediate rounding.

    Returns
    -------
    visible : bool
    warning : str
    """
    import numpy as np

    # --- extract and round points ---
    def _pts(cell):
        f = cell.faces
        n = int(f[0])
        idx = f[1:1+n]
        return np.round(cell.points[idx], rounding_decimal)

    pts1 = _pts(cell1)
    pts2 = _pts(cell2)

    # --- compute normals ---
    def _norm(pts):
        v = np.cross(pts[1] - pts[0], pts[2] - pts[0])
        return v / np.linalg.norm(v)

    norm1 = _norm(pts1)
    norm2 = _norm(pts2)

    # --- compute centroids ---
    c1 = polygon_centroid(pts1)
    c2 = polygon_centroid(pts2)

    # --- quick centroid front/back check ---
    v21  = c1 - c2
    if not (np.dot(v21, norm2) > 0 and np.dot(v21, norm1) < 0):
        return False, ""

    # --- strict mode: full vertex‐to‐vertex test ---
    if strict:
        for (ptsA, cB, nB) in [(pts1, c2, norm2), (pts2, c1, norm1)]:
            dots = np.dot(ptsA - cB, nB)
            # partial if some points are on both sides of the plane
            if np.min(dots) < 0 < np.max(dots):
                warning = "[PVF-Warning] strict=True: partial occlusion → rejected"
                if print_warning:
                    print(warning)
                return False, warning
        return True, ""

    # --- non‐strict mode: shortcut if warnings off ---
    if not print_warning:
        return True, ""

    # --- non‐strict + warnings: check and accept with warning ---
    for (ptsA, cB, nB) in [(pts1, c2, norm2), (pts2, c1, norm1)]:
        dots = np.dot(ptsA - cB, nB)
        if np.min(dots) < 0 < np.max(dots):
            warning = "[PVF-Warning] strict=False: partial occlusion → accepted"
            print(warning)
            return True, warning

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

    # 1) build vertex‐sets to skip “self” triangles
    vs1 = face_vertex_set(face1, decimals=8)
    vs2 = face_vertex_set(face2, decimals=8)

    # 2) get corner points & combined AABB
    pts1 = face1.get_cell(0).points.astype(np.float64)
    pts2 = face2.get_cell(0).points.astype(np.float64)
    all_pts = np.vstack((pts1, pts2))
    aabb_min, aabb_max = all_pts.min(axis=0), all_pts.max(axis=0)

    # 3) collect only relevant obstacle triangles
    tri_list = []
    for i in range(obstacle.n_cells):
        tri = obstacle.get_cell(i).points.astype(np.float64)
        tri = np.round(tri, 8)
        tri_set = {(p[0], p[1], p[2]) for p in tri}

        # skip if triangle is part of face1 or face2
        if tri_set.issubset(vs1) or tri_set.issubset(vs2):
            if print_debug:
                print(f"[DEBUG] Skipping self‐triangle {i}")
            continue

        # skip if no AABB overlap
        if not _tri_overlaps_aabb(tri, aabb_min, aabb_max):
            if print_debug:
                print(f"[DEBUG] Skipping triangle {i} (outside AABB)")
            continue

        tri_list.append(tri)

    tri_array = np.array(tri_list) if tri_list else np.empty((0,3,3), dtype=np.float64)

    # 4) build all vertex→vertex rays
    m, n = pts1.shape[0], pts2.shape[0]
    ray_starts = np.repeat(pts1, n, axis=0)
    ray_ends   = np.tile(pts2, (m, 1))

    # 5) trace rays against tri_array
    if tri_array.size > 0:
        blocked_mask = batch_ray_obstruction(ray_starts, ray_ends, tri_array, eps=eps)
    else:
        blocked_mask = np.zeros(ray_starts.shape[0], dtype=bool)

    if print_debug:
        total   = blocked_mask.size
        blocked = blocked_mask.sum()
        clear   = total - blocked
        print(f"[DEBUG] rays → total={total}, blocked={blocked}, clear={clear}")

    all_clear   = (~blocked_mask).all()
    all_blocked = blocked_mask.all()
    mixed       = not (all_clear or all_blocked)

    # 6) decide based on strict flag
    if strict:
        # strict: only all‐clear passes
        return (all_clear, "")

    # non‐strict:
    if all_clear:
        return True, ""
    if mixed:
        warning = "[PVF-Warning-4] strict=False: partial‐block but treated as visible"
        if print_debug:
            print(f"[DEBUG] {warning}")
        return True, warning

    # all_blocked
    return False, ""

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



""" ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ End Of File ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ """

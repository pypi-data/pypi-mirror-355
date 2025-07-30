""" PVF main functions"""


# Imports
from numba import njit
import numpy as np
import pyvista as pv
from joblib import Parallel, delayed
from tqdm import tqdm
from numpy.polynomial.legendre import leggauss
import scipy.integrate
from functools import partial


class FaceCache:
    """
    A lightweight structure to cache face geometry (points, normals, centroids, area)
    for high-performance view factor computation.
    """
    def __init__(self, mesh, rounding_decimal=6):
        self.rounding_decimal = rounding_decimal
        self.N = mesh.n_cells
        self.points = []
        self.normals = np.zeros((self.N, 3), dtype=np.float64)
        self.centroids = np.zeros((self.N, 3), dtype=np.float64)
        self.areas = np.zeros(self.N, dtype=np.float64)

        for i in range(self.N):
            raw = mesh.extract_cells(i)
            face = fc_unstruc2poly(raw)
            faces_i = face.faces
            n_i = int(faces_i[0])
            idxs = faces_i[1:1 + n_i]
            pts = np.round(face.points[idxs], rounding_decimal)

            self.points.append(pts)
            self.centroids[i] = polygon_centroid(pts)

            v1 = pts[1] - pts[0]
            v2 = pts[2] - pts[0]
            norm = np.cross(v1, v2)
            self.normals[i] = norm / np.linalg.norm(norm)

            self.areas[i] = 0.5 * np.linalg.norm(np.cross(pts[1] - pts[0], pts[2] - pts[0])) if pts.shape[0] == 3 else polygon_area(np.round(face.points, rounding_decimal))

    def get_face(self, i):
        return self.points[i]

    def get_normal(self, i):
        return self.normals[i]

    def get_centroid(self, i):
        return self.centroids[i]

    def get_area(self, i):
        return self.areas[i]




class FaceMeshPreprocessor:
    def __init__(self, mesh: pv.PolyData):
        if not mesh.is_all_triangles:
            mesh = mesh.triangulate()
        self.points = mesh.points.astype(np.float64)
        # cells array is [n, i0, i1, i2, n, ...]
        cells = mesh.faces.reshape(-1,4)[:,1:]
        self.faces = cells  # shape (n_cells,3)
        self.triangles = np.array([self.points[c] for c in cells], dtype=np.float64)

    def aabb_filter(self, aabb_min, aabb_max):
        kept = []
        for tri in self.triangles:  # tri.shape == (3,3)
            if tri_overlaps_aabb(tri, aabb_min, aabb_max):
                kept.append(tri)
        return np.array(kept, dtype=np.float64)

    def exclude_exact_match(self, pts1, pts2, tris):
        # build frozensets of each vertex array
        vs1 = frozenset(sorted(tuple(np.round(p,8)) for p in pts1))
        vs2 = frozenset(sorted(tuple(np.round(p,8)) for p in pts2))
        out = []
        for tri in tris:
            tri_set = frozenset(sorted(tuple(np.round(p,8)) for p in tri))
            if not tri_set.isdisjoint(vs1) or not tri_set.isdisjoint(vs2):
                continue
            out.append(tri)
        return np.array(out, dtype=np.float64)

def face_to_array(face):
    """Convert a single-cell PolyData face to an (n,3) ndarray."""
    return face.get_cell(0).points.astype(np.float64)


def polygon_area(pts):
    # Compute normal
    n = face_normal_numpy(pts)
    # Use polygon centroid and cross product trick
    area = 0.0
    n_pts = pts.shape[0]
    for i in range(n_pts):
        v0 = pts[i]
        v1 = pts[(i + 1) % n_pts]
        area += np.dot(n, np.cross(v0, v1))
    return 0.5 * np.abs(area)


@njit
def face_normal_numpy(pts):
    """
    Compute a unit normal for a planar polygon with vertex coords in pts (n×3).
    Returns the *right-handed* normal. Handles n > 3.
    If degenerate, returns [0,0,1].
    """
    n = pts.shape[0]
    if n < 3:
        return np.array([0.0, 0.0, 1.0])
    # Newell's method (robust for convex planar polygons)
    nx = 0.0
    ny = 0.0
    nz = 0.0
    for i in range(n):
        j = (i + 1) % n
        nx += (pts[i,1] - pts[j,1]) * (pts[i,2] + pts[j,2])
        ny += (pts[i,2] - pts[j,2]) * (pts[i,0] + pts[j,0])
        nz += (pts[i,0] - pts[j,0]) * (pts[i,1] + pts[j,1])
    norm = np.sqrt(nx*nx + ny*ny + nz*nz)
    if norm < 1e-12:
        return np.array([0.0, 0.0, 1.0])
    return np.array([nx, ny, nz]) / norm


@njit
def tri_overlaps_aabb(tri_pts, aabb_min, aabb_max):
    """
    JIT‐compatible AABB overlap test without using axis keywords.
    """
    # initialize with the first vertex
    tri_min0 = tri_pts[0, 0]
    tri_min1 = tri_pts[0, 1]
    tri_min2 = tri_pts[0, 2]
    tri_max0 = tri_min0
    tri_max1 = tri_min1
    tri_max2 = tri_min2

    # find true min/max over the three vertices
    for i in range(1, tri_pts.shape[0]):
        x, y, z = tri_pts[i, 0], tri_pts[i, 1], tri_pts[i, 2]
        if x < tri_min0: tri_min0 = x
        if y < tri_min1: tri_min1 = y
        if z < tri_min2: tri_min2 = z
        if x > tri_max0: tri_max0 = x
        if y > tri_max1: tri_max1 = y
        if z > tri_max2: tri_max2 = z

    # now test overlap
    return (
        (tri_max0 >= aabb_min[0]) and (tri_min0 <= aabb_max[0]) and
        (tri_max1 >= aabb_min[1]) and (tri_min1 <= aabb_max[1]) and
        (tri_max2 >= aabb_min[2]) and (tri_min2 <= aabb_max[2])
    )



def face_vertex_set(face_poly, decimals=8):
    """
    Return a set of sorted rounded (x, y, z) vertex tuples from a face.
    Sorting ensures symmetry regardless of vertex order.
    """
    raw_pts = face_poly.get_cell(0).points.astype(np.float64)
    raw_pts = np.round(raw_pts, decimals)
    vert_list = [tuple(p) for p in raw_pts]
    vert_set = frozenset(sorted(vert_list))
    return vert_set


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




@njit
def ray_intersects_triangle(orig, dest, v0, v1, v2, eps=1e-6):
    # 0) If origin or dest coincides with a vertex, skip this triangle
    #    (treat as no intersection)
    #    Use squared tolerance to avoid sqrt
    if ((orig[0]-v0[0])**2 + (orig[1]-v0[1])**2 + (orig[2]-v0[2])**2) < eps**2:
        return False
    if ((orig[0]-v1[0])**2 + (orig[1]-v1[1])**2 + (orig[2]-v1[2])**2) < eps**2:
        return False
    if ((orig[0]-v2[0])**2 + (orig[1]-v2[1])**2 + (orig[2]-v2[2])**2) < eps**2:
        return False
    d = dest - orig
    L = np.linalg.norm(d)
    if L < eps: 
        return False
    edge1 = v1 - v0
    edge2 = v2 - v0
    h = np.cross(d, edge2)
    a = np.dot(edge1, h)
    if abs(a) < eps:
        return False
    f = 1.0 / a
    s = orig - v0
    u = f * np.dot(s, h)
    if u < 0 or u > 1:
        return False
    q = np.cross(s, edge1)
    v = f * np.dot(d, q)
    if v < 0 or u+v > 1:
        return False
    t = f * np.dot(edge2, q)
    return (eps < t) and (t < L - eps)


@njit
def is_ray_blocked(start, end, triangles, eps=1e-6):
    for tri in triangles:
        if ray_intersects_triangle(start, end,
                                   tri[0], tri[1], tri[2],
                                   eps):
            return True
    return False

## Encore un soucis avec les tests strict
def get_obstruction(
        cell1, cell2, obstacle,
        strict=False,
        print_warning=False,
        eps=1e-6
    ):
    """
    Test obstruction between two facets (which can be either PyVista PolyData
    or raw (n,3) arrays) and an obstacle (either PolyData or FaceMeshPreprocessor).
    """
    # 1) Convert inputs to numpy arrays
    if isinstance(cell1, pv.PolyData):
        pts1 = face_to_array(cell1)
    else:
        pts1 = np.asarray(cell1, dtype=np.float64)

    if isinstance(cell2, pv.PolyData):
        pts2 = face_to_array(cell2)
    else:
        pts2 = np.asarray(cell2, dtype=np.float64)

    # 2) Prepare obstacle triangles
    if isinstance(obstacle, FaceMeshPreprocessor):
        pre = obstacle
    else:
        pre = FaceMeshPreprocessor(obstacle)
    # 3) AABB cull
    # 2) Build combined AABB & cull triangles
    # 3) AABB cull
    all_pts = np.vstack((pts1, pts2))
    amin, amax = all_pts.min(axis=0), all_pts.max(axis=0)
    cand = pre.aabb_filter(amin, amax)
    
    # 4) Exclude self‐triangles
    cand = pre.exclude_exact_match(pts1, pts2, cand)
    if cand.size == 0:
        return True, "fully visible"

    # 5) non‐strict: centroid ray
    if not strict:
        c1 = polygon_centroid(pts1)
        c2 = polygon_centroid(pts2)
        if is_ray_blocked(c1, c2, cand, eps=eps):
            return False, ""
        return True, ("partially visible" if print_warning else "")

    # 6) strict: every vertex‐to‐vertex
    for p1 in pts1:
        for p2 in pts2:
            if is_ray_blocked(p1, p2, cand, eps=eps):
                return False, ""
    return True, ""


# #################
# Utility functions
# #################

# Mesh/Cell conversion
def fc_unstruc2poly(mesh_unstruc):
    """Convenience conversion function from UnstructuredGrid to PolyData

    Parameters
    ----------
    * **mesh_unstruc** : *pyvista.UnstructuredGrid*

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
    values : float or ndarray
        Float or array of floats to truncate.
    decs : int, optional
        Number of decimals to keep (default=0).

    Returns
    -------
    float or ndarray
        Truncated values.

    Examples
    --------
    >>> trunc(1.234567, 2)
    1.23
    >>> import pyvista as pv
    >>> tri = pv.Triangle([[0.111111, 1.111111, 1.111111],
    ...                  [1.222222, 1.222222, 1.222222],
    ...                  [1.333333, 0.333333, 1.333333]])
    >>> trunc(tri.points, 2)
    array([[0.11, 1.11, 1.11],
           [1.22, 1.22, 1.22],
           [1.33, 0.33, 1.33]])
    """
    factor = 10 ** decs
    return np.trunc(values * factor) / factor


# #########################
# Visibility / Obstrucitons
# #########################

# Visibility
def get_visibility(c1, c2, strict=False, print_warning=False, rounding_decimal=6):
    """Facets visibility:

    A test to check if two facets can "see" each other, taking the normals
    into consideration (no obstruction tests, only normals orientations).

    Parameters
    ----------
    * **c1** : *pyvista.PolyData*

        > PolyData facet (pyvista format).

    * **c2** : *pyvista.PolyData*

        > PolyData facet (pyvista format).

    * **strict** : *Bool*

        > If *True*, checks all the points are able to see each other
          (considering the face normal) and then continue. If some points are
          "begind the other faces, it will return *False*,
        > Else, compute the centroids visibility, and might print a warning if
          some points are "behind".

    * **print_warning** : *Bool*

        > If *True*, warning messages will be printed in addition to be returned

    * **rounding_decimal** : *Int*

        > Number of decimals at which rounding shall be done for the points
          coordinates. This is to avoid numeric issues when the points
          coordinates are given as for instance 1.234e-13 instead of 0.

    Returns
    -------
    * **bool**

        > True when the facets "see" each other, False else.

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
    center1 = polygon_centroid(np.round(c1.points, rounding_decimal))
    center2 = polygon_centroid(np.round(c2.points, rounding_decimal))

    v21 = center1 - center2

    n1 = c1.cell_normals[0]
    n2 = c2.cell_normals[0]

    pos_dot_prod = np.dot(v21, n2)
    neg_dot_prod = np.dot(v21, n1)

    if not (pos_dot_prod > 0 and neg_dot_prod < 0):
        return False, ""

    if strict:
        for cel_i, cel_j in [(c1, c2), (c2, c1)]:
            base_center = polygon_centroid(np.round(cel_j.points, rounding_decimal))
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
            base_center = polygon_centroid(np.round(cel_j.points, rounding_decimal))
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


# ########################
# View Factor Computations
# ########################


# #########################
# SCIPY DBLQUAD INTEGRATION

@njit
def _integrand_dblquad(x, y, norm_q_carree, norm_p_carree, scal_qpq,
                       scal_qpp, scal_pq, norm_qp_carree):
    """
    Represents the logarithmic integrand of the contour form‐factor integral
    for one edge‐pair between two facets.

    Used in the *compute_viewfactor* function.

    Core integrand function for SciPy dblquad contour integration.

    Parameters
    ----------
    x, y : float
        Quadrature parameters in [0,1].
    norm_q_carree : float
        Squared length of one directed edge vector (facet1).
    norm_p_carree : float
        Squared length of the other directed edge vector (facet2).
    scal_qpq : float
        Dot(edge1, edge2) term coupling the two edges in the log.
    scal_qpp : float
        Dot(edge2, vector between vertices).
    scal_pq : float
        Dot(edge1, vector between vertices); also multiplies the log.
    norm_qp_carree : float
        Squared length of the inter‐vertex vector.

    Returns
    -------
    float
        V

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

    It is used only in cases of shared edges or vertices

    Parameters
    ----------
    pts1 : ndarray, shape (n1, 3)
        Rounded vertex coordinates of the *receiving* facet.
    pts2 : ndarray, shape (n2, 3)
        Rounded (and possibly epsilon-shifted) vertex coordinates of the
        *emitting* facet.
    constante : float
        Normalization constant = 4π × area of the emitting facet.

    Returns
    -------
    float
        The computed view factor from emitting→receiving (non-negative).

    Notes
    -----
    If the raw integral comes out negative due to numerical noise,
    it is clamped to zero.
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


# ##########################
# GAUSS LEGENDRE INTEGRATION

# Default settings. 
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
    over a 10×10 tensor product of nodes/weights on [0,1]×[0,1].

    Parameters
    ----------
    norm_q : float
        Squared length of the directed edge from the receiving facet.
    norm_p : float
        Squared length of the directed edge from the emitting facet.
    scal_qpq : float
        Dot(edge_q, vector between vertices).
    scal_qpp : float
        Dot(edge_p, vector between vertices).
    scal_pq : float
        Dot(edge_q, edge_p).
    norm_qp : float
        Squared length of the vector between a vertex on facet1 and a vertex on facet2.

    Returns
    -------
    float
        Contribution of this edge‐pair to the contour integral,
        already multiplied by the Gauss–Legendre weights.
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
    (or _GL_ORDER value is modified)
.
    Parameters
    ----------
    pts1 : ndarray, shape (n1,3)
        Ordered vertex coordinates of the *receiving* facet.
    pts2 : ndarray, shape (n2,3)
        Ordered (and possibly shifted) vertex coordinates of the *emitting* facet.
    constante : float
        Normalization factor = 4π × area of the emitting facet.

    Returns
    -------
    float
        The view factor F<sub>2→1</sub>, clamped to ≥0.

    Notes
    -----
    - Uses precomputed nodes & weights `_GL_X`, `_GL_W` of length `_GL_ORDER=10`.
    - Requires no external dependencies once jitted; extremely fast.
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


# #########################
# MAIN INTEGRATION FUNCTION

def compute_viewfactor(cell1, cell2, *, epsilon=1e-6, rounding_decimal=6):
    """
    Compute the view factor between two planar facets, choosing the best integrator.

    By default, non‐adjacent facets are handled by a fast fixed‐order
    Gauss–Legendre quadrature (`_compute_viewfactor_gauss_legendre`), while
    any pair sharing vertices or edges is bumped by `epsilon` and passed to
    the robust SciPy dblquad integrator (`_compute_viewfactor_dblquad`).

    Parameters
    ----------
    cell1 : pyvista.PolyData
        The *receiving* single‐cell facet.
    cell2 : pyvista.PolyData
        The *emitting* single‐cell facet.
    epsilon : float, optional
        Small shift distance along the centroid‐to‐centroid direction
        when facets share any vertex (default=1e-6).
    rounding_decimal : int, optional
        Number of decimals to which vertex coordinates are rounded
        for numeric stability (default=6).

    Returns
    -------
    float
        The view factor F<sub>2→1</sub>, clamped to ≥0.

    Examples
    --------
    >>> import pyvista as pv
    >>> import pyviewfactor as pvf
    >>> tri1 = pv.Triangle([[0,0,0],[1,0,0],[0,1,0]])
    >>> tri2 = pv.Triangle([[0,0,1],[1,0,1],[0,1,1]])
    >>> vf = pvf.compute_viewfactor(tri1, tri2)
    >>> 0.0 < vf < 1.0
    """
    # 1) Extract & round points


    pts1 = face_to_array(cell1)
    pts2 = face_to_array(cell2)

    # 2) Small shift along normal‐bisector if they share vertices
    set1 = {tuple(p) for p in pts1}
    set2 = {tuple(p) for p in pts2}
    use_dblquad = bool(set1 & set2)
    if use_dblquad:
        c1 = polygon_centroid(pts1)
        c2 = polygon_centroid(pts2)
        direction = c2 - c1
        norm = np.linalg.norm(direction)
        if norm > 0.0:
            direction = direction / norm
            pts2 = pts2 + epsilon * direction
    area2 = polygon_area(pts2)
    constante = 4.0 * np.pi * area2
    if use_dblquad:
        VF = _compute_viewfactor_dblquad(pts1, pts2, constante)
    else:
        VF = _compute_viewfactor_gauss_legendre(pts1, pts2, constante)
    return VF



@njit(parallel=True)
def batch_compute_viewfactors(all_pts1, all_pts2, all_const):
    N = all_pts1.shape[0]
    out = np.zeros(N)
    for k in prange(N):
        out[k] = _compute_viewfactor_gauss_legendre(all_pts1[k], all_pts2[k], all_const[k])
    return out








# ####################################
# View Factor Full Matrix Computations
# ####################################

# Helper function to compute VF matrix for a complete mesh
def _is_blocked(f_i, f_j, obstacles, obstruction_kwargs, skip_obstruction):
    """
    Check whether any obstacle mesh blocks the view between two facets.

    Parameters
    ----------
    f_i, f_j : pyvista.PolyData
        Receiving and emitting facets, respectively.
    obstacles : list of pyvista.PolyData
        One or more occluder meshes to test.
    obstruction_kwargs : dict
        Keyword args forwarded to `get_obstruction(...)`.
    skip_obstruction : bool
        If True, skip all obstruction tests (always returns False).

    Returns
    -------
    bool
        True if any obstacle reports a block (i.e., faces do *not* see each other),
        False otherwise.
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
    i, j : int
        Indices of the two facets in the `faces` list.
    faces : list of pyvista.PolyData
        All single‐cell facets extracted from the mesh.
    areas : list of float
        Precomputed facet areas, matching `faces`.
    obstacles : list of pyvista.PolyData
        Occluder meshes.
    skip_visibility : bool
        If False, runs `get_visibility` and sets F=0 on fail.
    skip_obstruction : bool
        If False, runs `_is_blocked` and sets F=0 on fail.
    visibility_kwargs : dict
        Forwarded to `get_visibility`.
    obstruction_kwargs : dict
        Forwarded to `get_obstruction`.
    epsilon : float
        Small shift magnitude for shared‐vertex cases.
    rounding_decimal : int
        Decimal‐rounding for vertex coords.
    use_reciprocity : bool
        If True, uses the relation F[j,i] = (A_i/A_j)*F[i,j]
        otherwise computes both directions.

    Returns
    -------
    tuple of (i, j, F_ij, F_ji)
        Indices and computed view factors.  If culled by visibility or
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


def compute_viewfactor_matrix(mesh, obstacle=None,
                              use_reciprocity=True,
                              visibility_kwargs=None,
                              obstruction_kwargs=None,
                              compute_kwargs=None,
                              skip_visibility=False,
                              skip_obstruction=False,
                              n_jobs=1):
    """
    Compute the view factor matrix for all faces in a mesh, skipping
    pairs that are not mutually visible or are obstructed.

    Parameters
    ----------
    mesh : pyvista.PolyData
        Input mesh with planar faces (triangles or polygons).
    obstacle : pyvista.PolyData, list of PolyData, or None
        Obstruction geometry. Can be a single mesh or a list of meshes. If None,
        no obstruction testing is applied.
    use_reciprocity : bool
        If True, applies reciprocity: F[j,i] = (A_i/A_j) * F[i,j].
    visibility_kwargs : dict or None
        Keyword arguments passed to get_visibility().
    obstruction_kwargs : dict or None
        Keyword arguments passed to get_obstruction().
    n_jobs : int, optional
        Number of parallel jobs to launch (using joblib). 1 means sequential.

    Returns
    -------
    F : ndarray, shape (n_cells, n_cells)
        The view‐factor matrix for the mesh.  By convention
           F[i, j] = view factor from cell j → cell i
        i.e. the fraction of energy leaving cell *j* that arrives at cell *i*.

    Examples
    --------
    Basic usage without obstruction or custom kwargs:

        F = compute_viewfactor_matrix(my_mesh)

    Using a separate obstacle mesh or list of meshes:

        occluder = pv.read("building_block.vtk")
        F = compute_viewfactor_matrix(
            my_mesh,
            obstacle=[occluder, other_obstacle_mesh],
            visibility_kwargs={'strict': False},
            obstruction_kwargs={'strict': True},
            n_jobs=4
        )

    Showing progress bar on sequential run (n_jobs=1):

        F = compute_viewfactor_matrix(
            my_mesh,
            n_jobs=1  # tqdm progress bar shown
        )
    """

    # Prepare faces and areas
    compute_kwargs = compute_kwargs or {}
    epsilon = compute_kwargs.get("epsilon", 1e-6)
    rounding_decimal = compute_kwargs.get("rounding_decimal", 6)

    faces = []
    areas = []

    for i in range(mesh.n_cells):
        raw = mesh.extract_cells(i)
        face = fc_unstruc2poly(raw)
        faces.append(face)
        areas.append(polygon_area(np.round(face.points, rounding_decimal)))
    n = len(faces)
    F = np.zeros((n, n), dtype=np.float64)

    visibility_kwargs = visibility_kwargs or {}
    obstruction_kwargs = obstruction_kwargs or {}

    # Normalize obstacle to list
    obstacles = []
    if obstacle is None:
        obstacles = []
    elif isinstance(obstacle, (list, tuple)):
        obstacles = obstacle
    else:
        obstacles = [obstacle]

    # build a callable with all those locals pre-filled
    compute_pair = partial(
        _compute_pair,
        faces=faces,
        areas=areas,
        obstacles=obstacles,
        skip_visibility=skip_visibility,
        skip_obstruction=skip_obstruction,
        visibility_kwargs=visibility_kwargs,
        obstruction_kwargs=obstruction_kwargs,
        epsilon=epsilon,
        rounding_decimal=rounding_decimal,
        use_reciprocity=use_reciprocity,
    )
    # Prepare all unique pairs
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]

    # Compute in parallel or sequential
    if n_jobs and n_jobs != 1:
        results = Parallel(n_jobs=n_jobs)(
            delayed(compute_pair)(i, j) for (i, j) in pairs
        )
    else:
        results = []
        for (i, j) in tqdm(pairs, desc="Computing view factors", total=len(pairs)):
            results.append(compute_pair(i, j))

    # Fill matrix
    for res in results:
        i, j, fij, fji = res
        F[i, j] = fij
        F[j, i] = fji
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
    mesh : pyvista.PolyData
        Closed or open mesh whose cells correspond to both rows and columns of F.
    F : ndarray, shape (n_cells, n_cells)
        Precomputed view‐factor matrix.
    cell_id : int
        Index of the source cell whose F → others will be plotted.
    cmap : str, optional
        Name of a Matplotlib colormap (default=`"viridis"`).
    show : bool, optional
        If `True`, calls `pl.show()` before returning.
        If `False`, returns the `Plotter` for further customization.

    Returns
    -------
    pv.Plotter
        The PyVista Plotter instance with the view‐factor plot.

    Raises
    ------
    ValueError
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

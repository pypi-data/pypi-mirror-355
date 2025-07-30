"""
file: pvf_visibility_obstruction.py
"""

from numba import njit
import numpy as np
import pyvista as pv
from .pvf_geometry_preprocess import (
    ProcessedGeometry,
    FaceMeshPreprocessor,
    face_to_array,
    polygon_centroid
)


# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Visibility



def get_visibility(c1, c2, strict=False, print_warning=False, rounding_decimal=8):
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


def get_visibility_from_cache(i, j, cache, strict=False, print_warning=False, rounding_decimal=8):
    """
    Check visibility (normals/orientation only) between faces i and j, using FaceCache.
    """
    c1 = cache.get_centroid(i)
    c2 = cache.get_centroid(j)
    n1 = cache.get_normal(i)
    n2 = cache.get_normal(j)
    v21 = c1 - c2

    pos_dot_prod = np.dot(v21, n2)
    neg_dot_prod = np.dot(v21, n1)
    if not (pos_dot_prod > 0 and neg_dot_prod < 0):
        return False, ""

    pts1 = cache.get_face(i)
    pts2 = cache.get_face(j)

    if strict:
        # Test all points of both faces
        for (ptsA, cB, nB) in [(pts1, c2, n2), (pts2, c1, n1)]:
            vectors = np.round(ptsA - cB, rounding_decimal)
            dot_products = np.dot(vectors, nB)
            if np.any(dot_products > 0) and np.any(dot_products < 0):
                warning_str = (
                    "[PVF-Warning-1] strict=True, cells not fully visible (partial)."
                )
                if print_warning:
                    print(warning_str)
                return False, warning_str
    else:
        for (ptsA, cB, nB) in [(pts1, c2, n2), (pts2, c1, n1)]:
            vectors = np.round(ptsA - cB, rounding_decimal)
            dot_products = np.dot(vectors, nB)
            if np.any(dot_products > 0) and np.any(dot_products < 0):
                warning_str = (
                    "[PVF-Warning-2] strict=False, cells partially visible."
                )
                if print_warning:
                    print(warning_str)
                return True, warning_str

    return True, ""


# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Obstruction


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


def get_obstruction_from_cache(i, j, cache, obstacle_mesh, strict=False, print_warning=False, eps=1e-6):
    """
    Obstruction test (with optional strict mode) between faces i and j using FaceCache.
    `obstacle_mesh` can be a PyVista mesh or a FaceCache/ProcessedGeometry object.
    """
    pts1 = cache.get_face(i)
    pts2 = cache.get_face(j)
    c1 = cache.get_centroid(i)
    c2 = cache.get_centroid(j)

    # Optionally, use a similar cache for the obstacle mesh, or extract triangles as needed.
    # For now, fallback to regular PolyData interface:
    # if isinstance(obstacle_mesh, FaceMeshPreprocessor):
        # triangles = [obstacle_mesh.get_face(t) for t in range(obstacle_mesh.N)]
    # else:
        # triangles = [obstacle_mesh.get_cell(t).points for t in range(obstacle_mesh.n_cells)]

    # Filter triangles by AABB
    all_pts = np.vstack((pts1, pts2))
    aabb_min = np.min(all_pts, axis=0)
    aabb_max = np.max(all_pts, axis=0)
    cand_tris = obstacle_mesh.aabb_filter(aabb_min, aabb_max)
    cand_tris = obstacle_mesh.exclude_exact_match(pts1, pts2, cand_tris)

    # Exclude any triangles exactly matching face i or j
    # set1 = {tuple(np.round(p, 8)) for p in pts1}
    # set2 = {tuple(np.round(p, 8)) for p in pts2}
    # def is_exact_match(tri, sets):
        # s = {tuple(np.round(p, 8)) for p in tri}
        # return s == sets[0] or s == sets[1]
    # cand_tris = [tri for tri in cand_tris if not is_exact_match(tri, [set1, set2])]

    if cand_tris.size == 0:
        return True, "fully visible"

    # Strict/non-strict logic:
    if not strict:
        blocked = is_ray_blocked(c1, c2, cand_tris, eps=eps)
        if blocked:
            return False, ""
        else:
            return True, ("partially visible" if print_warning else "")
    else:
        for p1 in pts1:
            for p2 in pts2:
                if is_ray_blocked(p1, p2, cand_tris, eps=eps):
                    warning = "[PVF-Warning-1] Cells are partially obstructed (strict)."
                    if print_warning:
                        return False, warning
                    return False, ""
        return True, ""
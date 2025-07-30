"""
`file: pvf_visibility_obstruction.py`
"""
from numba import njit
import numpy as np
import pyvista as pv
from .pvf_geometry_preprocess import (
    FaceMeshPreprocessor,
    face_to_array,
    polygon_centroid
)

# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Visibility


def get_visibility(c1, c2, strict=False, verbose=False, rounding_decimal=8):
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

    * **verbose** : *Bool*

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
    >>> pvf.get_visibility(tri1, tri2,strict=False, verbose=True)
    """
    center1 = polygon_centroid(np.round(c1.points, rounding_decimal))
    center2 = polygon_centroid(np.round(c2.points, rounding_decimal))

    v21 = center1 - center2

    n1 = c1.cell_normals[0]
    n2 = c2.cell_normals[0]

    pos_dot_prod = np.dot(v21, n2)
    neg_dot_prod = np.dot(v21, n1)

    if not (pos_dot_prod > 0 and neg_dot_prod < 0):
        warning = "[PVF] [Visibility] Cells are not visible"
        if verbose:
            print(warning)
        return False, warning

    if strict:
        for cel_i, cel_j in [(c1, c2), (c2, c1)]:
            base_center = polygon_centroid(np.round(cel_j.points, rounding_decimal))
            normal = cel_j.cell_normals[0]
            vectors = np.round(cel_i.points - base_center, rounding_decimal)
            dot_products = np.dot(vectors, normal)
            if np.any(dot_products > 0) and np.any(dot_products < 0):
                warning_str = (
                    "[PVF] [Visibility] strict=True, "
                    "Cells are considered not visible, but partially are"
                )
                if verbose:
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
                    "[PVF] [Visibility] strict=False, "
                    "Cells are considered visible, but are only partially"
                )
                if verbose:
                    print(warning_str)
                return True, warning_str
    warning = "[PVF] [Visibility] Cells are visible"
    if verbose:
        print(warning)
    return True, warning


def get_visibility_from_cache(i, j, cache, strict=False, verbose=False,
                              rounding_decimal=8):
    """
    Check geometric visibility (normals/orientation only) between faces i and j using a
    ProcessedGeometry cache.

    Uses cached centroids, normals, and vertices for speed, following the same logic
    as `get_visibility`.

    Parameters
    ----------
    * **i** : *int*

        > Index of the first facet in the cache.

    * **j** : *int*

        > Index of the second facet in the cache.

    * **cache** : *pvf.ProcessedGeometry*

        > Geometry cache for all facets.

    * **strict** : *bool*, optional

        > If **True**, checks all vertex-to-centroid relationships for mutual
        visibility. If any points are "behind", returns *False*.
        > If **False**, uses centroids only and prints a warning if partially visible.

    * **verbose** : *bool*, optional

        > If *True*, warning messages will be printed in addition to be returned

    * **rounding_decimal** : *int*, optional

        > Number of decimals to round vertex coordinates for robustness.

    Returns
    -------
    * **bool**

        > **True** if the facets "see" each other; **False** otherwise.

    * **str**

        > Warning message if any (empty string if no warning).

    Examples
    --------
    >>> import pyvista as pv
    >>> import pyviewfactor as pvf
    >>> file = './test_mesh.stl'
    >>> mesh = pv.read(file)
    >>> pg = pvf.ProcessedGeometry(mesh)
    >>> pvf.get_visibility_from_cache(0, 1, pg, strict=True)
    """
    c1 = cache.get_centroid(i)
    c2 = cache.get_centroid(j)
    n1 = cache.get_normal(i)
    n2 = cache.get_normal(j)
    v21 = c1 - c2

    pos_dot_prod = np.dot(v21, n2)
    neg_dot_prod = np.dot(v21, n1)
    if not (pos_dot_prod > 0 and neg_dot_prod < 0):
        warning = "[PVF] [Visibility] Cells are not visible"
        if verbose:
            print(warning)
        return False, warning

    pts1 = cache.get_face(i)
    pts2 = cache.get_face(j)

    if strict:
        # Test all points of both faces
        for (ptsA, cB, nB) in [(pts1, c2, n2), (pts2, c1, n1)]:
            vectors = np.round(ptsA - cB, rounding_decimal)
            dot_products = np.dot(vectors, nB)
            if np.any(dot_products > 0) and np.any(dot_products < 0):
                warning_str = (
                    "[PVF] [Visibility] strict=True, "
                    "Cells are considered not visible, but partially are"
                )
                if verbose:
                    print(warning_str)
                return False, warning_str
    else:
        for (ptsA, cB, nB) in [(pts1, c2, n2), (pts2, c1, n1)]:
            vectors = np.round(ptsA - cB, rounding_decimal)
            dot_products = np.dot(vectors, nB)
            if np.any(dot_products > 0) and np.any(dot_products < 0):
                warning_str = (
                    "[PVF] [Visibility] strict=False, "
                    "Cells are considered visible, but are only partially"
                )
                if verbose:
                    print(warning_str)
                return True, warning_str
    warning = "[PVF] [Visibility] Cells are visible"
    if verbose:
        print(warning)
    return True, warning


# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Obstruction


@njit
def ray_intersects_triangle(orig, dest, v0, v1, v2, eps=1e-6):
    """
    Check whether a ray segment from `orig` to `dest` intersects
    a triangle defined by (v0, v1, v2).

    Uses the Möller–Trumbore algorithm, with additional logic to skip intersections
    if the ray starts or ends exactly at a triangle vertex.

    Parameters
    ----------
    * **orig** : (3,) *float array*

        > Origin point of the ray.

    * **dest** : (3,) *float array*

        > Endpoint of the ray.

    * **v0, v1, v2** : (3,) *float array*

        > Coordinates of the triangle vertices.

    * **eps** : *float*, optional

        > Numerical tolerance for intersection and vertex matching.

    Returns
    -------
    * **bool**

        > **True** if the open segment (orig, dest) intersects the triangle;
        > **False** otherwise.

    """
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
    """
    JITed version
    Determine if the open ray segment from `start` to `end` is blocked
    by **any triangle** in `triangles`.

    Parameters
    ----------
    * **start** : *(3,) float array*

        > Starting point of the ray.

    * **end** : *(3,) float array*

        > Ending point of the ray.

    * **triangles** : *(N,3,3) float array*

        > Array of N triangles (each with 3 vertices).

    * **eps** : *float*, optional

        > Numerical tolerance for intersection and vertex matching.

    Returns
    -------
    * **bool**

        > **True** if any triangle blocks the segment; **False** otherwise.
    """
    for tri in triangles:
        if ray_intersects_triangle(start, end,
                                   tri[0], tri[1], tri[2],
                                   eps):
            return True
    return False


def get_obstruction(cell1, cell2, obstacle,
                    strict=False,
                    verbose=False,
                    eps=1e-6
                    ):
    """
    Test for geometric obstruction (occlusion) between two facets and an obstacle mesh.

    Obstruction is checked using centroid-to-centroid rays for non-strict mode, or all
    vertex-to-vertex rays in strict mode. Optionally skips triangles that match the
    tested faces.

    Parameters
    ----------
    * **cell1** : *pyvista.PolyData* or *(n,3) array*

        > The first facet (receiver).

    * **cell2** : *pyvista.PolyData* or *(n,3) array*

        > The second facet (emitter).

    * **obstacle** : *pvf.FaceMeshPreprocessor* or *pyvista.PolyData*

        > Obstacle mesh to test for occlusion.

    * **strict** : *bool*, optional

        > If **True**, checks all-to-all vertex rays; otherwise checks
        centroid-to-centroid only.

    * **verbose** : *bool*, optional

        > If *True*, warning messages will be printed in addition to be returned

    * **eps** : *float*, optional

        > Numerical tolerance.

    Returns
    -------
    * **bool**

        > **True** if there is no obstruction (faces are visible),
        **False** if blocked.

    * **str**

        > Warning message if any (empty string if no warning).
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
        warning = "[PVF] [Obstruction] Unobstructed (no candidate within c1-c2 AABB)"
        if verbose:
            print(warning)
        return True, warning

    # 5) non‐strict: centroid ray
    if not strict:
        c1 = polygon_centroid(pts1)
        c2 = polygon_centroid(pts2)
        if is_ray_blocked(c1, c2, cand, eps=eps):
            warning = "[PVF] [Obstruction] strict=False, cells obstructed (centroid to centroid)"
            if verbose:
                print(warning)
            return False, warning
        warning = "[PVF] [Obstruction] strict=False, cells not obstructed (centroid to centroid)"
        if verbose:
            print(warning)
        return True, warning
    # 6) strict: every vertex‐to‐vertex
    for p1 in pts1:
        for p2 in pts2:
            if is_ray_blocked(p1, p2, cand, eps=eps):
                warning = "[PVF] [Obstruction] strict=True, cells obstructed (at least one vertex to vertex ray)"
                if verbose:
                    print(warning)
                return False, warning
            
    warning = "[PVF] [Obstruction] strict=True, cells not obstructed (fully, all vertex to vertex rays clear)"
    if verbose:
        print(warning)
    return True, warning


def get_obstruction_from_cache(i, j, cache, obstacle_mesh, strict=False,
                               verbose=False, eps=1e-6):
    """
    Test for geometric obstruction between cached faces i and j, using a preprocessed
    obstacle mesh.

    Efficient variant that uses pre-cached face geometry for both source/target and
    obstacles.

    Parameters
    ----------
    * **i** : *int*

        > Index of first facet in cache.

    * **j** : *int*

        > Index of second facet in cache.

    * **cache** : *ProcessedGeometry*

        > Preprocessed face geometry cache for the tested mesh.

    * **obstacle_mesh** : *FaceMeshPreprocessor*

        > Preprocessed obstacle mesh for occlusion.

    * **strict** : *bool*, optional

        > If **True**, checks all-to-all vertex rays,
        otherwise checks centroids only.

    * **verbose** : *bool*, optional

        > If *True*, warning messages will be printed in addition to be returned

    * **eps** : *float*, optional

        > Numerical tolerance.

    Returns
    -------
    * **bool**

        > **True** if there is no obstruction (faces are visible), **False** if blocked.

    * **str**

        > Warning message if any (empty string if no warning).

    """
    pts1 = cache.get_face(i)
    pts2 = cache.get_face(j)
    c1 = cache.get_centroid(i)
    c2 = cache.get_centroid(j)

    # Filter triangles by AABB
    all_pts = np.vstack((pts1, pts2))
    aabb_min = np.min(all_pts, axis=0)
    aabb_max = np.max(all_pts, axis=0)
    cand_tris = obstacle_mesh.aabb_filter(aabb_min, aabb_max)
    cand_tris = obstacle_mesh.exclude_exact_match(pts1, pts2, cand_tris)

    if cand_tris.size == 0:
        warning = "[PVF] [Obstruction] Unobstructed (no candidate within c1-c2 AABB)"
        if verbose:
            print(warning)
        return True, warning

    # Strict/non-strict logic:
    if not strict:
        blocked = is_ray_blocked(c1, c2, cand_tris, eps=eps)
        if blocked:
            warning = "[PVF] [Obstruction] strict=False, cells obstructed (centroid to centroid)"
            if verbose:
                print(warning)
            return False, warning
        else:
            warning = "[PVF] [Obstruction] strict=False, cells not obstructed (centroid to centroid)"
            if verbose:
                print(warning)
            return True, warning
    else:
        for p1 in pts1:
            for p2 in pts2:
                if is_ray_blocked(p1, p2, cand_tris, eps=eps):
                    warning = "[PVF] [Obstruction] strict=True, cells obstructed (at least one vertex to vertex ray)"
                    if verbose:
                        print(warning)
                    return False, warning
        warning = "[PVF] [Obstruction] strict=True, cells not obstructed (fully, all vertex to vertex rays clear)"
        if verbose:
            print(warning)
        return True, warning
# End of File

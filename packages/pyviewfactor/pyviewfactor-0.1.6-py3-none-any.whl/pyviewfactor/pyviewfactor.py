""" PVF main functions"""


# Imports
from numba import njit
import numpy as np
import pyvista as pv
from joblib import Parallel, delayed
from tqdm import tqdm


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


def get_visibility(c1, c2, strict=False, print_warning=False, rounding_decimal=6):
    """Facets visibility:

    A test to check if two facets can "see" each other, taking the normals
    into consideration (no obstruction tests, only normals orientations).

    [UPDATE 23-05-2025]
    * Use cell_normals[0] and cell_centers().points[0] directly
    * Replace triple product logic with vectorized dot product half-space test
    * Support arbitrary convex planar polygons (not just triangles)

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


@njit
def batch_ray_obstruction(ray_starts, ray_ends, triangles, eps=1e-6):
    """
    Batch-ray intersection test (Möller–Trumbore) for multiple rays.

    Parameters
    ----------
    ray_starts : ndarray, shape (nrays,3)
        Ray origin points.
    ray_ends : ndarray, shape (nrays,3)
        Ray end points.
    triangles : ndarray, shape (ntri,3,3)
        Vertex coords for each triangle.
    eps : float, optional
        Epsilon to skip near-origin hits (default=1e-6).

    Returns
    -------
    mask : ndarray(bool), shape (nrays,)
        True if unobstructed; False if any intersection.

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


def is_ray_obstructed(start, end, obstacle, eps=1e-6, print_debug=False):
    """
    Test if a single ray intersects a triangulated mesh.

    Parameters
    ----------
    start : array-like, shape (3,)
        Ray origin.
    end : array-like, shape (3,)
        Ray end.
    obstacle : pyvista.PolyData
        Triangulated occluder.
    eps : float, optional
        Skip intersections within eps from origin.
    print_debug : bool, optional
        Print intersection info.

    Returns
    -------
    bool
        True if obstructed, False otherwise.

    Examples
    --------
    >>> mesh = pv.Cube().triangulate()
    >>> is_ray_obstructed([0,0,-1],[0,0,1],mesh)
    True
    """
    if not obstacle.is_all_triangles:
        obstacle.triangulate(inplace=True)
    d = np.array(end) - np.array(start)
    L = np.linalg.norm(d)
    for idx in range(obstacle.n_cells):
        v0, v1, v2 = obstacle.get_cell(idx).points
        e1 = v1 - v0
        e2 = v2 - v0
        h = np.cross(d, e2)
        a = np.dot(e1, h)
        if abs(a) < eps:
            continue
        f = 1.0 / a
        sv = np.array(start) - v0
        u = f * np.dot(sv, h)
        if u < 0 or u > 1:
            continue
        q = np.cross(sv, e1)
        v = f * np.dot(d, q)
        if v < 0 or u + v > 1:
            continue
        t = f * np.dot(e2, q)
        if eps < t < L - eps:
            if print_debug:
                print(f"Obstructed by triangle {idx}, t={t}")
            return True
    return False


def get_obstruction(face1, face2, obstacle, strict=False, print_debug=False):
    """
    Determine if face1 and face2 are obstructed by a mesh
    using Möller–Trumbore algorithm.

    [UPDATE 23/05/2025]
    * Only Möller Trumbore algorithm
    * Addition of a strict argument,
        * strict = False > centroid-to-centroid check
        * strict = True > points of cell1 to point of cell2

    Parameters
    ----------
    face1 : pyvista.PolyData
    face2 : pyvista.PolyData
    obstacle : pyvista.PolyData
    strict : bool, optional
        If True, checks all vertex-to-vertex rays between the two faces.
        If False, only the centroid-to-centroid ray is tested.
    print_debug : bool, optional

    Returns
    -------
    visible : bool
    warning_str : str
        Warning if strict=False and result is approximate.
    """
    if not obstacle.is_all_triangles:
        obstacle.triangulate(inplace=True)
    eps = 1e-6
    # --- strict mode: test every vertex‐to‐vertex ray ---
    if strict:
        # build a (N_tri,3,3) array of triangles
        tri_array = np.array([
            obstacle.get_cell(i).points
            for i in range(obstacle.n_cells)
        ])
        # build all (m×n) start‐end pairs
        m = face1.points.shape[0]
        n = face2.points.shape[0]
        m = face1.points.shape[0]
        n = face2.points.shape[0]
        tri_array = np.array([obstacle.get_cell(i).points
                              for i in range(obstacle.n_cells)])
        ray_starts = np.repeat(face1.points, n, axis=0)
        ray_ends = np.tile(face2.points, (m, 1))
        mask = batch_ray_obstruction(ray_starts, ray_ends, tri_array, eps=eps)

        print(mask)
        # if *all* rays clear → fully visible
        if mask.all():
            return True, ""

        # otherwise: strictly we call that "obstructed", but check centroid
        cent_s = face1.cell_centers().points[0]
        cent_e = face2.cell_centers().points[0]
        cent_blocked = is_ray_obstructed(
            cent_s, cent_e, obstacle, eps=eps, print_debug=print_debug
        )

        if not cent_blocked:
            warning = (
                "[PVF-Warning-4] strict=True: vertices indicate partial "
                "visibility, but strict mode treats as obstructed."
            )
            if print_debug:
                print(warning)
            return False, warning

        # centroid also blocked → just obstructed, no warning
        return False, ""

    # --- non‐strict mode: only centroid ray ---
    start = face1.cell_centers().points[0]
    end = face2.cell_centers().points[0]
    blocked = is_ray_obstructed(start, end,
                                obstacle, eps=eps,
                                print_debug=print_debug)
    visible = not blocked
    return visible, ""


@njit
def fast_integrand(norm_q_carree, norm_p_carree, scal_qpq,
                   scal_qpp, scal_pq, norm_qp_carree):
    """
    Compute the contour integral kernel for view factor between two edges.

    Uses 10-point Gauss–Legendre quadrature over [0,1]^2.

    Parameters
    ----------
    norm_q_carree : float
        Squared length of edge vector q.
    norm_p_carree : float
        Squared length of edge vector p.
    scal_qpq : float
        Dot(q, p).
    scal_qpp : float
        Dot(q, p_next).
    scal_pq : float
        Dot(p, q).
    norm_qp_carree : float
        Squared distance between edge origins.

    Returns
    -------
    float
        The weighted sum of ln(expr)*scal_pq over quadrature points.

    Examples
    --------
    >>> fast_integrand(1.0, 1.0, 0.5, 0.5, 0.25, 2.0)
    0.0  # example output
    """
    nodes = np.array([
        -0.9739065285, -0.8650633667, -0.6794095682, -0.4333953941, -0.1488743390,
        0.1488743390, 0.4333953941, 0.6794095682, 0.8650633667, 0.9739065285
    ])
    weights = np.array([
        0.0666713443, 0.1494513491, 0.2190863625, 0.2692667193, 0.2955242247,
        0.2955242247, 0.2692667193, 0.2190863625, 0.1494513491, 0.0666713443
    ])
    x = 0.5 * (nodes + 1.0)
    w = 0.5 * weights
    result = 0.0
    for i in range(10):
        xi = x[i]
        wi = w[i]
        for j in range(10):
            yj = x[j]
            wj = w[j]
            expr = (yj * yj * norm_q_carree + xi * xi * norm_p_carree
                    - 2 * yj * scal_qpq + 2 * xi * scal_qpp
                    - 2 * xi * yj * scal_pq + norm_qp_carree)
            if expr > 0.0:
                result += wi * wj * np.log(expr) * scal_pq
    return result


@njit
def compute_viewfactor_core(cell_1_points, cell_2_points,
                            vect_intra_1, vect_intra_2,
                            constante):
    """
    Core Numba kernel: sum contributions of all edge pairs between two facets.

    Parameters
    ----------
    cell_1_points : ndarray, shape (n1,3)
        Vertex coordinates of facet 1.
    cell_2_points : ndarray, shape (n2,3)
        Vertex coordinates of facet 2.
    vect_intra_1 : ndarray, shape (n1,3)
        Edge vectors of facet 1.
    vect_intra_2 : ndarray, shape (n2,3)
        Edge vectors of facet 2.
    constante : float
        Normalization constant = 4*pi*Area(facet2).

    Returns
    -------
    float
        View factor from facet 2 to facet 1.

    Examples
    --------
    >>> pts1 = np.array([[0,0,0],[1,0,0],[1,1,0]])
    >>> pts2 = pts1 + [0,0,1]
    >>> v1 = np.vstack([pts1[1:]-pts1[:-1], pts1[0]-pts1[-1]])
    >>> v2 = np.vstack([pts2[1:]-pts2[:-1], pts2[0]-pts2[-1]])
    >>> constant = 4*np.pi*1.0
    >>> compute_viewfactor_core(pts1, pts2, v1, v2, constant)
    0.0
    """
    n1 = cell_1_points.shape[0]
    n2 = cell_2_points.shape[0]
    matL = cell_2_points[None, :, :] - cell_1_points[:, None, :]
    norm1 = np.sum(vect_intra_1 * vect_intra_1, axis=1)
    norm2 = np.sum(vect_intra_2 * vect_intra_2, axis=1)
    scal = np.dot(vect_intra_1, vect_intra_2.T)
    total = 0.0
    for i in range(n1):
        nqi = norm1[i]
        for j in range(n2):
            npj = norm2[j]
            ld = matL[i, j]
            nl = np.dot(ld, ld)
            sqpq = np.dot(ld, vect_intra_1[i])
            sqpp = np.dot(ld, vect_intra_2[j])
            spq = scal[i, j]
            val = fast_integrand(nqi, npj, sqpq, sqpp, spq, nl)
            total += round(val / constante, 11)
    return total if total > 0 else 0.0


def compute_viewfactor(cell_1, cell_2, epsilon=0.00001, rounding_decimal=6):
    """
    Compute the radiation view factor from cell_2 to cell_1 using contour integration.

    This function casts each face to an unstructured grid, extracts and rounds
    its vertices, applies a small displacement if cells share vertices, and
    then calls a fast Numba-compiled core to evaluate the contour integral
    via Gauss-Legendre quadrature.

    Parameters
    ----------
    cell_1 : pyvista.PolyData
        The receiving facet (must be a single face PolyData).
    cell_2 : pyvista.PolyData
        The emitting facet (must be a single face PolyData).
    epsilon : float, optional
        Small displacement applied when facets share vertices to avoid singularities
        (default=0.001).
    rounding_decimal : int, optional
        Number of decimal places to round vertex coordinates for numerical stability
        (default=6).

    Returns
    -------
    float
        View factor from cell_2 onto cell_1 (dimensionless, between 0 and 1).

    Examples
    --------
    >>> import pyvista as pv
    >>> tri1 = pv.Triangle([[0,0,0],[1,0,0],[0,1,0]])
    >>> tri2 = pv.Triangle([[0,0,1],[1,0,1],[0,1,1]])
    >>> vf = compute_viewfactorNew(tri1, tri2)
    >>> isinstance(vf, float)
    True
    """
    # 1) Cast to PolyData & unstructured grid
    c1_poly = cell_1
    c2_poly = cell_2
    ug1     = c1_poly.cast_to_unstructured_grid()
    ug2     = c2_poly.cast_to_unstructured_grid()

    # 2) Get and round the points
    pts1 = np.round(ug1.get_cell(0).points, rounding_decimal)
    pts2 = np.round(ug2.get_cell(0).points, rounding_decimal)

    # 3) Detect shared vertices
    #    Build a set of tuples for quick compare
    set1 = {tuple(p) for p in pts1}
    set2 = {tuple(p) for p in pts2}
    if set1 & set2:  # non-empty intersection → shared vertex/edge
        # compute unit centroid direction
        cen1 = c1_poly.cell_centers().points[0]
        cen2 = c2_poly.cell_centers().points[0]
        dir_vec = cen2 - cen1
        dir_vec = dir_vec / np.linalg.norm(dir_vec)
        # translate pts2 by epsilon
        pts2 = pts2 + epsilon * dir_vec

    # 4) Recompute auxiliary arrays for the Numba core
    # Build the intra‐edge (directed edge) vectors for each facet
    pts1_roll = np.roll(pts1, -1, axis=0)
    vect_intra_1 = pts1_roll - pts1
    pts2_roll = np.roll(pts2, -1, axis=0)
    vect_intra_2 = pts2_roll - pts2

    # Compute the 4π·Area constant from cell_2
    area2 = cell_2.compute_cell_sizes(area=True)['Area'][0]
    constante = 4.0 * np.pi * area2
    # 5) Call the Numba core:
    return compute_viewfactor_core(pts1, pts2,
                                   vect_intra_1, vect_intra_2,
                                   constante)


def compute_viewfactor_matrix(mesh, obstacle=None,
                              use_reciprocity=True, 
                              visibility_kwargs=None, obstruction_kwargs=None,
                              skip_visibility=False, skip_obstruction=False,
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
    F : ndarray, shape (n_faces, n_faces)
        Symmetric view factor matrix.

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
    faces = []
    areas = []
    for i in range(mesh.n_cells):
        raw = mesh.extract_cells(i)
        face = fc_unstruc2poly(raw) 
        faces.append(face)
        areas.append(face.compute_cell_sizes(area=True)['Area'][0])
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

    def _is_blocked(f1, f2):
        for obs in obstacles:
            vis_obs, _ = get_obstruction(f1, f2, obs, **obstruction_kwargs)
            if not vis_obs:
                return True
        return False

    # Helper to compute a single pair
    def _compute_pair(i, j):
        """
        Compute a single pair (i,j) in the view‐factor matrix:
          - Optionally cull by visibility (skip_visibility)
          - Optionally cull by one or more obstacles
          - Compute F_ij and F_ji (via reciprocity or explicit)
        Always returns (i, j, F_ij, F_ji).
        """
        f_i = faces[i]
        f_j = faces[j]

        # 1) Visibility cull
        if not skip_visibility:
            vis, _ = get_visibility(f_i, f_j, **(visibility_kwargs or {}))
            if not vis:
                return i, j, 0.0, 0.0

        # 2) Obstruction cull (all obstacles must be clear)
        if obstacles:
            for obs in obstacles:
                vis_obs, _ = get_obstruction(f_i, f_j, obs, **(obstruction_kwargs or {}))
                if not vis_obs:
                    return i, j, 0.0, 0.0

        # 3) Compute the view factor
        F_ij = compute_viewfactor(f_i, f_j)
        if use_reciprocity:
            F_ji = F_ij * (areas[i] / areas[j])
        else:
            F_ji = compute_viewfactor(f_j, f_i)
        return i, j, F_ij, F_ji

    # Prepare all unique pairs
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]

    # Compute in parallel or sequential
    if n_jobs and n_jobs != 1:
        results = Parallel(n_jobs=n_jobs)(
            delayed(_compute_pair)(i, j) for (i, j) in pairs
        )
    else:
        results = []
        for (i, j) in tqdm(pairs, desc="Computing view factors", total=len(pairs)):
            results.append(_compute_pair(i, j))

    # Fill matrix
    for res in results:
        if len(res) == 3:
            i, j, val = res
            F[i, j] = val
        else:
            i, j, fij, fji = res
            F[i, j] = fij
            F[j, i] = fji
    return F


def plot_viewfactor(mesh: pv.PolyData,
                    F: np.ndarray,
                    cell_id: int,
                    cmap: str = "viridis",
                    show: bool = True) -> pv.Plotter:
    """
    Visualize the view factor distribution on a mesh from a given cell.
    pl = plot_viewfactor(mesh, F, cell_id=5, cmap='plasma', show=False)
    pl.show()

    Parameters
    ----------
    mesh : pyvista.PolyData
        The input mesh whose cells correspond to rows/columns of F.
    F : ndarray, shape (n_cells, n_cells)
        Precomputed view‐factor matrix.
    cell_id : int
        Index of the source cell whose view factors to plot.
    cmap : str, optional
        A matplotlib colormap name (default: 'viridis').
    show : bool, optional
        If True (default), immediately renders the window via `pl.show()`.
        If False, returns the Plotter so you can customize further.

    Returns
    -------
    pv.Plotter
        The PyVista Plotter instance with the mesh colored by view factors.

    Raises
    ------
    ValueError
        If `F`’s shape doesn’t match the number of cells in `mesh`.

    Examples
    --------
    >>> import pyvista as pv
    >>> import numpy as np
    >>> # Suppose mesh.n_cells == 5 and F is 5×5
    >>> mesh = pv.Sphere().triangulate()
    >>> F = np.random.rand(mesh.n_cells, mesh.n_cells)
    >>> pl = plot_viewfactor(mesh, F, cell_id=2, cmap='plasma', show=False)
    >>> pl.add_scalar_bar("View Factor")
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

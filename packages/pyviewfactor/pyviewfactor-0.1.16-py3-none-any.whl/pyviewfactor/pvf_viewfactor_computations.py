"""
`file: pvf_viewfactor_computations.py`
"""

import numpy as np
from tqdm import tqdm


from .pvf_geometry_preprocess import (
    ProcessedGeometry,
    FaceMeshPreprocessor,
    face_to_array,
    polygon_centroid,
    polygon_area
)

from .pvf_integrators import (
    compute_viewfactor_dblquad,
    compute_viewfactor_gauss_legendre
)

from .pvf_visibility_obstruction import (
    get_visibility_from_cache,
    get_obstruction_from_cache
)


def compute_viewfactor(cell1, cell2, *, epsilon=1e-6, rounding_decimal=8):
    """
    Compute the view factor between two planar facets, choosing the best integrator.

    By default, non‐adjacent facets are handled by a fast fixed‐order
    Gauss–Legendre quadrature (`_compute_viewfactor_gauss_legendre`), while
    any pair sharing vertices or edges is bumped by `epsilon` and passed to
    the robust SciPy dblquad integrator (`_compute_viewfactor_dblquad`).

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
    """
    pts1 = face_to_array(cell1)
    pts2 = face_to_array(cell2)

    set1 = {tuple(np.round(p, rounding_decimal)) for p in pts1}
    set2 = {tuple(np.round(p, rounding_decimal)) for p in pts2}
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
        VF = compute_viewfactor_dblquad(pts1, pts2, constante)
    else:
        VF = compute_viewfactor_gauss_legendre(pts1, pts2, constante)
    if VF > 0:
        return VF
    else:
        return 0.0


# @njit(parallel=True)
def batch_compute_viewfactors(pts1_arr, nverts1, pts2_arr,
                              nverts2, const_arr, verbose=False):
    """
    Batch Gauss–Legendre view factor computation for arbitrary n-gon pairs.

    Parameters
    ----------
    * **pts1_arr** : (N, max_n1, 3) *float64*

        > Batched receiving facet vertices, zero-padded.

    * **nverts1** : (N,) *int32*

        > Number of valid vertices for each facet in `pts1_arr`.

    * **pts2_arr : (N, max_n2, 3) *float64*

        > Batched emitting facet vertices, zero-padded.

    * **nverts2 : (N,) *int32*

        > Number of valid vertices for each facet in `pts2_arr`.

    * **const_arr** : (N,) *float64*

        > Normalization constants for each pair.

    Returns
    -------
    * **vf** : (N,) *float64*

        > The view factors.
    """
    N = pts1_arr.shape[0]
    vf = np.zeros(N, dtype=np.float64)
    # for k in prange(N):
    for k in tqdm(range(N), desc="[PVF] > GL batch integration",
                  total=N, disable=(not verbose)):
        n1 = nverts1[k]
        n2 = nverts2[k]
        VF = compute_viewfactor_gauss_legendre(
            pts1_arr[k, :n1, :],
            pts2_arr[k, :n2, :],
            const_arr[k]
        )
        vf[k] = VF
    return vf


def compute_viewfactor_matrix(
        mesh,
        obstacles=None,
        skip_visibility=False,
        skip_obstruction=False,
        strict_visibility=False,
        strict_obstruction=False,
        rounding_decimal=8,
        epsilon=1e-3,
        verbose=False
        ):
    """
    Compute the full view-factor matrix for all faces in `mesh`.

    Parameters
    ----------
    * **mesh** : *pyvista.PolyData*

        > The geometry mesh (faces as cells).

    * **obstacles** : list of *pyvista.PolyData*, *pvf.FaceMeshPreprocessor* or *None*

        > List of obstacle meshes (each triangulated).

    * **skip_visibility** : *bool*

        > Skip normal/orientation visibility test if True.

    * **skip_obstruction** : *bool*

        > Skip ray obstruction check if True.

    * **strict_visibility** : *bool*

        > Use strict pointwise test for normal/orientation visibility.

    * **strict_obstruction** : *bool*

        > Use all-to-all vertex obstruction if True (slower but stricter).

    * **rounding_decimal** : *int*

        > Rounding for vertex coordinates.

    * **epsilon** : *float*

        > Displacement for touching facets.

    * **verbose** : *bool*
       > If **True** print progression

    Returns
    -------
    * **F** : ndarray (N, N)

        > Full view-factor matrix.
    """
    N = mesh.n_cells
    pg = ProcessedGeometry(mesh, rounding_decimal=rounding_decimal)
    F = np.zeros((N, N), dtype=np.float64)

    # If obstacles is None, use empty list
    if obstacles is None:
        obstacles = []
    elif not isinstance(obstacles, (list, tuple)):
        obstacles = [obstacles]
    obs_pre = [FaceMeshPreprocessor(obs) for obs in obstacles]
    # Precompute vertex sets for "touching" logic
    vertex_sets = [frozenset(tuple(np.round(vert, rounding_decimal)) for
                   vert in pg.get_face(i)) for i in range(N)]

    touching_pairs = []
    disconnected_pairs = []
    for i in range(N):
        Si = vertex_sets[i]
        for j in range(i + 1, N):
            Sj = vertex_sets[j]
            if Si & Sj:
                touching_pairs.append((i, j))
            else:
                disconnected_pairs.append((i, j))

    N_touching = len(touching_pairs)
    if verbose:
        print(f"[PVF] >>> Touching pairs: {N_touching}")

    for i, j in tqdm(touching_pairs,
                     desc="[PVF] > Vis, Obs & dblquad int.",
                     disable=(not verbose),
                     total=N_touching):
        if not skip_visibility:
            vis, _ = get_visibility_from_cache(i, j, pg, strict=strict_visibility,
                                               rounding_decimal=rounding_decimal)
            if not vis:
                continue
        if not skip_obstruction and obs_pre:
            blocked = False
            for obs in obs_pre:
                if not get_obstruction_from_cache(i, j, pg, obs, strict=False,
                                                  print_warning=False, eps=1e-6)[0]:
                    blocked = True
                    break
            if blocked:
                continue
        # (C) Epsilon shift if shared
        pts1 = pg.get_face(i)
        pts2 = pg.get_face(j)
        pts2_adj = pts2.copy()
        c1 = pg.get_centroid(i)
        c2 = pg.get_centroid(j)
        direction = c2 - c1
        norm = np.linalg.norm(direction)
        # eps_ij = epsilon * 0.5 * (pg.get_size(i) + pg.get_size(j))
        if norm > 0.0:
            direction /= norm
            pts2_adj = pts2_adj + epsilon * direction
        constante = 4.0 * np.pi * pg.get_area(j)
        vf = compute_viewfactor_dblquad(pts1, pts2_adj, constante)
        F[i, j] = vf
        # if use_reciprocity:
        F[j, i] = vf * (pg.get_area(j) / pg.get_area(i))

    # DISCONNECTED: Use batch Gauss-Legendre for speed
    if verbose:
        print(f"\n[PVF] >>> Disconnected pairs (batch): {len(disconnected_pairs)}")
    Kd = len(disconnected_pairs)
    if Kd > 0:
        max_v1 = max(pg.get_face(i).shape[0] for i, _ in disconnected_pairs)
        max_v2 = max(pg.get_face(j).shape[0] for _, j in disconnected_pairs)
        pts1_arr = np.zeros((Kd, max_v1, 3), dtype=np.float64)
        nverts1 = np.zeros(Kd, dtype=np.int32)
        pts2_arr = np.zeros((Kd, max_v2, 3), dtype=np.float64)
        nverts2 = np.zeros(Kd, dtype=np.int32)
        const_arr = np.zeros(Kd, dtype=np.float64)
        valid_mask = np.ones(Kd, dtype=bool)
        for k, (i, j) in enumerate(tqdm(disconnected_pairs,
                                   desc="[PVF] > Batch Vis / Obs",
                                   disable=(not verbose),
                                   total=Kd)):
            # (A) Optional visibility test
            if not skip_visibility:
                vis, _ = get_visibility_from_cache(i, j, pg, strict=strict_visibility,
                                                   rounding_decimal=rounding_decimal)
                if not vis:
                    valid_mask[k] = False
                    continue
            # (B) Optional obstruction test
            if not skip_obstruction and obs_pre:
                blocked = False
                for obs in obs_pre:
                    if not get_obstruction_from_cache(i, j, pg, obs,
                                                      strict=False,
                                                      print_warning=False,
                                                      eps=1e-6)[0]:
                        blocked = True
                        break
                if blocked:
                    valid_mask[k] = False
                    continue
            pts1 = pg.get_face(i)
            pts2 = pg.get_face(j)
            m1 = pts1.shape[0]
            m2 = pts2.shape[0]
            pts1_arr[k, :m1, :] = pts1
            nverts1[k] = m1
            pts2_arr[k, :m2, :] = pts2
            nverts2[k] = m2
            const_arr[k] = 4.0 * np.pi * pg.get_area(j)
        # Batch computation (for all valid pairs)
        vf_arr = np.zeros(Kd, dtype=np.float64)

        idxs = np.flatnonzero(valid_mask)
        M = len(idxs)
        if M == 0:
            vf_arr[:] = 0.0
        else:
            # Build packed contiguous arrays
            packed_pts1 = np.zeros((M, max_v1, 3), dtype=np.float64)
            packed_nverts1 = np.zeros(M, dtype=np.int32)
            packed_pts2 = np.zeros((M, max_v2, 3), dtype=np.float64)
            packed_nverts2 = np.zeros(M, dtype=np.int32)
            packed_const = np.zeros(M, dtype=np.float64)

            for idx, k in enumerate(idxs):
                packed_pts1[idx, :, :] = pts1_arr[k, :, :]
                packed_nverts1[idx] = nverts1[k]
                packed_pts2[idx, :, :] = pts2_arr[k, :, :]
                packed_nverts2[idx] = nverts2[k]
                packed_const[idx] = const_arr[k]
            # Now you can safely call the Numba function
            vf_valid = batch_compute_viewfactors(
                packed_pts1,
                packed_nverts1,
                packed_pts2,
                packed_nverts2,
                packed_const,
                verbose=True
            )
            vf_arr[idxs] = vf_valid
        for idx, k in enumerate(idxs):
            i, j = disconnected_pairs[k]
            fij = vf_valid[idx]
            F[i, j] = fij
            # if use_reciprocity:
            F[j, i] = fij * (pg.get_area(j) / pg.get_area(i))

    return F

# End of File

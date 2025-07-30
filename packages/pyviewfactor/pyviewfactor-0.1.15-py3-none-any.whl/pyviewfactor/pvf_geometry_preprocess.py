"""
file:  pvf_geometry.py
"""

import numpy as np
import pyvista as pv
from numba import njit

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


def face_to_array(face):
    """Extract and return the vertices of a PyVista PolyData face as ndarray."""
    faces = face.faces
    n_pts = int(faces[0])
    idxs = faces[1:1 + n_pts]
    return np.array(face.points[idxs], dtype=np.float64)


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


class ProcessedGeometry:
    """
    A lightweight structure to cache face geometry (points, normals, centroids, area)
    for high-performance view factor computation.
    """
    def __init__(self, mesh, rounding_decimal=8):
        self.rounding_decimal = rounding_decimal
        self.N = mesh.n_cells
        self.points = []
        self.normals = np.zeros((self.N, 3), dtype=np.float64)
        self.centroids = np.zeros((self.N, 3), dtype=np.float64)
        self.areas = np.zeros(self.N, dtype=np.float64)
        self.sizes = np.zeros(self.N, dtype=np.float64)

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

            self.areas[i] = polygon_area(np.round(face.points, rounding_decimal))
            edges = np.roll(pts, -1, axis=0) - pts
            edge_lengths = np.linalg.norm(edges, axis=1)
            self.sizes[i] = np.mean(edge_lengths)

    def get_face(self, i):
        return self.points[i]

    def get_normal(self, i):
        return self.normals[i]

    def get_centroid(self, i):
        return self.centroids[i]

    def get_area(self, i):
        return self.areas[i]

    def get_size(self, i):
        return self.sizes[i]


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



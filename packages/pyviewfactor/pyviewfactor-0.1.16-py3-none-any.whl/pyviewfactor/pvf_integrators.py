"""
`file: pvf_integrators.py`
"""

import numpy as np
from numpy.polynomial.legendre import leggauss
import scipy.integrate
from numba import njit

# SCIPY DBLQUAD INTEGRATION


@njit
def integrand_dblquad(x, y, norm_q_carree, norm_p_carree, scal_qpq,
                      scal_qpp, scal_pq, norm_qp_carree):
    """
    Represents the logarithmic integrand of the contour form‐factor integral
    for one edge‐pair between two facets.

    Used in the `compute_viewfactor_dblquad` function.

    Core integrand function for SciPy dblquad contour integration.

    Parameters
    ----------
    * **x, y** : *float*

        > Quadrature parameters in [0,1].

    * **norm_q_carree** : *float*

        > Squared length of one directed edge vector (facet1).

    * **norm_p_carree** : *float*

        > Squared length of the other directed edge vector (facet2).

    * **scal_qpq** : *float*

        > dot(edge1, edge2) term coupling the two edges in the log.

    * **scal_qpp** : *float*

        > dot(edge2, vector between vertices).

    * **scal_pq** : *float*

        > dot(edge1, vector between vertices); also multiplies the log.

    * **norm_qp_carree** : *float*

        > Squared length of the inter‐vertex vector.

    Returns
    -------
    * *float*

    """
    integrand_function = np.log(y**2 * norm_q_carree
                                + x**2 * norm_p_carree
                                - 2 * y * scal_qpq
                                + 2 * x * scal_qpp
                                - 2 * x * y * scal_pq
                                + norm_qp_carree
                                ) * scal_pq
    return integrand_function


def compute_viewfactor_dblquad(pts1, pts2, constante):
    """
    Robust fallback integrator using SciPy’s dblquad for contour integration.

    This method loops over every pair of directed edges from two facets
    and evaluates the exact contour integral via `scipy.integrate.dblquad`.

    It is used only in cases of shared edges or vertices

    Parameters
    ----------
    * **pts1** : ndarray, shape (n1, 3)

        > Rounded vertex coordinates of the *receiving* facet.

    * **pts2** : *ndarray*, shape (n2, 3)

        > Rounded (and possibly epsilon-shifted) vertex coordinates of the
        *emitting* facet.

    * **constante** : *float*

        > Normalization constant = 4π × area of the emitting facet.

    Returns
    -------
    * **float**

        > The computed view factor from F<sub>2→1</sub> (non-negative).

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
                integrand_dblquad,
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
def integrand_gauss_legendre(norm_q, norm_p, scal_qpq, scal_qpp, scal_pq, norm_qp):
    """
    Fixed‐order Gauss–Legendre quadrature kernel for one edge‐pair.

    Internally used by `_compute_viewfactor_gauss_legendre` to sum
    over a 10×10 tensor product of nodes/weights on [0,1]×[0,1].

    Parameters
    ----------
    * **norm_q**: *float*

        > Squared length of the directed edge from the receiving facet.

    * **norm_p**: *float*

        > Squared length of the directed edge from the emitting facet.

    * **scal_qpq**: *float*

        > Dot(edge_q, vector between vertices).

    * **scal_qpp**: *float*

        > dot(edge_p, vector between vertices).

    * **scal_pq**: *float*

        > dot(edge_q, edge_p).

    * **norm_qp** : *float*

        Squared length of the vector between a vertex on facet1 and a vertex on facet2.

    Returns
    -------
    * **float**

        > Contribution of this edge‐pair to the contour integral,
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
def compute_viewfactor_gauss_legendre(pts1, pts2, constante):
    """
    Fast Numba‐JITed contour integrator using fixed‐order Gauss–Legendre.

    This routine evaluates the view‐factor contour integral by looping
    over every pair of directed edges on two convex planar facets,
    approximating the double integral with a 30×30 Gauss–Legendre rule
    (or _GL_ORDER value can modified)

    Parameters
    ----------
    * **pts1** : *ndarray*, shape (n1,3)

        > Ordered vertex coordinates of the *receiving* facet.

    * **pts2** : *ndarray*, shape (n2,3)

        > Ordered (and possibly shifted) vertex coordinates of the *emitting* facet.

    * **constante** : *float*

        > Normalization factor = 4π × area of the emitting facet.

    Returns
    -------
    * **float**

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
            total += integrand_gauss_legendre(nq, np_, sqpq, sqpp, spq, nqp)
    vf = total / constante
    return vf

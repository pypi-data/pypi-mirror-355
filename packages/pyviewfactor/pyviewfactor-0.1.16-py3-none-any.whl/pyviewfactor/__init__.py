"""
.. include:: ../README.md
"""

from ._version import __version__
from .pvf_geometry_preprocess import (
    ProcessedGeometry,
    FaceMeshPreprocessor,
    fc_unstruc2poly,
    face_to_array,
    polygon_area,
    polygon_centroid,
    face_normal_numpy,
    tri_overlaps_aabb
)
from .pvf_visibility_obstruction import (
    get_visibility,
    get_visibility_from_cache,
    get_obstruction,
    get_obstruction_from_cache
)

from .pvf_integrators import (
    set_quadrature_order,
)

from .pvf_viewfactor_computations import (
    compute_viewfactor,
    batch_compute_viewfactors,
    compute_viewfactor_matrix
)

from .pvf_plot import (
    plot_viewfactor
)
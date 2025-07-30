# plot.py
import pyvista as pv
import numpy as np
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

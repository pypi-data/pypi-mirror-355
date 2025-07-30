from __future__ import annotations
from pydantic import ConfigDict, Field, PrivateAttr
from biochatter.api_agent.base.agent_abc import BaseAPI
import typing
from typing import *
import collections

class ScPlPaga(BaseAPI):
    """
    Plot the PAGA graph through thresholding low-connectivity edges, compute a coarse-grained layout, and obtain embeddings with more meaningful global topology. Uses various layout algorithms, including ForceAtlas2 and igraph\'s layouts.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    threshold: float | None = Field(
        None,
        description="""Do not draw edges for weights below this threshold, set to 0 for all edges, helps in getting a clearer graph by discarding low-connectivity edges.
        Original annotation is float | None
        """,
    )
    color: str | Mapping[str | int, Mapping[Any, float]] | None = Field(
        None,
        description="""Defines node colors using gene names or obs annotation. Can also plot the degree of the abstracted graph or visualize pie charts at each node.
        Original annotation is str | Mapping[str | int, Mapping[Any, float]] | None
        """,
    )
    layout: typing.Any = Field(
        None,
        description="""Computes positions through different layouts like \'ForceAtlas2\', \'Fruchterman-Reingold\', \'Reingold-Tilford\', \'eqally spaced tree\'.
        Original annotation is _Layout | None
        """,
    )
    layout_kwds: Mapping[str, Any] = Field(
        "{}",
        description="""Keywords for the layout.
        Original annotation is Mapping[str, Any]
        """,
    )
    init_pos: typing.Any = Field(
        None,
        description="""Two-column array with x and y coordinates for initializing the layout.
        Original annotation is np.ndarray | None
        """,
    )
    root: typing.Any = Field(
        0,
        description="""Index of the root node for tree layout or list of root node indices. Automatically calculates root vertices if None or empty list.
        Original annotation is int | str | Sequence[int] | None
        """,
    )
    labels: str | Sequence[str] | Mapping[str, str] | None = Field(
        None,
        description="""Node labels, defaults to group labels stored in categorical data computed by tl.paga if None.
        Original annotation is str | Sequence[str] | Mapping[str, str] | None
        """,
    )
    single_component: bool = Field(
        False,
        description="""Restricts to the largest connected component.
        Original annotation is bool
        """,
    )
    solid_edges: str = Field(
        "connectivities",
        description="""Key specifying the matrix for solid black edges.
        Original annotation is str
        """,
    )
    dashed_edges: str | None = Field(
        None,
        description="""Key specifying the matrix for dashed grey edges, if None, no dashed edges are drawn.
        Original annotation is str | None
        """,
    )
    transitions: str | None = Field(
        None,
        description="""Key specifying the matrix for arrows, for instance \'transitions_confidence\'.
        Original annotation is str | None
        """,
    )
    fontsize: int | None = Field(
        None,
        description="""Font size for node labels.
        Original annotation is int | None
        """,
    )
    fontweight: str = Field(
        "bold",
        description="""No description available.
        Original annotation is str
        """,
    )
    fontoutline: int | None = Field(
        None,
        description="""Width of the white outline around fonts.
        Original annotation is int | None
        """,
    )
    text_kwds: Mapping[str, Any] = Field(
        "{}",
        description="""Keywords for matplotlib axes text.
        Original annotation is Mapping[str, Any]
        """,
    )
    node_size_scale: float = Field(
        1.0,
        description="""Increase or decrease node sizes.
        Original annotation is float
        """,
    )
    node_size_power: float = Field(
        0.5,
        description="""Influence of group sizes on node radius.
        Original annotation is float
        """,
    )
    edge_width_scale: float = Field(
        1.0,
        description="""Scale for edge width relative to rcParams[\'lines.linewidth\'].
        Original annotation is float
        """,
    )
    min_edge_width: float | None = Field(
        None,
        description="""Minimum width of solid edges.
        Original annotation is float | None
        """,
    )
    max_edge_width: float | None = Field(
        None,
        description="""Maximum width of solid and dashed edges.
        Original annotation is float | None
        """,
    )
    arrowsize: int = Field(
        30,
        description="""Size of arrow heads for directed graphs.
        Original annotation is int
        """,
    )
    title: str | None = Field(
        None,
        description="""Provides a title.
        Original annotation is str | None
        """,
    )
    left_margin: float = Field(
        0.01,
        description="""No description available.
        Original annotation is float
        """,
    )
    random_state: int | None = Field(
        0,
        description="""Changes initial states for layouts like \'fr\', ensuring reproducibility if not None.
        Original annotation is int | None
        """,
    )
    pos: typing.Any = Field(
        None,
        description="""Two-column array-like coordinates for drawing or path to a .gdf file exported from visualization software.
        Original annotation is np.ndarray | Path | str | None
        """,
    )
    normalize_to_color: bool = Field(
        False,
        description="""Whether to normalize categorical plots to color or underlying grouping.
        Original annotation is bool
        """,
    )
    cmap: typing.Any = Field(
        None,
        description="""Color map.
        Original annotation is str | Colormap | None
        """,
    )
    cax: typing.Any = Field(
        None,
        description="""Matplotlib axes object for potential colorbar.
        Original annotation is Axes | None
        """,
    )
    colorbar: typing.Any = Field(
        None,
        description="""No description available.
        """,
    )
    cb_kwds: Mapping[str, Any] = Field(
        "{}",
        description="""Keyword arguments for matplotlib.colorbar.Colorbar, like ticks.
        Original annotation is Mapping[str, Any]
        """,
    )
    frameon: bool | None = Field(
        None,
        description="""Draws a frame around the PAGA graph.
        Original annotation is bool | None
        """,
    )
    add_pos: bool = Field(
        True,
        description="""Adds positions to adata.uns[\'paga\'].
        Original annotation is bool
        """,
    )
    export_to_gexf: bool = Field(
        False,
        description="""Exports to gexf format for other visualization programs.
        Original annotation is bool
        """,
    )
    use_raw: bool = Field(
        True,
        description="""No description available.
        Original annotation is bool
        """,
    )
    colors: typing.Any = Field(
        None,
        description="""No description available.
        """,
    )
    groups: typing.Any = Field(
        None,
        description="""No description available.
        """,
    )
    plot: bool = Field(
        True,
        description="""If False, only computes layout without creating the figure.
        Original annotation is bool
        """,
    )
    show: bool | None = Field(
        None,
        description="""No description available.
        Original annotation is bool | None
        """,
    )
    # Jiahang (TODO): return_fig only exists in some of pl api, not all.
    # show and ax don't control save or return figure
    # save will take some default image name which cannot be controlled by user.
    # this figure control really sucks.
    save: bool | str | None = Field(
        # None,
        True,
        description="""If True or a string, saves the figure with inferred file type based on extension.
        Original annotation is bool | str | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""Matplotlib axes object.
        Original annotation is Axes | None
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.paga")
    _products_str_repr: list[str] = PrivateAttr(default=['data.uns["paga"]["pos"]'])
    _data_name: str = PrivateAttr(default="adata")


class ScPlScatter(BaseAPI):
    """
    Scatter plot along observations or variables axes. Color the plot using annotations of observations, variables, or expression of genes.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    x: str | None = Field(
        None,
        description="""x coordinate.
        Original annotation is str | None
        """,
    )
    y: str | None = Field(
        None,
        description="""y coordinate.
        Original annotation is str | None
        """,
    )
    color: typing.Any = Field(
        None,
        description="""Keys for annotations of observations/cells or variables/genes, or a hex color specification.
        Original annotation is str | ColorLike | Collection[str | ColorLike] | None
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""Whether to use raw attribute of adata. Defaults to true if .raw is present.
        Original annotation is bool | None
        """,
    )
    layers: typing.Any = Field(
        None,
        description="""Use the layers attribute of adata if present: specify the layer for x, y and color.
        Original annotation is str | Collection[str] | None
        """,
    )
    sort_order: bool = Field(
        True,
        description="""For continuous annotations used as color parameter, plot data points with higher values on top of others.
        Original annotation is bool
        """,
    )
    alpha: float | None = Field(
        None,
        description="""No description available.
        Original annotation is float | None
        """,
    )
    basis: typing.Any = Field(
        None,
        description="""String that denotes a plotting tool that computed coordinates.
        Original annotation is _Basis | None
        """,
    )
    groups: str | Iterable[str] | None = Field(
        None,
        description="""Restrict to a few categories in categorical observation annotation. The default is not to restrict to any groups.
        Original annotation is str | Iterable[str] | None
        """,
    )
    components: str | Collection[str] | None = Field(
        None,
        description="""For instance, [\'1,2\', \'2,3\']. To plot all available components use components=\'all\'.
        Original annotation is str | Collection[str] | None
        """,
    )
    projection: typing.Any = Field(
        "2d",
        description="""Projection of plot (default: \'2d\').
        Original annotation is Literal['2d', '3d']
        """,
    )
    legend_loc: typing.Any = Field(
        "right margin",
        description="""Location of legend, either \'on data\', \'right margin\', None, or a valid keyword for the loc parameter of matplotlib.legend.Legend.
        Original annotation is _LegendLoc | None
        """,
    )
    legend_fontsize: typing.Any = Field(
        None,
        description="""Numeric size in pt or string describing the size.
        Original annotation is float | _FontSize | None
        """,
    )
    legend_fontweight: typing.Any = Field(
        None,
        description="""Legend font weight. A numeric value in range 0-1000 or a string. Defaults to \'bold\' if legend_loc == \'on data\', otherwise to \'normal\'.
        Original annotation is int | _FontWeight | None
        """,
    )
    legend_fontoutline: float | None = Field(
        None,
        description="""Line width of the legend font outline in pt. Draws a white outline using the path effect matplotlib.patheffects.withStroke.
        Original annotation is float | None
        """,
    )
    color_map: typing.Any = Field(
        None,
        description="""Color map to use for continuous variables. Can be a name or a matplotlib.colors.Colormap instance.
        Original annotation is str | Colormap | None
        """,
    )
    palette: typing.Any = Field(
        None,
        description="""Colors to use for plotting categorical annotation groups. The palette can be a valid matplotlib.colors.ListedColormap name, a cycler.Cycler object, a dict mapping categories to colors, or a sequence of colors.
        Original annotation is Cycler | ListedColormap | ColorLike | Sequence[ColorLike] | None
        """,
    )
    frameon: bool | None = Field(
        None,
        description="""Draw a frame around the scatter plot. Defaults to value set in scanpy.set_figure_params, defaults to true.
        Original annotation is bool | None
        """,
    )
    right_margin: float | None = Field(
        None,
        description="""No description available.
        Original annotation is float | None
        """,
    )
    left_margin: float | None = Field(
        None,
        description="""No description available.
        Original annotation is float | None
        """,
    )
    size: float | None = Field(
        None,
        description="""Point size. If None, is automatically computed as 120000 / n_cells. Can be a sequence containing the size for each cell.
        Original annotation is float | None
        """,
    )
    marker: str | Sequence[str] = Field(
        ".",
        description="""No description available.
        Original annotation is str | Sequence[str]
        """,
    )
    title: str | Collection[str] | None = Field(
        None,
        description="""Provide title for panels either as string or list of strings.
        Original annotation is str | Collection[str] | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: str | bool | None = Field(
        # None,
        True,
        description="""If true or a string, save the figure. A string is appended to the default filename. Infer the filetype if ending on {\'.pdf\', \'.png\', \'.svg\'}.
        Original annotation is str | bool | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""A matplotlib axes object. Only works if plotting a single component.
        Original annotation is Axes | None
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.scatter")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlUmap(BaseAPI):
    """
    Scatter plot in UMAP basis.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    color: typing.Any = Field(
        None,
        description="""Keys for annotations of observations/cells or variables/genes, e.g., `\'ann1\'` or `[\'ann1\', \'ann2\']`.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    mask_obs: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool]] | str | None
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Column name in `.var` DataFrame that stores gene symbols. By default `var_names` refer to the index column of the `.var` DataFrame. Setting this option allows alternative names to be used.
        Original annotation is str | None
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""Use `.raw` attribute of `adata` for coloring with gene expression. If `None`, defaults to `True` if `layer` isn\'t provided and `adata.raw` is present.
        Original annotation is bool | None
        """,
    )
    sort_order: typing.Any = Field(
        True,
        description="""For continuous annotations used as color parameter, plot data points with higher values on top of others.
        Original annotation is <class 'bool'>
        """,
    )
    edges: typing.Any = Field(
        False,
        description="""Show edges.
        Original annotation is <class 'bool'>
        """,
    )
    edges_width: typing.Any = Field(
        0.1,
        description="""Width of edges.
        Original annotation is <class 'float'>
        """,
    )
    edges_color: typing.Any = Field(
        "grey",
        description="""Color of edges. See :func:`~networkx.drawing.nx_pylab.draw_networkx_edges`.
        Original annotation is str | collections.abc.Sequence[float] | collections.abc.Sequence[str]
        """,
    )
    neighbors_key: str | None = Field(
        None,
        description="""Where to look for neighbors connectivities. If not specified, this looks .obsp[\'connectivities\'] for connectivities (default storage place for pp.neighbors). If specified, this looks .obsp[.uns[neighbors_key][\'connectivities_key\']] for connectivities.
        Original annotation is str | None
        """,
    )
    arrows: typing.Any = Field(
        False,
        description="""Show arrows (deprecated in favour of `scvelo.pl.velocity_embedding`).
        Original annotation is <class 'bool'>
        """,
    )
    arrows_kwds: typing.Any = Field(
        None,
        description="""Passed to :meth:`~matplotlib.axes.Axes.quiver`
        Original annotation is collections.abc.Mapping[str, typing.Any] | None
        """,
    )
    groups: typing.Any = Field(
        None,
        description="""Restrict to a few categories in categorical observation annotation. The default is not to restrict to any groups.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    components: typing.Any = Field(
        None,
        description="""For instance, `[\'1,2\', \'2,3\']`. To plot all available components use `components=\'all\'`.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    dimensions: typing.Any = Field(
        None,
        description="""0-indexed dimensions of the embedding to plot as integers. E.g. [(0, 1), (1, 2)]. Unlike `components`, this argument is used in the same way as `colors`, e.g. is used to specify a single plot at a time. Will eventually replace the components argument.
        Original annotation is tuple[int, int] | collections.abc.Sequence[tuple[int, int]] | None
        """,
    )
    layer: str | None = Field(
        None,
        description="""Name of the AnnData object layer that wants to be plotted. By default adata.raw.X is plotted. If `use_raw=False` is set, then `adata.X` is plotted. If `layer` is set to a valid layer name, then the layer is plotted. `layer` takes precedence over `use_raw`.
        Original annotation is str | None
        """,
    )
    projection: typing.Any = Field(
        "2d",
        description="""Projection of plot (default: `\'2d\'`).
        Original annotation is typing.Literal['2d', '3d']
        """,
    )
    scale_factor: float | None = Field(
        None,
        description="""No description available.
        Original annotation is float | None
        """,
    )
    color_map: typing.Any = Field(
        None,
        description="""Color map to use for continous variables. Can be a name or a :class:`~matplotlib.colors.Colormap` instance (e.g. `\"magma`\", `\"viridis\"` or `mpl.cm.cividis`), see :meth:`~matplotlib.cm.ColormapRegistry.get_cmap`. If `None`, the value of `mpl.rcParams[\"image.cmap\"]` is used. The default `color_map` can be set using :func:`~scanpy.set_figure_params`.
        Original annotation is matplotlib.colors.Colormap | str | None
        """,
    )
    cmap: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is matplotlib.colors.Colormap | str | None
        """,
    )
    palette: typing.Any = Field(
        None,
        description="""Colors to use for plotting categorical annotation groups. The palette can be a valid :class:`~matplotlib.colors.ListedColormap` name (`\'Set2\'`, `\'tab20\'`, …), a :class:`~cycler.Cycler` object, a dict mapping categories to colors, or a sequence of colors. Colors must be valid to matplotlib. (see :func:`~matplotlib.colors.is_color_like`). If `None`, `mpl.rcParams[\"axes.prop_cycle\"]` is used unless the categorical variable already has colors stored in `adata.uns[\"{var}_colors\"]`. If provided, values of `adata.uns[\"{var}_colors\"]` will be set.
        Original annotation is str | collections.abc.Sequence[str] | cycler.Cycler | None
        """,
    )
    na_color: str | tuple[float, ...] = Field(
        "lightgray",
        description="""Color to use for null or masked values. Can be anything matplotlib accepts as a color. Used for all points if `color=None`.
        Original annotation is str | tuple[float, ...]
        """,
    )
    na_in_legend: typing.Any = Field(
        True,
        description="""If there are missing values, whether they get an entry in the legend. Currently only implemented for categorical legends.
        Original annotation is <class 'bool'>
        """,
    )
    size: typing.Any = Field(
        None,
        description="""Point size. If `None`, is automatically computed as 120000 / n_cells. Can be a sequence containing the size for each cell. The order should be the same as in adata.obs.
        Original annotation is float | collections.abc.Sequence[float] | None
        """,
    )
    frameon: bool | None = Field(
        None,
        description="""Draw a frame around the scatter plot. Defaults to value set in :func:`~scanpy.set_figure_params`, defaults to `True`.
        Original annotation is bool | None
        """,
    )
    legend_fontsize: typing.Any = Field(
        None,
        description="""Numeric size in pt or string describing the size. See :meth:`~matplotlib.text.Text.set_fontsize`.
        Original annotation is typing.Union[float, typing.Literal['xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large'], NoneType]
        """,
    )
    legend_fontweight: typing.Any = Field(
        "bold",
        description="""Legend font weight. A numeric value in range 0-1000 or a string. Defaults to `\'bold\'` if `legend_loc == \'on data\'`, otherwise to `\'normal\'`. See :meth:`~matplotlib.text.Text.set_fontweight`.
        Original annotation is typing.Union[int, typing.Literal['light', 'normal', 'medium', 'semibold', 'bold', 'heavy', 'black']]
        """,
    )
    legend_loc: typing.Any = Field(
        "right margin",
        description="""Location of legend, either `\'on data\'`, `\'right margin\'`, `None`, or a valid keyword for the `loc` parameter of :class:`~matplotlib.legend.Legend`.
        Original annotation is typing.Optional[typing.Literal['none', 'right margin', 'on data', 'on data export', 'best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 'upper center', 'center']]
        """,
    )
    legend_fontoutline: int | None = Field(
        None,
        description="""Line width of the legend font outline in pt. Draws a white outline using the path effect :class:`~matplotlib.patheffects.withStroke`.
        Original annotation is int | None
        """,
    )
    colorbar_loc: str | None = Field(
        "right",
        description="""Where to place the colorbar for continous variables. If `None`, no colorbar is added.
        Original annotation is str | None
        """,
    )
    vmax: typing.Any = Field(
        None,
        description="""The value representing the upper limit of the color scale. The format is the same as for `vmin`.
        Original annotation is str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float] | collections.abc.Sequence[str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float]] | None
        """,
    )
    vmin: typing.Any = Field(
        None,
        description="""The value representing the lower limit of the color scale. Values smaller than vmin are plotted with the same color as vmin. vmin can be a number, a string, a function or `None`. If vmin is a string and has the format `pN`, this is interpreted as a vmin=percentile(N). For example vmin=\'p1.5\' is interpreted as the 1.5 percentile. If vmin is function, then vmin is interpreted as the return value of the function over the list of values to plot. For example to set vmin tp the mean of the values to plot, `def my_vmin(values): return np.mean(values)` and then set `vmin=my_vmin`. If vmin is None (default) an automatic minimum value is used as defined by matplotlib `scatter` function. When making multiple plots, vmin can be a list of values, one for each plot. For example `vmin=[0.1, \'p1\', None, my_vmin]`
        Original annotation is str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float] | collections.abc.Sequence[str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float]] | None
        """,
    )
    vcenter: typing.Any = Field(
        None,
        description="""The value representing the center of the color scale. Useful for diverging colormaps. The format is the same as for `vmin`. Example: ``sc.pl.umap(adata, color=\'TREM2\', vcenter=\'p50\', cmap=\'RdBu_r\')``
        Original annotation is str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float] | collections.abc.Sequence[str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float]] | None
        """,
    )
    norm: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is matplotlib.colors.Normalize | collections.abc.Sequence[matplotlib.colors.Normalize] | None
        """,
    )
    add_outline: bool | None = Field(
        False,
        description="""If set to True, this will add a thin border around groups of dots. In some situations this can enhance the aesthetics of the resulting image
        Original annotation is bool | None
        """,
    )
    # Jiahang (TODO): openai bug - array schema missing items.
    # all comments come from this reason. seems that tuple is not supported.
    # outline_width: tuple[float, float] = Field(
    #     (0.3, 0.05),
    #     description="""Tuple with two width numbers used to adjust the outline. The first value is the width of the border color as a fraction of the scatter dot size (default: 0.3). The second value is width of the gap color (default: 0.05).
    #     Original annotation is tuple[float, float]
    #     """,
    # )
    # outline_color: tuple[str, str] = Field(
    #     ("black", "white"),
    #     description="""Tuple with two valid color names used to adjust the add_outline. The first color is the border color (default: black), while the second color is a gap color between the border color and the scatter dot (default: white).
    #     Original annotation is tuple[str, str]
    #     """,
    # )
    ncols: typing.Any = Field(
        4,
        description="""Number of panels per row.
        Original annotation is <class 'int'>
        """,
    )
    hspace: typing.Any = Field(
        0.25,
        description="""Adjust the height of the space between multiple panels.
        Original annotation is <class 'float'>
        """,
    )
    wspace: float | None = Field(
        None,
        description="""Adjust the width of the space between multiple panels.
        Original annotation is float | None
        """,
    )
    title: typing.Any = Field(
        None,
        description="""Provide title for panels either as string or list of strings, e.g. `[\'title1\', \'title2\', ...]`.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: bool | str | None = Field(
        # None,
        True,
        description="""If `True` or a `str`, save the figure. A string is appended to the default filename. Infer the filetype if ending on {`\'.pdf\'`, `\'.png\'`, `\'.svg\'`}.
        Original annotation is bool | str | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""A matplotlib axes object. Only works if plotting a single component.
        Original annotation is matplotlib.axes._axes.Axes | None
        """,
    )
    return_fig: bool | None = Field(
        None,
        description="""Return the matplotlib figure.
        Original annotation is bool | None
        """,
    )
    marker: typing.Any = Field(
        ".",
        description="""No description available.
        Original annotation is str | collections.abc.Sequence[str]
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.umap")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlTsne(BaseAPI):
    """
    Scatter plot in tSNE basis.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    color: typing.Any = Field(
        None,
        description="""Keys for annotations of observations/cells or variables/genes.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    mask_obs: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool]] | str | None
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Column name in `.var` DataFrame that stores gene symbols.
        Original annotation is str | None
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""Use `.raw` attribute of `adata` for coloring with gene expression.
        Original annotation is bool | None
        """,
    )
    sort_order: typing.Any = Field(
        True,
        description="""For continuous annotations used as color parameter, plot data points with higher values on top of others.
        Original annotation is <class 'bool'>
        """,
    )
    edges: typing.Any = Field(
        False,
        description="""Show edges.
        Original annotation is <class 'bool'>
        """,
    )
    edges_width: typing.Any = Field(
        0.1,
        description="""Width of edges.
        Original annotation is <class 'float'>
        """,
    )
    edges_color: typing.Any = Field(
        "grey",
        description="""Color of edges.
        Original annotation is str | collections.abc.Sequence[float] | collections.abc.Sequence[str]
        """,
    )
    neighbors_key: str | None = Field(
        None,
        description="""Where to look for neighbors connectivities.
        Original annotation is str | None
        """,
    )
    arrows: typing.Any = Field(
        False,
        description="""Show arrows (deprecated in favour of `scvelo.pl.velocity_embedding`).
        Original annotation is <class 'bool'>
        """,
    )
    arrows_kwds: typing.Any = Field(
        None,
        description="""Passed to :meth:`~matplotlib.axes.Axes.quiver`
        Original annotation is collections.abc.Mapping[str, typing.Any] | None
        """,
    )
    groups: typing.Any = Field(
        None,
        description="""Restrict to a few categories in categorical observation annotation.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    components: typing.Any = Field(
        None,
        description="""For instance, `[\'1,2\', \'2,3\']`. To plot all available components use `components=\'all\'.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    dimensions: typing.Any = Field(
        None,
        description="""0-indexed dimensions of the embedding to plot as integers.
        Original annotation is tuple[int, int] | collections.abc.Sequence[tuple[int, int]] | None
        """,
    )
    layer: str | None = Field(
        None,
        description="""Name of the AnnData object layer that wants to be plotted.
        Original annotation is str | None
        """,
    )
    projection: typing.Any = Field(
        "2d",
        description="""Projection of plot (default: `\'2d\'`).
        Original annotation is typing.Literal['2d', '3d']
        """,
    )
    scale_factor: float | None = Field(
        None,
        description="""No description available.
        Original annotation is float | None
        """,
    )
    color_map: typing.Any = Field(
        None,
        description="""Color map to use for continuous variables.
        Original annotation is matplotlib.colors.Colormap | str | None
        """,
    )
    cmap: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is matplotlib.colors.Colormap | str | None
        """,
    )
    palette: typing.Any = Field(
        None,
        description="""Colors to use for plotting categorical annotation groups.
        Original annotation is str | collections.abc.Sequence[str] | cycler.Cycler | None
        """,
    )
    na_color: str | tuple[float, ...] = Field(
        "lightgray",
        description="""Color to use for null or masked values.
        Original annotation is str | tuple[float, ...]
        """,
    )
    na_in_legend: typing.Any = Field(
        True,
        description="""If there are missing values, whether they get an entry in the legend.
        Original annotation is <class 'bool'>
        """,
    )
    size: typing.Any = Field(
        None,
        description="""Point size.
        Original annotation is float | collections.abc.Sequence[float] | None
        """,
    )
    frameon: bool | None = Field(
        None,
        description="""Draw a frame around the scatter plot.
        Original annotation is bool | None
        """,
    )
    legend_fontsize: typing.Any = Field(
        None,
        description="""Numeric size in pt or string describing the size.
        Original annotation is typing.Union[float, typing.Literal['xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large'], NoneType]
        """,
    )
    legend_fontweight: typing.Any = Field(
        "bold",
        description="""Legend font weight.
        Original annotation is typing.Union[int, typing.Literal['light', 'normal', 'medium', 'semibold', 'bold', 'heavy', 'black']]
        """,
    )
    legend_loc: typing.Any = Field(
        "right margin",
        description="""Location of legend.
        Original annotation is typing.Optional[typing.Literal['none', 'right margin', 'on data', 'on data export', 'best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 'upper center', 'center']]
        """,
    )
    legend_fontoutline: int | None = Field(
        None,
        description="""Line width of the legend font outline in pt.
        Original annotation is int | None
        """,
    )
    colorbar_loc: str | None = Field(
        "right",
        description="""Where to place the colorbar for continuous variables.
        Original annotation is str | None
        """,
    )
    vmax: typing.Any = Field(
        None,
        description="""The value representing the upper limit of the color scale.
        Original annotation is str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float] | collections.abc.Sequence[str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float]] | None
        """,
    )
    vmin: typing.Any = Field(
        None,
        description="""The value representing the lower limit of the color scale.
        Original annotation is str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float] | collections.abc.Sequence[str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float]] | None
        """,
    )
    vcenter: typing.Any = Field(
        None,
        description="""The value representing the center of the color scale.
        Original annotation is str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float] | collections.abc.Sequence[str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float]] | None
        """,
    )
    norm: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is matplotlib.colors.Normalize | collections.abc.Sequence[matplotlib.colors.Normalize] | None
        """,
    )
    add_outline: bool | None = Field(
        False,
        description="""If set to True, this will add a thin border around groups of dots.
        Original annotation is bool | None
        """,
    )
    # outline_width: tuple[float, float] = Field(
    #     (0.3, 0.05),
    #     description="""Width numbers used to adjust the outline.
    #     Original annotation is tuple[float, float]
    #     """,
    # )
    # outline_color: tuple[str, str] = Field(
    #     ("black", "white"),
    #     description="""Valid color names used to adjust the add_outline.
    #     Original annotation is tuple[str, str]
    #     """,
    # )
    ncols: typing.Any = Field(
        4,
        description="""Number of panels per row.
        Original annotation is <class 'int'>
        """,
    )
    hspace: typing.Any = Field(
        0.25,
        description="""Adjust the height of the space between multiple panels.
        Original annotation is <class 'float'>
        """,
    )
    wspace: float | None = Field(
        None,
        description="""Adjust the width of the space between multiple panels.
        Original annotation is float | None
        """,
    )
    title: typing.Any = Field(
        None,
        description="""Provide title for panels.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: bool | str | None = Field(
        # None,
        True,
        description="""If `True` or a `str`, save the figure.
        Original annotation is bool | str | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""A matplotlib axes object.
        Original annotation is matplotlib.axes._axes.Axes | None
        """,
    )
    return_fig: bool | None = Field(
        None,
        description="""Return the matplotlib figure.
        Original annotation is bool | None
        """,
    )
    marker: typing.Any = Field(
        ".",
        description="""No description available.
        Original annotation is str | collections.abc.Sequence[str]
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.tsne")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlHeatmap(BaseAPI):
    """
    Heatmap of the expression values of genes with various customizable parameters such as ordering by groups, logarithmic axis, and dendrogram addition based on the hierarchical clustering.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix required for plotting the heatmap.
        """,
    )
    var_names: typing.Any = Field(
        Ellipsis,
        description="""Subset of `adata.var_names` used for grouping values, with options for coloring or \'brackets\' based on the plot.
        Original annotation is _VarNames | Mapping[str, _VarNames]
        """,
    )
    groupby: str | Sequence[str] = Field(
        Ellipsis,
        description="""Key of the observation grouping to consider for the heatmap.
        Original annotation is str | Sequence[str]
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""Decision to use the `raw` attribute of `adata` if available.
        Original annotation is bool | None
        """,
    )
    log: bool = Field(
        False,
        description="""Option to plot the heatmap on a logarithmic axis.
        Original annotation is bool
        """,
    )
    num_categories: int = Field(
        7,
        description="""Determines the number of groups to subdivide the groupby observation into if it\'s not categorical.
        Original annotation is int
        """,
    )
    dendrogram: bool | str = Field(
        False,
        description="""Adds a dendrogram based on hierarchical clustering between groupby categories if True or a valid dendrogram key.
        Original annotation is bool | str
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Column name in `.var` DataFrame that stores gene symbols, providing an alternative to default var_names.
        Original annotation is str | None
        """,
    )
    # var_group_positions: Sequence[tuple[int, int]] | None = Field(
    #     None,
    #     description="""Highlights groups of var_names with \'brackets\' or color blocks based on specified start and end positions.
    #     Original annotation is Sequence[tuple[int, int]] | None
    #     """,
    # )
    var_group_labels: typing.Any = Field(
        None,
        description="""Labels for each var_group_positions to be highlighted.
        Original annotation is Sequence[str] | None
        """,
    )
    var_group_rotation: float | None = Field(
        None,
        description="""Rotation degrees for labels, default is 90 degrees for labels larger than 4 characters.
        Original annotation is float | None
        """,
    )
    layer: str | None = Field(
        None,
        description="""Specifies the AnnData object layer to be plotted, with priority over `use_raw` if set to a valid layer name.
        Original annotation is str | None
        """,
    )
    standard_scale: Literal["var", "obs"] | None = Field(
        None,
        description="""Determines whether to standardize dimension between 0 and 1 by subtracting the minimum and dividing by the maximum.
        Original annotation is Literal['var', 'obs'] | None
        """,
    )
    swap_axes: bool = Field(
        False,
        description="""Switches the x and y axes in the heatmap, swapping `var_names` with `groupby` categories.
        Original annotation is bool
        """,
    )
    show_gene_labels: bool | None = Field(
        None,
        description="""Controls the display of gene labels based on the number of genes in the plot.
        Original annotation is bool | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Displays the plot without returning the axis.
        Original annotation is bool | None
        """,
    )
    save: str | bool | None = Field(
        # None,
        True,
        description="""Saves the figure if True or a string, with filetype inferred from the appended extension.
        Original annotation is str | bool | None
        """,
    )
    # figsize: tuple[float, float] | None = Field(
    #     None,
    #     description="""Figure size when `multi_panel=True`, otherwise uses default `rcParam[\'figure.figsize]` value.
    #     Original annotation is tuple[float, float] | None
    #     """,
    # )
    vmin: float | None = Field(
        None,
        description="""Lower limit of the color scale, values smaller than vmin are plotted with the same color as vmin.
        Original annotation is float | None
        """,
    )
    vmax: float | None = Field(
        None,
        description="""Upper limit of the color scale, values larger than vmax are plotted with the same color as vmax.
        Original annotation is float | None
        """,
    )
    vcenter: float | None = Field(
        None,
        description="""Center of the color scale, useful for diverging colormaps.
        Original annotation is float | None
        """,
    )
    norm: typing.Any = Field(
        None,
        description="""Custom color normalization object from matplotlib for the heatmap.
        Original annotation is Normalize | None
        """,
    )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""Additional parameters passed to `matplotlib.pyplot.imshow`.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.heatmap")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlDotplot(BaseAPI):
    """
    Make a dot plot of the expression values of var_names. Each dot represents mean expression within each category and fraction of cells expressing the var_name.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    var_names: typing.Any = Field(
        Ellipsis,
        description="""Subset of adata.var_names, used to group values. Can be a mapping with keys as labels and values as sequences of var_names.
        Original annotation is _VarNames | Mapping[str, _VarNames]
        """,
    )
    groupby: str | Sequence[str] = Field(
        Ellipsis,
        description="""Key of the observation grouping to consider.
        Original annotation is str | Sequence[str]
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""Use raw attribute of adata if present.
        Original annotation is bool | None
        """,
    )
    log: bool = Field(
        False,
        description="""Plot on a logarithmic axis.
        Original annotation is bool
        """,
    )
    num_categories: int = Field(
        7,
        description="""Determines the number of groups if groupby observation is not categorical.
        Original annotation is int
        """,
    )
    categories_order: typing.Any = Field(
        None,
        description="""Order in which to show the categories.
        Original annotation is Sequence[str] | None
        """,
    )
    expression_cutoff: float = Field(
        0.0,
        description="""Threshold used for binarizing gene expression.
        Original annotation is float
        """,
    )
    mean_only_expressed: bool = Field(
        False,
        description="""If True, average gene expression over cells expressing the gene.
        Original annotation is bool
        """,
    )
    standard_scale: typing.Any = Field(
        None,
        description="""Standardize dimension between 0 and 1.
        Original annotation is Literal['var', 'group'] | None
        """,
    )
    title: str | None = Field(
        None,
        description="""Title for the figure.
        Original annotation is str | None
        """,
    )
    colorbar_title: str | None = Field(
        "Mean expression in group",
        description="""Title for the color bar.
        Original annotation is str | None
        """,
    )
    size_title: str | None = Field(
        "Fraction of cells in group (%)",
        description="""Title for the size legend.
        Original annotation is str | None
        """,
    )
    # figsize: tuple[float, float] | None = Field(
    #     None,
    #     description="""Figure size, format: (width, height).
    #     Original annotation is tuple[float, float] | None
    #     """,
    # )
    dendrogram: bool | str = Field(
        False,
        description="""Add dendrogram based on hierarchical clustering between groupby categories.
        Original annotation is bool | str
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Column name in .var DataFrame that stores gene symbols.
        Original annotation is str | None
        """,
    )
    # var_group_positions: Sequence[tuple[int, int]] | None = Field(
    #     None,
    #     description="""Highlight groups of var_names with brackets or color blocks.
    #     Original annotation is Sequence[tuple[int, int]] | None
    #     """,
    # )
    var_group_labels: typing.Any = Field(
        None,
        description="""Labels for var_group_positions.
        Original annotation is Sequence[str] | None
        """,
    )
    var_group_rotation: float | None = Field(
        None,
        description="""Label rotation degrees.
        Original annotation is float | None
        """,
    )
    layer: str | None = Field(
        None,
        description="""Name of the AnnData object layer to plot.
        Original annotation is str | None
        """,
    )
    swap_axes: bool | None = Field(
        False,
        description="""Swap x and y axes.
        Original annotation is bool | None
        """,
    )
    dot_color_df: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is pd.DataFrame | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot without returning axes.
        Original annotation is bool | None
        """,
    )
    save: str | bool | None = Field(
        # None,
        True,
        description="""Save the figure if True or string.
        Original annotation is str | bool | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""Matplotlib axes object for plotting a single component.
        Original annotation is _AxesSubplot | None
        """,
    )
    return_fig: bool | None = Field(
        False,
        description="""Returns DotPlot object for fine-tuning the plot.
        Original annotation is bool | None
        """,
    )
    vmin: float | None = Field(
        None,
        description="""Lower limit of the color scale.
        Original annotation is float | None
        """,
    )
    vmax: float | None = Field(
        None,
        description="""Upper limit of the color scale.
        Original annotation is float | None
        """,
    )
    vcenter: float | None = Field(
        None,
        description="""Center of the color scale.
        Original annotation is float | None
        """,
    )
    norm: typing.Any = Field(
        None,
        description="""Custom color normalization object from matplotlib.
        Original annotation is Normalize | None
        """,
    )
    cmap: typing.Any = Field(
        "Reds",
        description="""Matplotlib color map.
        Original annotation is Colormap | str | None
        """,
    )
    dot_max: float | None = Field(
        None,
        description="""Maximum dot size for fraction value.
        Original annotation is float | None
        """,
    )
    dot_min: float | None = Field(
        None,
        description="""Minimum dot size for fraction value.
        Original annotation is float | None
        """,
    )
    smallest_dot: float = Field(
        0.0,
        description="""Size for expression levels with dot_min.
        Original annotation is float
        """,
    )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""Passed to matplotlib.pyplot.scatter.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.dotplot")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlViolin(BaseAPI):
    """
    Violin plot. Wraps seaborn.violinplot for AnnData. Parameters include adata, keys, groupby, log, use_raw, stripplot, jitter, size, layer, density_norm, order, multi_panel, xlabel, ylabel, rotation, show, save, ax, and kwds.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    keys: str | Sequence[str] = Field(
        Ellipsis,
        description="""Keys for accessing variables of .var_names or fields of .obs.
        Original annotation is str | Sequence[str]
        """,
    )
    groupby: str | None = Field(
        None,
        description="""The key of the observation grouping to consider.
        Original annotation is str | None
        """,
    )
    log: bool = Field(
        False,
        description="""Plot on logarithmic axis.
        Original annotation is bool
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""Whether to use raw attribute of adata. Defaults to True if .raw is present.
        Original annotation is bool | None
        """,
    )
    stripplot: bool = Field(
        True,
        description="""Add a stripplot on top of the violin plot.
        Original annotation is bool
        """,
    )
    jitter: float | bool = Field(
        True,
        description="""Add jitter to the stripplot (only when stripplot is True).
        Original annotation is float | bool
        """,
    )
    size: int = Field(
        1,
        description="""Size of the jitter points.
        Original annotation is int
        """,
    )
    layer: str | None = Field(
        None,
        description="""Name of the AnnData object layer that wants to be plotted. By default adata.raw.X is plotted. If use_raw=False, then adata.X is plotted. If layer is set to a valid layer name, then the layer is plotted. layer takes precedence over use_raw.
        Original annotation is str | None
        """,
    )
    density_norm: typing.Any = Field(
        "width",
        description="""Method used to scale the width of each violin. Options include width, area, and count.
        Original annotation is DensityNorm
        """,
    )
    order: typing.Any = Field(
        None,
        description="""Order in which to show the categories.
        Original annotation is Sequence[str] | None
        """,
    )
    multi_panel: bool | None = Field(
        None,
        description="""Display keys in multiple panels also when groupby is not None.
        Original annotation is bool | None
        """,
    )
    xlabel: str = Field(
        "",
        description="""Label of the x axis. Defaults to groupby if rotation is None, otherwise, no label is shown.
        Original annotation is str
        """,
    )
    ylabel: str | Sequence[str] | None = Field(
        None,
        description="""Label of the y axis. Defaults to \'value\' if groupby is None, otherwise defaults to keys.
        Original annotation is str | Sequence[str] | None
        """,
    )
    rotation: float | None = Field(
        None,
        description="""Rotation of xtick labels.
        Original annotation is float | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: bool | str | None = Field(
        # None,
        True,
        description="""If True or a str, save the figure. A string is appended to the default filename. Infer the filetype if ending on {\'.pdf\', \'.png\', \'.svg\'}.
        Original annotation is bool | str | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""A matplotlib axes object. Only works if plotting a single component.
        Original annotation is Axes | None
        """,
    )
    scale: typing.Any = Field(
        "Empty.token",
        description="""No description available.
        Original annotation is DensityNorm | Empty
        """,
    )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""No description available.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.violin")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlDendrogram(BaseAPI):
    """
    Plot a dendrogram of the categories defined in `groupby`. See :func:`~scanpy.tl.dendrogram`.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    groupby: str = Field(
        Ellipsis,
        description="""Categorical data column used to create the dendrogram.
        Original annotation is str
        """,
    )
    dendrogram_key: str | None = Field(
        None,
        description="""Key under with the dendrogram information was stored. By default stored under `.uns[f\'dendrogram_{groupby}\']`.
        Original annotation is str | None
        """,
    )
    orientation: typing.Any = Field(
        "top",
        description="""Origin of the tree. Will grow into the opposite direction.
        Original annotation is Literal['top', 'bottom', 'left', 'right']
        """,
    )
    remove_labels: bool = Field(
        False,
        description="""Don’t draw labels. Used e.g. by :func:`scanpy.pl.matrixplot` to annotate matrix columns/rows.
        Original annotation is bool
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: str | bool | None = Field(
        # None,
        True,
        description="""If `True` or a `str`, save the figure. A string is appended to the default filename. Infer the filetype if ending on {`\'.pdf\'`, `\'.png\'`, `\'.svg\'`}.
        Original annotation is str | bool | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""A matplotlib axes object. Only works if plotting a single component.
        Original annotation is Axes | None
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.dendrogram")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlDiffmap(BaseAPI):
    """
    Scatter plot in Diffusion Map basis.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    color: typing.Any = Field(
        None,
        description="""Keys for annotations of observations/cells or variables/genes, e.g., `\'ann1\'` or `[\'ann1\', \'ann2\']`.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    mask_obs: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool]] | str | None
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Column name in `.var` DataFrame that stores gene symbols. By default `var_names` refer to the index column of the `.var` DataFrame. Setting this option allows alternative names to be used.
        Original annotation is str | None
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""Use `.raw` attribute of `adata` for coloring with gene expression. If `None`, defaults to `True` if `layer` isn\'t provided and `adata.raw` is present.
        Original annotation is bool | None
        """,
    )
    sort_order: typing.Any = Field(
        True,
        description="""For continuous annotations used as color parameter, plot data points with higher values on top of others.
        Original annotation is <class 'bool'>
        """,
    )
    edges: typing.Any = Field(
        False,
        description="""No description available.
        Original annotation is <class 'bool'>
        """,
    )
    edges_width: typing.Any = Field(
        0.1,
        description="""No description available.
        Original annotation is <class 'float'>
        """,
    )
    edges_color: typing.Any = Field(
        "grey",
        description="""No description available.
        Original annotation is str | collections.abc.Sequence[float] | collections.abc.Sequence[str]
        """,
    )
    neighbors_key: str | None = Field(
        None,
        description="""No description available.
        Original annotation is str | None
        """,
    )
    arrows: typing.Any = Field(
        False,
        description="""No description available.
        Original annotation is <class 'bool'>
        """,
    )
    arrows_kwds: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is collections.abc.Mapping[str, typing.Any] | None
        """,
    )
    groups: typing.Any = Field(
        None,
        description="""Restrict to a few categories in categorical observation annotation. The default is not to restrict to any groups.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    components: typing.Any = Field(
        None,
        description="""For instance, `[\'1,2\', \'2,3\']`. To plot all available components use `components=\'all\'`.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    dimensions: typing.Any = Field(
        None,
        description="""0-indexed dimensions of the embedding to plot as integers. E.g. [(0, 1), (1, 2)]. Unlike `components`, this argument is used in the same way as `colors`, e.g. is used to specify a single plot at a time. Will eventually replace the components argument.
        Original annotation is tuple[int, int] | collections.abc.Sequence[tuple[int, int]] | None
        """,
    )
    layer: str | None = Field(
        None,
        description="""Name of the AnnData object layer that wants to be plotted. By default adata.raw.X is plotted. If `use_raw=False` is set, then `adata.X` is plotted. If `layer` is set to a valid layer name, then the layer is plotted. `layer` takes precedence over `use_raw`.
        Original annotation is str | None
        """,
    )
    projection: typing.Any = Field(
        "2d",
        description="""Projection of plot (default: `\'2d\'`).
        Original annotation is typing.Literal['2d', '3d']
        """,
    )
    scale_factor: float | None = Field(
        None,
        description="""No description available.
        Original annotation is float | None
        """,
    )
    color_map: typing.Any = Field(
        None,
        description="""Color map to use for continous variables. Can be a name or a :class:`~matplotlib.colors.Colormap` instance (e.g. `\"magma`\", `\"viridis\"` or `mpl.cm.cividis`), see :meth:`~matplotlib.cm.ColormapRegistry.get_cmap`. If `None`, the value of `mpl.rcParams[\"image.cmap\"]` is used. The default `color_map` can be set using :func:`~scanpy.set_figure_params`.
        Original annotation is matplotlib.colors.Colormap | str | None
        """,
    )
    cmap: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is matplotlib.colors.Colormap | str | None
        """,
    )
    palette: typing.Any = Field(
        None,
        description="""Colors to use for plotting categorical annotation groups. The palette can be a valid :class:`~matplotlib.colors.ListedColormap` name (`\'Set2\'`, `\'tab20\'`, …), a :class:`~cycler.Cycler` object, a dict mapping categories to colors, or a sequence of colors. Colors must be valid to matplotlib. (see :func:`~matplotlib.colors.is_color_like`). If `None`, `mpl.rcParams[\"axes.prop_cycle\"]` is used unless the categorical variable already has colors stored in `adata.uns[\"{var}_colors\"]`. If provided, values of `adata.uns[\"{var}_colors\"]` will be set.
        Original annotation is str | collections.abc.Sequence[str] | cycler.Cycler | None
        """,
    )
    na_color: str | tuple[float, ...] = Field(
        "lightgray",
        description="""Color to use for null or masked values. Can be anything matplotlib accepts as a color. Used for all points if `color=None`.
        Original annotation is str | tuple[float, ...]
        """,
    )
    na_in_legend: typing.Any = Field(
        True,
        description="""If there are missing values, whether they get an entry in the legend. Currently only implemented for categorical legends.
        Original annotation is <class 'bool'>
        """,
    )
    size: typing.Any = Field(
        None,
        description="""Point size. If `None`, is automatically computed as 120000 / n_cells. Can be a sequence containing the size for each cell. The order should be the same as in adata.obs.
        Original annotation is float | collections.abc.Sequence[float] | None
        """,
    )
    frameon: bool | None = Field(
        None,
        description="""Draw a frame around the scatter plot. Defaults to value set in :func:`~scanpy.set_figure_params`, defaults to `True`.
        Original annotation is bool | None
        """,
    )
    legend_fontsize: typing.Union[
        float,
        typing.Literal[
            "xx-small", "x-small", "small", "medium", "large", "x-large", "xx-large"
        ],
        None,
    ] = Field(
        None,
        description="""Numeric size in pt or string describing the size. See :meth:`~matplotlib.text.Text.set_fontsize`.
        Original annotation is typing.Union[float, typing.Literal['xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large'], NoneType]
        """,
    )
    legend_fontweight: typing.Any = Field(
        "bold",
        description="""Legend font weight. A numeric value in range 0-1000 or a string. Defaults to `\'bold\'` if `legend_loc == \'on data\'`, otherwise to `\'normal\'`. See :meth:`~matplotlib.text.Text.set_fontweight`.
        Original annotation is typing.Union[int, typing.Literal['light', 'normal', 'medium', 'semibold', 'bold', 'heavy', 'black']]
        """,
    )
    legend_loc: typing.Any = Field(
        "right margin",
        description="""Location of legend, either `\'on data\'`, `\'right margin\'`, `None`, or a valid keyword for the `loc` parameter of :class:`~matplotlib.legend.Legend`.
        Original annotation is typing.Optional[typing.Literal['none', 'right margin', 'on data', 'on data export', 'best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 'upper center', 'center']]
        """,
    )
    legend_fontoutline: int | None = Field(
        None,
        description="""Line width of the legend font outline in pt. Draws a white outline using the path effect :class:`~matplotlib.patheffects.withStroke`.
        Original annotation is int | None
        """,
    )
    colorbar_loc: str | None = Field(
        "right",
        description="""Where to place the colorbar for continous variables. If `None`, no colorbar is added.
        Original annotation is str | None
        """,
    )
    vmax: typing.Any = Field(
        None,
        description="""The value representing the upper limit of the color scale. The format is the same as for `vmin`.
        Original annotation is str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float] | collections.abc.Sequence[str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float]] | None
        """,
    )
    vmin: typing.Any = Field(
        None,
        description="""The value representing the lower limit of the color scale. Values smaller than vmin are plotted with the same color as vmin. vmin can be a number, a string, a function or `None`. If vmin is a string and has the format `pN`, this is interpreted as a vmin=percentile(N). For example vmin=\'p1.5\' is interpreted as the 1.5 percentile. If vmin is function, then vmin is interpreted as the return value of the function over the list of values to plot. For example to set vmin tp the mean of the values to plot, `def my_vmin(values): return np.mean(values)` and then set `vmin=my_vmin`. If vmin is None (default) an automatic minimum value is used as defined by matplotlib `scatter` function. When making multiple plots, vmin can be a list of values, one for each plot. For example `vmin=[0.1, \'p1\', None, my_vmin]`
        Original annotation is str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float] | collections.abc.Sequence[str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float]] | None
        """,
    )
    vcenter: typing.Any = Field(
        None,
        description="""The value representing the center of the color scale. Useful for diverging colormaps. The format is the same as for `vmin`. Example: ``sc.pl.umap(adata, color=\'TREM2\', vcenter=\'p50\', cmap=\'RdBu_r\')``
        Original annotation is str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float] | collections.abc.Sequence[str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float]] | None
        """,
    )
    norm: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is matplotlib.colors.Normalize | collections.abc.Sequence[matplotlib.colors.Normalize] | None
        """,
    )
    add_outline: bool | None = Field(
        False,
        description="""If set to True, this will add a thin border around groups of dots. In some situations this can enhance the aesthetics of the resulting image
        Original annotation is bool | None
        """,
    )
    # outline_width: tuple[float, float] = Field(
    #     (0.3, 0.05),
    #     description="""Tuple with two width numbers used to adjust the outline. The first value is the width of the border color as a fraction of the scatter dot size (default: 0.3). The second value is width of the gap color (default: 0.05).
    #     Original annotation is tuple[float, float]
    #     """,
    # )
    # outline_color: tuple[str, str] = Field(
    #     ("black", "white"),
    #     description="""Tuple with two valid color names used to adjust the add_outline. The first color is the border color (default: black), while the second color is a gap color between the border color and the scatter dot (default: white).
    #     Original annotation is tuple[str, str]
    #     """,
    # )
    ncols: typing.Any = Field(
        4,
        description="""Number of panels per row.
        Original annotation is <class 'int'>
        """,
    )
    hspace: typing.Any = Field(
        0.25,
        description="""Adjust the height of the space between multiple panels.
        Original annotation is <class 'float'>
        """,
    )
    wspace: float | None = Field(
        None,
        description="""Adjust the width of the space between multiple panels.
        Original annotation is float | None
        """,
    )
    title: typing.Any = Field(
        None,
        description="""Provide title for panels either as string or list of strings, e.g. `[\'title1\', \'title2\', ...]`.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: bool | str | None = Field(
        # None,
        True,
        description="""If `True` or a `str`, save the figure. A string is appended to the default filename. Infer the filetype if ending on {`\'.pdf\'`, `\'.png\'`, `\'.svg\'`}.
        Original annotation is bool | str | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""A matplotlib axes object. Only works if plotting a single component.
        Original annotation is matplotlib.axes._axes.Axes | None
        """,
    )
    return_fig: bool | None = Field(
        None,
        description="""Return the matplotlib figure.
        Original annotation is bool | None
        """,
    )
    marker: typing.Any = Field(
        ".",
        description="""No description available.
        Original annotation is str | collections.abc.Sequence[str]
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.diffmap")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlHighlyVariableGenes(BaseAPI):
    """
    Plot dispersions or normalized variance versus means for genes. Produces Supp. Fig. 5c of Zheng et al. (2017) and MeanVarPlot() and VariableFeaturePlot() of Seurat.
    """

    adata_or_result: typing.Any = Field(
        Ellipsis,
        description="""No description available.
        Original annotation is AnnData | pd.DataFrame | np.recarray
        """,
    )
    log: bool = Field(
        False,
        description="""Plot on logarithmic axes.
        Original annotation is bool
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: bool | str | None = Field(
        # None,
        True,
        description="""If `True` or a `str`, save the figure. A string is appended to the default filename. Infer the filetype if ending on {\'.pdf\', \'.png\', \'.svg\'}.
        Original annotation is bool | str | None
        """,
    )
    highly_variable_genes: bool = Field(
        True,
        description="""No description available.
        Original annotation is bool
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.highly_variable_genes")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlPca(BaseAPI):
    """
    Scatter plot in PCA coordinates. Use the parameter `annotate_var_explained` to annotate the explained variance.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    color: typing.Any = Field(
        None,
        description="""Keys for annotations of observations/cells or variables/genes.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    mask_obs: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool]] | str | None
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Column name in `.var` DataFrame that stores gene symbols.
        Original annotation is str | None
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""Use `.raw` attribute of `adata` for coloring with gene expression.
        Original annotation is bool | None
        """,
    )
    sort_order: typing.Any = Field(
        True,
        description="""For continuous annotations used as color parameter, plot data points with higher values on top of others.
        Original annotation is <class 'bool'>
        """,
    )
    edges: typing.Any = Field(
        False,
        description="""No description available.
        Original annotation is <class 'bool'>
        """,
    )
    edges_width: typing.Any = Field(
        0.1,
        description="""No description available.
        Original annotation is <class 'float'>
        """,
    )
    edges_color: typing.Any = Field(
        "grey",
        description="""No description available.
        Original annotation is str | collections.abc.Sequence[float] | collections.abc.Sequence[str]
        """,
    )
    neighbors_key: str | None = Field(
        None,
        description="""No description available.
        Original annotation is str | None
        """,
    )
    arrows: typing.Any = Field(
        False,
        description="""No description available.
        Original annotation is <class 'bool'>
        """,
    )
    arrows_kwds: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is collections.abc.Mapping[str, typing.Any] | None
        """,
    )
    groups: typing.Any = Field(
        None,
        description="""Restrict to a few categories in categorical observation annotation.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    components: typing.Any = Field(
        None,
        description="""Specify components for plotting.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    dimensions: typing.Any = Field(
        None,
        description="""0-indexed dimensions of the embedding to plot as integers.
        Original annotation is tuple[int, int] | collections.abc.Sequence[tuple[int, int]] | None
        """,
    )
    layer: str | None = Field(
        None,
        description="""Name of the AnnData object layer that wants to be plotted.
        Original annotation is str | None
        """,
    )
    projection: typing.Any = Field(
        "2d",
        description="""Projection of plot.
        Original annotation is typing.Literal['2d', '3d']
        """,
    )
    scale_factor: float | None = Field(
        None,
        description="""No description available.
        Original annotation is float | None
        """,
    )
    color_map: typing.Any = Field(
        None,
        description="""Color map to use for continuous variables.
        Original annotation is matplotlib.colors.Colormap | str | None
        """,
    )
    cmap: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is matplotlib.colors.Colormap | str | None
        """,
    )
    palette: typing.Any = Field(
        None,
        description="""Colors to use for plotting categorical annotation groups.
        Original annotation is str | collections.abc.Sequence[str] | cycler.Cycler | None
        """,
    )
    na_color: str | tuple[float, ...] = Field(
        "lightgray",
        description="""Color to use for null or masked values.
        Original annotation is str | tuple[float, ...]
        """,
    )
    na_in_legend: typing.Any = Field(
        True,
        description="""Whether missing values get an entry in the legend.
        Original annotation is <class 'bool'>
        """,
    )
    size: typing.Any = Field(
        None,
        description="""Point size.
        Original annotation is float | collections.abc.Sequence[float] | None
        """,
    )
    frameon: bool | None = Field(
        None,
        description="""Draw a frame around the scatter plot.
        Original annotation is bool | None
        """,
    )
    legend_fontsize: typing.Any = Field(
        None,
        description="""Numeric size in pt or string describing the size.
        Original annotation is typing.Union[float, typing.Literal['xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large'], NoneType]
        """,
    )
    legend_fontweight: typing.Any = Field(
        "bold",
        description="""Legend font weight.
        Original annotation is typing.Union[int, typing.Literal['light', 'normal', 'medium', 'semibold', 'bold', 'heavy', 'black']]
        """,
    )
    legend_loc: typing.Any = Field(
        "right margin",
        description="""Location of legend.
        Original annotation is typing.Optional[typing.Literal['none', 'right margin', 'on data', 'on data export', 'best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 'upper center', 'center']]
        """,
    )
    legend_fontoutline: int | None = Field(
        None,
        description="""Line width of the legend font outline.
        Original annotation is int | None
        """,
    )
    colorbar_loc: str | None = Field(
        "right",
        description="""Where to place the colorbar for continuous variables.
        Original annotation is str | None
        """,
    )
    vmax: typing.Any = Field(
        None,
        description="""The upper limit of the color scale.
        Original annotation is str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float] | collections.abc.Sequence[str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float]] | None
        """,
    )
    vmin: typing.Any = Field(
        None,
        description="""The lower limit of the color scale.
        Original annotation is str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float] | collections.abc.Sequence[str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float]] | None
        """,
    )
    vcenter: typing.Any = Field(
        None,
        description="""The center of the color scale.
        Original annotation is str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float] | collections.abc.Sequence[str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float]] | None
        """,
    )
    norm: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is matplotlib.colors.Normalize | collections.abc.Sequence[matplotlib.colors.Normalize] | None
        """,
    )
    add_outline: bool | None = Field(
        False,
        description="""Add a thin border around groups of dots.
        Original annotation is bool | None
        """,
    )
    # outline_width: tuple[float, float] = Field(
    #     (0.3, 0.05),
    #     description="""Width numbers used to adjust the outline.
    #     Original annotation is tuple[float, float]
    #     """,
    # )
    # outline_color: tuple[str, str] = Field(
    #     ("black", "white"),
    #     description="""Valid color names used to adjust the add_outline.
    #     Original annotation is tuple[str, str]
    #     """,
    # )
    ncols: typing.Any = Field(
        4,
        description="""Number of panels per row.
        Original annotation is <class 'int'>
        """,
    )
    hspace: typing.Any = Field(
        0.25,
        description="""Height of the space between multiple panels.
        Original annotation is <class 'float'>
        """,
    )
    wspace: float | None = Field(
        None,
        description="""Width of the space between multiple panels.
        Original annotation is float | None
        """,
    )
    title: typing.Any = Field(
        None,
        description="""Provide title for panels.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot.
        Original annotation is bool | None
        """,
    )
    save: bool | str | None = Field(
        # None,
        True,
        description="""Save the figure.
        Original annotation is bool | str | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""A matplotlib axes object.
        Original annotation is matplotlib.axes._axes.Axes | None
        """,
    )
    return_fig: bool | None = Field(
        None,
        description="""Return the matplotlib figure.
        Original annotation is bool | None
        """,
    )
    marker: typing.Any = Field(
        ".",
        description="""No description available.
        Original annotation is str | collections.abc.Sequence[str]
        """,
    )
    annotate_var_explained: typing.Any = Field(
        False,
        description="""No description available.
        Original annotation is <class 'bool'>
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.pca")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlEmbeddingDensity(BaseAPI):
    """
    Plot the density of cells in an embedding (per condition) by using gaussian kernel density estimates from the `sc.tl.embedding_density()` output.
    """

    adata: str = Field(
        "data",
        description="""The annotated data matrix.
        """,
    )
    basis: str = Field(
        "umap",
        description="""The embedding over which the density was calculated, found in `adata.obsm[\'X_[basis]\']`.
        Original annotation is str
        """,
    )
    key: str | None = Field(
        None,
        description="""Name of the `.obs` covariate that contains the density estimates or pass `groupby`.
        Original annotation is str | None
        """,
    )
    groupby: str | None = Field(
        None,
        description="""Name of the condition used in `tl.embedding_density` or pass `key`.
        Original annotation is str | None
        """,
    )
    group: str | Sequence[str] | None = Field(
        "all",
        description="""Category in the categorical observation annotation to be plotted, with options for different groupings and color representation.
        Original annotation is str | Sequence[str] | None
        """,
    )
    color_map: typing.Any = Field(
        "YlOrRd",
        description="""Matplotlib color map used for density plotting.
        Original annotation is Colormap | str
        """,
    )
    bg_dotsize: int | None = Field(
        80,
        description="""Dot size for background data points not in the `group`.
        Original annotation is int | None
        """,
    )
    fg_dotsize: int | None = Field(
        180,
        description="""Dot size for foreground data points in the `group`.
        Original annotation is int | None
        """,
    )
    vmax: int | None = Field(
        1,
        description="""The upper limit of the color scale for density representation.
        Original annotation is int | None
        """,
    )
    vmin: int | None = Field(
        0,
        description="""The lower limit of the color scale for density representation, with various options for customization such as using percentiles or functions.
        Original annotation is int | None
        """,
    )
    vcenter: int | None = Field(
        None,
        description="""The center value of the color scale, useful for diverging colormaps.
        Original annotation is int | None
        """,
    )
    norm: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is Normalize | None
        """,
    )
    ncols: int | None = Field(
        4,
        description="""Number of panels per row for visualization.
        Original annotation is int | None
        """,
    )
    hspace: float | None = Field(
        0.25,
        description="""Adjust the height of the space between multiple panels.
        Original annotation is float | None
        """,
    )
    wspace: typing.Any = Field(
        None,
        description="""Adjust the width of the space between multiple panels.
        Original annotation is None
        """,
    )
    title: str | None = Field(
        None,
        description="""No description available.
        Original annotation is str | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot without returning axis.
        Original annotation is bool | None
        """,
    )
    save: bool | str | None = Field(
        True,
        description="""Save the figure if `True` or a `str`, with inferred filetype based on extension.
        Original annotation is bool | str | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""Matplotlib axes object, works when plotting a single component.
        Original annotation is Axes | None
        """,
    )
    return_fig: bool | None = Field(
        None,
        description="""Return the matplotlib figure.
        Original annotation is bool | None
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.embedding_density")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlRankGenesGroups(BaseAPI):
    """
    Plot ranking of genes. Annotated data matrix. The groups for which to show the gene ranking. Key for field in `.var` that stores gene symbols if you do not want to use `.var_names`. Number of genes to show. Fontsize for gene names. Number of panels shown per row. Controls if the y-axis of each panels should be shared. Show the plot, do not return axis. If `True` or a `str`, save the figure. A string is appended to the default filename. Infer the filetype if ending on {`\'.pdf\'`, `\'.png\'`, `\'.svg\'`}. A matplotlib axes object. Only works if plotting a single component.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    groups: typing.Any = Field(
        None,
        description="""The groups for which to show the gene ranking.
        Original annotation is str | Sequence[str] | None
        """,
    )
    n_genes: int = Field(
        20,
        description="""Number of genes to show.
        Original annotation is int
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Key for field in `.var` that stores gene symbols if you do not want to use `.var_names`.
        Original annotation is str | None
        """,
    )
    key: str | None = Field(
        "rank_genes_groups",
        description="""No description available.
        Original annotation is str | None
        """,
    )
    fontsize: int = Field(
        8,
        description="""Fontsize for gene names.
        Original annotation is int
        """,
    )
    ncols: int = Field(
        4,
        description="""Number of panels shown per row.
        Original annotation is int
        """,
    )
    sharey: bool = Field(
        True,
        description="""Controls if the y-axis of each panels should be shared. But passing `sharey=False`, each panel has its own y-axis range.
        Original annotation is bool
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: bool | None = Field(
        # None,
        True,
        description="""If `True` or a `str`, save the figure. A string is appended to the default filename. Infer the filetype if ending on {`\'.pdf\'`, `\'.png\'`, `\'.svg\'`}.
        Original annotation is bool | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""A matplotlib axes object. Only works if plotting a single component.
        Original annotation is Axes | None
        """,
    )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""No description available.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.rank_genes_groups")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlRankGenesGroupsDotplot(BaseAPI):
    """
    Plot ranking of genes using dotplot plot.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    groups: str | Sequence[str] | None = Field(
        None,
        description="""The groups for which to show the gene ranking.
        Original annotation is str | Sequence[str] | None
        """,
    )
    n_genes: int | None = Field(
        None,
        description="""Number of genes to show, can be negative to indicate downregulated genes.
        Original annotation is int | None
        """,
    )
    groupby: str | None = Field(
        None,
        description="""Key of the observation grouping to consider, expected to be categorical.
        Original annotation is str | None
        """,
    )
    values_to_plot: typing.Any = Field(
        None,
        description="""Plot values computed by `sc.rank_genes_groups` instead of mean gene value.
        Original annotation is Literal['scores', 'logfoldchanges', 'pvals', 'pvals_adj', 'log10_pvals', 'log10_pvals_adj'] | None
        """,
    )
    var_names: typing.Any = Field(
        None,
        description="""Genes to plot, can be a specific list or dictionary.
        Original annotation is Sequence[str] | Mapping[str, Sequence[str]] | None
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Column name in `.var` DataFrame storing gene symbols.
        Original annotation is str | None
        """,
    )
    min_logfoldchange: float | None = Field(
        None,
        description="""Value to filter genes based on logfoldchange.
        Original annotation is float | None
        """,
    )
    key: str | None = Field(
        None,
        description="""Key used to store ranking results in `adata.uns`.
        Original annotation is str | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot without returning axis.
        Original annotation is bool | None
        """,
    )
    save: bool | None = Field(
        # None,
        True,
        description="""Save the figure with inferred filetype.
        Original annotation is bool | None
        """,
    )
    return_fig: bool = Field(
        False,
        description="""Returns `DotPlot` object, useful for fine-tuning the plot.
        Original annotation is bool
        """,
    )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""Additional parameters passed to `scanpy.pl.dotplot`.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.rank_genes_groups_dotplot")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlRankGenesGroupsViolin(BaseAPI):
    """
    Plot ranking of genes for all tested comparisons.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    groups: typing.Any = Field(
        None,
        description="""List of group names.
        Original annotation is Sequence[str] | None
        """,
    )
    n_genes: int = Field(
        20,
        description="""Number of genes to show. Is ignored if `gene_names` is passed.
        Original annotation is int
        """,
    )
    gene_names: Iterable[str] | None = Field(
        None,
        description="""List of genes to plot. Is only useful if interested in a custom gene list, which is not the result of :func:`scanpy.tl.rank_genes_groups`.
        Original annotation is Iterable[str] | None
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Key for field in `.var` that stores gene symbols if you do not want to use `.var_names` displayed in the plot.
        Original annotation is str | None
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""Use `raw` attribute of `adata` if present. Defaults to the value that was used in :func:`~scanpy.tl.rank_genes_groups`.
        Original annotation is bool | None
        """,
    )
    key: str | None = Field(
        None,
        description="""No description available.
        Original annotation is str | None
        """,
    )
    split: bool = Field(
        True,
        description="""Whether to split the violins or not.
        Original annotation is bool
        """,
    )
    density_norm: typing.Any = Field(
        "width",
        description="""See :func:`~seaborn.violinplot`.
        Original annotation is DensityNorm
        """,
    )
    strip: bool = Field(
        True,
        description="""Show a strip plot on top of the violin plot.
        Original annotation is bool
        """,
    )
    jitter: float | bool = Field(
        True,
        description="""If set to 0, no points are drawn. See :func:`~seaborn.stripplot`.
        Original annotation is float | bool
        """,
    )
    size: int = Field(
        1,
        description="""Size of the jitter points.
        Original annotation is int
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""A matplotlib axes object. Only works if plotting a single component.
        Original annotation is Axes | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: bool | None = Field(
        # None,
        True,
        description="""If `True` or a `str`, save the figure. A string is appended to the default filename. Infer the filetype if ending on {`\'.pdf\'`, `\'.png\'`, `\'.svg\'`}.
        Original annotation is bool | None
        """,
    )
    scale: typing.Any = Field(
        "Empty.token",
        description="""No description available.
        Original annotation is DensityNorm | Empty
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.rank_genes_groups_violin")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlRankGenesGroupsHeatmap(BaseAPI):
    """
    Plot ranking of genes using heatmap plot (see :func:`~scanpy.pl.heatmap`).
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    groups: typing.Any = Field(
        None,
        description="""The groups for which to show the gene ranking.
        Original annotation is str | Sequence[str] | None
        """,
    )
    n_genes: int | None = Field(
        None,
        description="""Number of genes to show. This can be a negative number to show for example the down regulated genes. eg: num_genes=-10. Is ignored if `gene_names` is passed.
        Original annotation is int | None
        """,
    )
    groupby: str | None = Field(
        None,
        description="""The key of the observation grouping to consider. By default, the groupby is chosen from the rank genes groups parameter but other groupby options can be used. It is expected that groupby is a categorical. If groupby is not a categorical observation, it would be subdivided into `num_categories` (see :func:`~scanpy.pl.dotplot`)
        Original annotation is str | None
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Column name in `.var` DataFrame that stores gene symbols. By default `var_names` refer to the index column of the `.var` DataFrame. Setting this option allows alternative names to be used.
        Original annotation is str | None
        """,
    )
    var_names: Sequence[str] | Mapping[str, Sequence[str]] | None = Field(
        None,
        description="""No description available.
        Original annotation is Sequence[str] | Mapping[str, Sequence[str]] | None
        """,
    )
    min_logfoldchange: float | None = Field(
        None,
        description="""Value to filter genes in groups if their logfoldchange is less than the min_logfoldchange
        Original annotation is float | None
        """,
    )
    key: str | None = Field(
        None,
        description="""Key used to store the ranking results in `adata.uns`.
        Original annotation is str | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: bool | None = Field(
        # None,
        True,
        description="""If `True` or a `str`, save the figure. A string is appended to the default filename. Infer the filetype if ending on {`\'.pdf\'`, `\'.png\'`, `\'.svg\'`}.
        Original annotation is bool | None
        """,
    )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""No description available.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.rank_genes_groups_heatmap")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlRankGenesGroupsStackedViolin(BaseAPI):
    """
    Plot ranking of genes using stacked_violin plot.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    groups: str | Sequence[str] | None = Field(
        None,
        description="""The groups for which to show the gene ranking.
        Original annotation is str | Sequence[str] | None
        """,
    )
    n_genes: int | None = Field(
        None,
        description="""Number of genes to show, with the option to show down regulated genes.
        Original annotation is int | None
        """,
    )
    groupby: str | None = Field(
        None,
        description="""The key of the observation grouping to consider, typically a categorical variable.
        Original annotation is str | None
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Column name in `.var` DataFrame that stores gene symbols, allowing alternative names to be used.
        Original annotation is str | None
        """,
    )
    var_names: Sequence[str] | Mapping[str, Sequence[str]] | None = Field(
        None,
        description="""No description available.
        Original annotation is Sequence[str] | Mapping[str, Sequence[str]] | None
        """,
    )
    min_logfoldchange: float | None = Field(
        None,
        description="""Value to filter genes in groups based on their logfoldchange.
        Original annotation is float | None
        """,
    )
    key: str | None = Field(
        None,
        description="""Key used to store the ranking results in `adata.uns`.
        Original annotation is str | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot without returning the axis.
        Original annotation is bool | None
        """,
    )
    save: bool | None = Field(
        # None,
        True,
        description="""Option to save the figure, with automatic file type inference from the filename.
        Original annotation is bool | None
        """,
    )
    return_fig: bool = Field(
        False,
        description="""Returns a `StackedViolin` object, useful for fine-tuning the plot and takes precedence over `show=False`.
        Original annotation is bool
        """,
    )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""No description available.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.rank_genes_groups_stacked_violin")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlRankGenesGroupsMatrixplot(BaseAPI):
    """
    Plot ranking of genes using matrixplot plot (see :func:`~scanpy.pl.matrixplot`). Parameters and examples are provided in the description.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    groups: typing.Any = Field(
        None,
        description="""The groups for which to show the gene ranking.
        Original annotation is str | Sequence[str] | None
        """,
    )
    n_genes: int | None = Field(
        None,
        description="""Number of genes to show. This can be a negative number to show for example the down regulated genes.
        Original annotation is int | None
        """,
    )
    groupby: str | None = Field(
        None,
        description="""The key of the observation grouping to consider. By default, the groupby is chosen from the rank genes groups parameter but other groupby options can be used.
        Original annotation is str | None
        """,
    )
    values_to_plot: typing.Any = Field(
        None,
        description="""Instead of the mean gene value, plot the values computed by `sc.rank_genes_groups`. Options are provided for different values to plot.
        Original annotation is Literal['scores', 'logfoldchanges', 'pvals', 'pvals_adj', 'log10_pvals', 'log10_pvals_adj'] | None
        """,
    )
    var_names: typing.Any = Field(
        None,
        description="""Genes to plot. Sometimes is useful to pass a specific list of var names to check their fold changes or p-values.
        Original annotation is Sequence[str] | Mapping[str, Sequence[str]] | None
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Column name in `.var` DataFrame that stores gene symbols. Allows alternative names to be used.
        Original annotation is str | None
        """,
    )
    min_logfoldchange: float | None = Field(
        None,
        description="""Value to filter genes in groups if their logfoldchange is less than the min_logfoldchange.
        Original annotation is float | None
        """,
    )
    key: str | None = Field(
        None,
        description="""Key used to store the ranking results in `adata.uns`.
        Original annotation is str | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: bool | None = Field(
        # None,
        True,
        description="""If `True` or a `str`, save the figure with inferred filetype.
        Original annotation is bool | None
        """,
    )
    return_fig: bool = Field(
        False,
        description="""Returns :class:`MatrixPlot` object. Useful for fine-tuning the plot. Takes precedence over `show=False`.
        Original annotation is bool
        """,
    )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""No description available.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.rank_genes_groups_matrixplot")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlRankGenesGroupsTracksplot(BaseAPI):
    """
    Plot ranking of genes using heatmap plot (see :func:`~scanpy.pl.heatmap`).
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    groups: str | Sequence[str] | None = Field(
        None,
        description="""The groups for which to show the gene ranking.
        Original annotation is str | Sequence[str] | None
        """,
    )
    n_genes: int | None = Field(
        None,
        description="""Number of genes to show. This can be a negative number to show for example the down regulated genes. Is ignored if `gene_names` is passed.
        Original annotation is int | None
        """,
    )
    groupby: str | None = Field(
        None,
        description="""The key of the observation grouping to consider. By default, the groupby is chosen from the rank genes groups parameter but other groupby options can be used.
        Original annotation is str | None
        """,
    )
    var_names: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is Sequence[str] | Mapping[str, Sequence[str]] | None
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Column name in `.var` DataFrame that stores gene symbols. By default `var_names` refer to the index column of the `.var` DataFrame. Setting this option allows alternative names to be used.
        Original annotation is str | None
        """,
    )
    min_logfoldchange: float | None = Field(
        None,
        description="""Value to filter genes in groups if their logfoldchange is less than the min_logfoldchange
        Original annotation is float | None
        """,
    )
    key: str | None = Field(
        None,
        description="""Key used to store the ranking results in `adata.uns`.
        Original annotation is str | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: bool | None = Field(
        # None,
        True,
        description="""If `True` or a `str`, save the figure. A string is appended to the default filename. Infer the filetype if ending on {`\'.pdf\'`, `\'.png\'`, `\'.svg\'`}.
        Original annotation is bool | None
        """,
    )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""No description available.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.rank_genes_groups_tracksplot")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlHighestExprGenes(BaseAPI):
    """
    Fraction of counts assigned to each gene over all cells.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    n_top: int = Field(
        30,
        description="""Number of top
        Original annotation is int
        """,
    )
    layer: str | None = Field(
        None,
        description="""Layer from which to pull data.
        Original annotation is str | None
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Key for field in .var that stores gene symbols if you do not want to use .var_names.
        Original annotation is str | None
        """,
    )
    log: bool = Field(
        False,
        description="""Plot x-axis in log scale
        Original annotation is bool
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: str | bool | None = Field(
        # None,
        True,
        description="""If `True` or a `str`, save the figure. A string is appended to the default filename. Infer the filetype if ending on {`\'.pdf\'`, `\'.png\'`, `\'.svg\'`}.
        Original annotation is str | bool | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""A matplotlib axes object. Only works if plotting a single component.
        Original annotation is Axes | None
        """,
    )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""No description available.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.highest_expr_genes")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlTracksplot(BaseAPI):
    """
    Compact plot of expression of a list of genes. Parameters such as `groupby`, `use_raw`, and `log` are crucial for obtaining the best results. Additionally, features like `dendrogram` and `var_group_positions` can provide valuable insights into the data structure.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix containing the data to be visualized.
        """,
    )
    var_names: typing.Any = Field(
        Ellipsis,
        description="""Defines the genes or features to be plotted, either as a list or a mapping that allows for grouping. It includes options to customize the visualization based on these groupings.
        Original annotation is _VarNames | Mapping[str, _VarNames]
        """,
    )
    groupby: str = Field(
        Ellipsis,
        description="""Specifies the key for grouping the observations in the plot.
        Original annotation is str
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""Determines whether to use raw data for plotting, if available.
        Original annotation is bool | None
        """,
    )
    log: bool = Field(
        False,
        description="""Specifies whether to plot the data on a logarithmic scale.
        Original annotation is bool
        """,
    )
    dendrogram: bool | str = Field(
        False,
        description="""Controls the addition of a dendrogram based on hierarchical clustering of the groupby categories.
        Original annotation is bool | str
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Column name in the dataset that stores gene symbols, allowing for alternative names to be used in the visualization.
        Original annotation is str | None
        """,
    )
    # var_group_positions: Sequence[tuple[int, int]] | None = Field(
    #     None,
    #     description="""Highlights specified groups of var_names by adding brackets or color blocks between the given positions. Labels can be added for clarity.
    #     Original annotation is Sequence[tuple[int, int]] | None
    #     """,
    # )
    var_group_labels: typing.Any = Field(
        None,
        description="""Provides labels for the var_group_positions to be highlighted in the plot.
        Original annotation is Sequence[str] | None
        """,
    )
    layer: str | None = Field(
        None,
        description="""Defines the specific layer of the data to be plotted, with options to prioritize a particular layer over the raw data.
        Original annotation is str | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Specifies whether to display the plot or just return the axis object.
        Original annotation is bool | None
        """,
    )
    save: str | bool | None = Field(
        True,
        description="""Controls the saving of the figure, with options to specify the file type and filename.
        Original annotation is str | bool | None
        """,
    )
    # figsize: tuple[float, float] | None = Field(
    #     None,
    #     description="""Determines the size of the figure when `multi_panel=True`, otherwise defaults to the standard figure size.
    #     Original annotation is tuple[float, float] | None
    #     """,
    # )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""Additional keyword arguments that are passed to the plotting function.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.tracksplot")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlClustermap(BaseAPI):
    """
    Hierarchically-clustered heatmap. Wraps :func:`seaborn.clustermap` for :class:`~anndata.AnnData`.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    obs_keys: str | None = Field(
        None,
        description="""Categorical annotation to plot with a different color map. Currently, only a single key is supported.
        Original annotation is str | None
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""Whether to use `raw` attribute of `adata`. Defaults to `True` if `.raw` is present.
        Original annotation is bool | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: bool | str | None = Field(
        # None,
        True,
        description="""If `True` or a `str`, save the figure. A string is appended to the default filename. Infer the filetype if ending on {`\'.pdf\'`, `\'.png\'`, `\'.svg\'`}.
        Original annotation is bool | str | None
        """,
    )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""No description available.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.clustermap")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlStackedViolin(BaseAPI):
    """
    Stacked violin plots. Makes a compact image composed of individual violin plots stacked on top of each other. Useful to visualize gene expression per cluster. Wraps seaborn.violinplot for anndata.AnnData.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    var_names: typing.Any = Field(
        Ellipsis,
        description="""`var_names` should be a valid subset of `adata.var_names`. If `var_names` is a mapping, then the key is used as a label to group the values. The mapping values should be sequences of valid `adata.var_names`.
        Original annotation is _VarNames | Mapping[str, _VarNames]
        """,
    )
    groupby: str | Sequence[str] = Field(
        Ellipsis,
        description="""The key of the observation grouping to consider.
        Original annotation is str | Sequence[str]
        """,
    )
    log: bool = Field(
        False,
        description="""Plot on logarithmic axis.
        Original annotation is bool
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""Use `raw` attribute of `adata` if present.
        Original annotation is bool | None
        """,
    )
    num_categories: int = Field(
        7,
        description="""Determines the number of groups into which the groupby observation should be subdivided.
        Original annotation is int
        """,
    )
    title: str | None = Field(
        None,
        description="""Title for the figure.
        Original annotation is str | None
        """,
    )
    colorbar_title: str | None = Field(
        "Median expression in group",
        description="""Title for the color bar. New line character (\\n) can be used.
        Original annotation is str | None
        """,
    )
    # figsize: tuple[float, float] | None = Field(
    #     None,
    #     description="""Figure size when `multi_panel=True`. Otherwise the default figsize value is used.
    #     Original annotation is tuple[float, float] | None
    #     """,
    # )
    dendrogram: bool | str = Field(
        False,
        description="""If True or a valid dendrogram key, a dendrogram based on the hierarchical clustering between the `groupby` categories is added.
        Original annotation is bool | str
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Column name in `.var` DataFrame that stores gene symbols.
        Original annotation is str | None
        """,
    )
    # var_group_positions: Sequence[tuple[int, int]] | None = Field(
    #     None,
    #     description="""Use this parameter to highlight groups of `var_names`. This will draw a \'bracket\' or a color block between the given start and end positions.
    #     Original annotation is Sequence[tuple[int, int]] | None
    #     """,
    # )
    var_group_labels: typing.Any = Field(
        None,
        description="""Labels for each of the `var_group_positions` that want to be highlighted.
        Original annotation is Sequence[str] | None
        """,
    )
    standard_scale: Literal["var", "group"] | None = Field(
        None,
        description="""Whether or not to standardize the given dimension between 0 and 1.
        Original annotation is Literal['var', 'group'] | None
        """,
    )
    var_group_rotation: float | None = Field(
        None,
        description="""Label rotation degrees.
        Original annotation is float | None
        """,
    )
    layer: str | None = Field(
        None,
        description="""Name of the AnnData object layer that wants to be plotted.
        Original annotation is str | None
        """,
    )
    categories_order: typing.Any = Field(
        None,
        description="""Order in which to show the categories.
        Original annotation is Sequence[str] | None
        """,
    )
    swap_axes: bool = Field(
        False,
        description="""By setting `swap_axes`, the x and y axes are swapped.
        Original annotation is bool
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return the axis.
        Original annotation is bool | None
        """,
    )
    save: bool | str | None = Field(
        True,
        description="""Save the figure. Infer the filetype if ending on {\'.pdf\', \'.png\', \'.svg\'}.
        Original annotation is bool | str | None
        """,
    )
    return_fig: bool | None = Field(
        False,
        description="""Returns a DotPlot object. Useful for fine-tuning the plot.
        Original annotation is bool | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""A matplotlib axes object. Only works if plotting a single component.
        Original annotation is _AxesSubplot | None
        """,
    )
    vmin: float | None = Field(
        None,
        description="""The value representing the lower limit of the color scale.
        Original annotation is float | None
        """,
    )
    vmax: float | None = Field(
        None,
        description="""The value representing the upper limit of the color scale.
        Original annotation is float | None
        """,
    )
    vcenter: float | None = Field(
        None,
        description="""The value representing the center of the color scale.
        Original annotation is float | None
        """,
    )
    norm: typing.Any = Field(
        None,
        description="""Custom color normalization object from matplotlib.
        Original annotation is Normalize | None
        """,
    )
    cmap: typing.Any = Field(
        "Blues",
        description="""String denoting matplotlib color map.
        Original annotation is Colormap | str | None
        """,
    )
    stripplot: bool = Field(
        False,
        description="""Add a stripplot on top of the violin plot.
        Original annotation is bool
        """,
    )
    jitter: float | bool = Field(
        False,
        description="""Add jitter to the stripplot when stripplot is True.
        Original annotation is float | bool
        """,
    )
    size: float = Field(
        1,
        description="""Size of the jitter points.
        Original annotation is float
        """,
    )
    row_palette: str | None = Field(
        None,
        description="""Color each violin plot row using a different color.
        Original annotation is str | None
        """,
    )
    density_norm: typing.Any = Field(
        "Empty.token",
        description="""The method used to scale the width of each violin.
        Original annotation is DensityNorm | Empty
        """,
    )
    yticklabels: bool = Field(
        False,
        description="""Set to true to view the y tick labels.
        Original annotation is bool
        """,
    )
    order: typing.Any = Field(
        "Empty.token",
        description="""No description available.
        Original annotation is Sequence[str] | None | Empty
        """,
    )
    scale: typing.Any = Field(
        "Empty.token",
        description="""No description available.
        Original annotation is DensityNorm | Empty
        """,
    )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""No description available.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.stacked_violin")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlMatrixplot(BaseAPI):
    """
    Create a heatmap of the mean expression values per group of each var_names. This function provides a convenient interface to the MatrixPlot class with various parameters for customization.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    var_names: typing.Any = Field(
        Ellipsis,
        description="""`var_names` should be a valid subset of `adata.var_names`. If `var_names` is a mapping, then the key is used as a label to group the values with options for coloring or grouping using \'brackets\'.
        Original annotation is _VarNames | Mapping[str, _VarNames]
        """,
    )
    groupby: str | Sequence[str] = Field(
        Ellipsis,
        description="""The key of the observation grouping to consider.
        Original annotation is str | Sequence[str]
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""Use `raw` attribute of `adata` if present.
        Original annotation is bool | None
        """,
    )
    log: bool = Field(
        False,
        description="""Plot on logarithmic axis.
        Original annotation is bool
        """,
    )
    num_categories: int = Field(
        7,
        description="""Determines the number of groups if groupby observation is not categorical.
        Original annotation is int
        """,
    )
    categories_order: typing.Any = Field(
        None,
        description="""Order in which to show the categories with options to change based on dendrogram or totals.
        Original annotation is Sequence[str] | None
        """,
    )
    # figsize: tuple[float, float] | None = Field(
    #     None,
    #     description="""Figure size parameter for the plot.
    #     Original annotation is tuple[float, float] | None
    #     """,
    # )
    dendrogram: bool | str = Field(
        False,
        description="""Adds a dendrogram based on hierarchical clustering between groupby categories.
        Original annotation is bool | str
        """,
    )
    title: str | None = Field(
        None,
        description="""Title for the figure.
        Original annotation is str | None
        """,
    )
    cmap: typing.Any = Field(
        "viridis",
        description="""String representing the matplotlib color map.
        Original annotation is Colormap | str | None
        """,
    )
    colorbar_title: str | None = Field(
        "Mean expression in group",
        description="""Title for the color bar with support for newline character.
        Original annotation is str | None
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Column name in `.var` DataFrame that stores gene symbols.
        Original annotation is str | None
        """,
    )
    # var_group_positions: Sequence[tuple[int, int]] | None = Field(
    #     None,
    #     description="""Highlight groups of `var_names` with brackets or color blocks between given positions.
    #     Original annotation is Sequence[tuple[int, int]] | None
    #     """,
    # )
    var_group_labels: typing.Any = Field(
        None,
        description="""Labels for each of the `var_group_positions`.
        Original annotation is Sequence[str] | None
        """,
    )
    var_group_rotation: float | None = Field(
        None,
        description="""Label rotation degrees.
        Original annotation is float | None
        """,
    )
    layer: str | None = Field(
        None,
        description="""Name of the AnnData object layer to be plotted.
        Original annotation is str | None
        """,
    )
    standard_scale: typing.Any = Field(
        None,
        description="""Standardize dimension values between 0 and 1.
        Original annotation is Literal['var', 'group'] | None
        """,
    )
    values_df: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is pd.DataFrame | None
        """,
    )
    swap_axes: bool = Field(
        False,
        description="""Swap x and y axes for plotting.
        Original annotation is bool
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot without returning axis.
        Original annotation is bool | None
        """,
    )
    save: str | bool | None = Field(
        True,
        description="""Save the figure with options for file type.
        Original annotation is str | bool | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""Matplotlib axes object for plotting a single component.
        Original annotation is _AxesSubplot | None
        """,
    )
    return_fig: bool | None = Field(
        False,
        description="""Returns a DotPlot object for fine-tuning the plot.
        Original annotation is bool | None
        """,
    )
    vmin: float | None = Field(
        None,
        description="""Lower limit of the color scale.
        Original annotation is float | None
        """,
    )
    vmax: float | None = Field(
        None,
        description="""Upper limit of the color scale.
        Original annotation is float | None
        """,
    )
    vcenter: float | None = Field(
        None,
        description="""Center of the color scale for diverging colormaps.
        Original annotation is float | None
        """,
    )
    norm: typing.Any = Field(
        None,
        description="""Custom color normalization object from matplotlib.
        Original annotation is Normalize | None
        """,
    )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""Parameters passed to matplotlib.pyplot.pcolor.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.matrixplot")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlScrubletScoreDistribution(BaseAPI):
    """
    Plot histogram of doublet scores for observed transcriptomes and simulated doublets. The function requires the previous execution of Scrublet with the input object.
    """

    adata: str = Field(
        "data",
        description="""An AnnData object resulting from the scrublet function.
        """,
    )
    scale_hist_obs: typing.Any = Field(
        "log",
        description="""Set y axis scale transformation in matplotlib for the plot of observed transcriptomes.
        Original annotation is Scale
        """,
    )
    scale_hist_sim: typing.Any = Field(
        "linear",
        description="""Set y axis scale transformation in matplotlib for the plot of simulated doublets.
        Original annotation is Scale
        """,
    )
    # figsize: tuple[float | int, float | int] = Field(
    #     (8, 3),
    #     description="""Specifies the width and height of the figure.
    #     Original annotation is tuple[float | int, float | int]
    #     """,
    # )
    return_fig: bool = Field(
        False,
        description="""No further description available for this parameter.
        Original annotation is bool
        """,
    )
    show: bool = Field(
        True,
        description="""Displays the plot without returning axis.
        Original annotation is bool
        """,
    )
    save: str | bool | None = Field(
        # None,
        True,
        description="""If True or a string, saves the figure with a filename extension to infer the filetype.
        Original annotation is str | bool | None
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.scrublet_score_distribution")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlPcaLoadings(BaseAPI):
    """
    Rank genes according to contributions to PCs. Parameters: adata - Annotated data matrix, components - For example, \'1,2,3\' means [1, 2, 3], first, second, third principal component, include_lowest - Whether to show the variables with both highest and lowest loadings, show - Show the plot, do not return axis, n_points - Number of variables to plot for each component, save - If True or a str, save the figure. A string is appended to the default filename. Infer the filetype if ending on {\'.pdf\', \'.png\', \'.svg\'}.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    components: typing.Any = Field(
        None,
        description="""For example, \'1,2,3\' means [1, 2, 3], first, second, third principal component.
        Original annotation is str | Sequence[int] | None
        """,
    )
    include_lowest: bool = Field(
        True,
        description="""Whether to show the variables with both highest and lowest loadings.
        Original annotation is bool
        """,
    )
    n_points: int | None = Field(
        None,
        description="""Number of variables to plot for each component.
        Original annotation is int | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: str | bool | None = Field(
        # None,
        True,
        description="""If True or a str, save the figure. A string is appended to the default filename. Infer the filetype if ending on {\'.pdf\', \'.png\', \'.svg\'}.
        Original annotation is str | bool | None
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.pca_loadings")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlDrawGraph(BaseAPI):
    """
    Scatter plot in graph-drawing basis.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    color: typing.Any = Field(
        None,
        description="""Keys for annotations of observations/cells or variables/genes.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    mask_obs: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is numpy.ndarray[tuple[int, ...], numpy.dtype[numpy.bool]] | str | None
        """,
    )
    gene_symbols: str | None = Field(
        None,
        description="""Column name in .var DataFrame that stores gene symbols.
        Original annotation is str | None
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""Use .raw attribute of adata for coloring with gene expression.
        Original annotation is bool | None
        """,
    )
    sort_order: typing.Any = Field(
        True,
        description="""For continuous annotations, higher values on top of others.
        Original annotation is <class 'bool'>
        """,
    )
    edges: typing.Any = Field(
        False,
        description="""Show edges.
        Original annotation is <class 'bool'>
        """,
    )
    edges_width: typing.Any = Field(
        0.1,
        description="""Width of edges.
        Original annotation is <class 'float'>
        """,
    )
    edges_color: (
        str | collections.abc.Sequence[float] | collections.abc.Sequence[str]
    ) = Field(
        "grey",
        description="""Color of edges.
        Original annotation is str | collections.abc.Sequence[float] | collections.abc.Sequence[str]
        """,
    )
    neighbors_key: str | None = Field(
        None,
        description="""Where to look for neighbors connectivities.
        Original annotation is str | None
        """,
    )
    arrows: typing.Any = Field(
        False,
        description="""Show arrows (deprecated).
        Original annotation is <class 'bool'>
        """,
    )
    arrows_kwds: typing.Any = Field(
        None,
        description="""Passed to matplotlib.axes.Axes.quiver.
        Original annotation is collections.abc.Mapping[str, typing.Any] | None
        """,
    )
    groups: typing.Any = Field(
        None,
        description="""Restrict to a few categories in categorical observation annotation.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    components: typing.Any = Field(
        None,
        description="""To plot components.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    dimensions: typing.Any = Field(
        None,
        description="""0-indexed dimensions to plot as integers.
        Original annotation is tuple[int, int] | collections.abc.Sequence[tuple[int, int]] | None
        """,
    )
    layer: str | None = Field(
        None,
        description="""Name of the AnnData object layer to plot.
        Original annotation is str | None
        """,
    )
    projection: typing.Any = Field(
        "2d",
        description="""Projection of plot.
        Original annotation is typing.Literal['2d', '3d']
        """,
    )
    scale_factor: float | None = Field(
        None,
        description="""No description available.
        Original annotation is float | None
        """,
    )
    color_map: typing.Any = Field(
        None,
        description="""Color map to use for continuous variables.
        Original annotation is matplotlib.colors.Colormap | str | None
        """,
    )
    cmap: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is matplotlib.colors.Colormap | str | None
        """,
    )
    palette: typing.Any = Field(
        None,
        description="""Colors to use for plotting categorical annotation groups.
        Original annotation is str | collections.abc.Sequence[str] | cycler.Cycler | None
        """,
    )
    na_color: str | tuple[float, ...] = Field(
        "lightgray",
        description="""Color to use for null or masked values.
        Original annotation is str | tuple[float, ...]
        """,
    )
    na_in_legend: typing.Any = Field(
        True,
        description="""If missing values get an entry in the legend.
        Original annotation is <class 'bool'>
        """,
    )
    size: typing.Any = Field(
        None,
        description="""Point size.
        Original annotation is float | collections.abc.Sequence[float] | None
        """,
    )
    frameon: bool | None = Field(
        None,
        description="""Draw a frame around the scatter plot.
        Original annotation is bool | None
        """,
    )
    legend_fontsize: typing.Any = Field(
        None,
        description="""Numeric size in pt or string.
        Original annotation is typing.Union[float, typing.Literal['xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large'], NoneType]
        """,
    )
    legend_fontweight: typing.Any = Field(
        "bold",
        description="""Legend font weight.
        Original annotation is typing.Union[int, typing.Literal['light', 'normal', 'medium', 'semibold', 'bold', 'heavy', 'black']]
        """,
    )
    legend_loc: typing.Any = Field(
        "right margin",
        description="""Location of legend.
        Original annotation is typing.Optional[typing.Literal['none', 'right margin', 'on data', 'on data export', 'best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 'upper center', 'center']]
        """,
    )
    legend_fontoutline: int | None = Field(
        None,
        description="""Line width of the legend font outline.
        Original annotation is int | None
        """,
    )
    colorbar_loc: str | None = Field(
        "right",
        description="""Where to place the colorbar.
        Original annotation is str | None
        """,
    )
    vmax: typing.Any = Field(
        None,
        description="""The upper limit of the color scale.
        Original annotation is str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float] | collections.abc.Sequence[str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float]] | None
        """,
    )
    vmin: typing.Any = Field(
        None,
        description="""The lower limit of the color scale.
        Original annotation is str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float] | collections.abc.Sequence[str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float]] | None
        """,
    )
    vcenter: typing.Any = Field(
        None,
        description="""The center of the color scale.
        Original annotation is str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float] | collections.abc.Sequence[str | float | collections.abc.Callable[[collections.abc.Sequence[float]], float]] | None
        """,
    )
    norm: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is matplotlib.colors.Normalize | collections.abc.Sequence[matplotlib.colors.Normalize] | None
        """,
    )
    add_outline: bool | None = Field(
        False,
        description="""Add a thin border around groups of dots.
        Original annotation is bool | None
        """,
    )
    # outline_width: tuple[float, float] = Field(
    #     (0.3, 0.05),
    #     description="""Width of the border and gap color.
    #     Original annotation is tuple[float, float]
    #     """,
    # )
    # outline_color: tuple[str, str] = Field(
    #     ("black", "white"),
    #     description="""Colors used to adjust the add_outline.
    #     Original annotation is tuple[str, str]
    #     """,
    # )
    ncols: typing.Any = Field(
        4,
        description="""Number of panels per row.
        Original annotation is <class 'int'>
        """,
    )
    hspace: typing.Any = Field(
        0.25,
        description="""Adjust the height of the space between multiple panels.
        Original annotation is <class 'float'>
        """,
    )
    wspace: float | None = Field(
        None,
        description="""Adjust the width of the space between multiple panels.
        Original annotation is float | None
        """,
    )
    title: typing.Any = Field(
        None,
        description="""Provide title for panels.
        Original annotation is str | collections.abc.Sequence[str] | None
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot.
        Original annotation is bool | None
        """,
    )
    save: bool | str | None = Field(
        # None,
        True,
        description="""Save the figure.
        Original annotation is bool | str | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""A matplotlib axes object.
        Original annotation is matplotlib.axes._axes.Axes | None
        """,
    )
    return_fig: bool | None = Field(
        None,
        description="""Return the matplotlib figure.
        Original annotation is bool | None
        """,
    )
    marker: typing.Any = Field(
        ".",
        description="""No description available.
        Original annotation is str | collections.abc.Sequence[str]
        """,
    )
    layout: typing.Any = Field(
        None,
        description="""One of the scanpy.tl.draw_graph layouts.
        Original annotation is typing.Optional[typing.Literal['fr', 'drl', 'kk', 'grid_fr', 'lgl', 'rt', 'rt_circular', 'fa']]
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.draw_graph")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


class ScPlPagaPath(BaseAPI):
    """
    Gene expression and annotation changes along paths in the abstracted graph.
    """

    adata: str = Field(
        "data",
        description="""An annotated data matrix.
        """,
    )
    nodes: Sequence[str | int] = Field(
        Ellipsis,
        description="""A path through nodes of the abstracted graph, names or indices of groups used in PAGA.
        Original annotation is Sequence[str | int]
        """,
    )
    keys: typing.Any = Field(
        Ellipsis,
        description="""Variables in adata.var_names or annotations in adata.obs, plotted using color_map.
        Original annotation is Sequence[str]
        """,
    )
    use_raw: bool = Field(
        True,
        description="""Retrieve gene expressions using adata.raw if set.
        Original annotation is bool
        """,
    )
    annotations: typing.Any = Field(
        ("dpt_pseudotime",),
        description="""Plot keys with color_maps_annotations, must be keys for adata.obs.
        Original annotation is Sequence[str]
        """,
    )
    color_map: typing.Any = Field(
        None,
        description="""Matplotlib colormap.
        Original annotation is str | Colormap | None
        """,
    )
    color_maps_annotations: typing.Any = Field(
        "{'dpt_pseudotime': 'Greys'}",
        description="""Color maps for plotting annotations, keys must match annotations.
        Original annotation is Mapping[str, str | Colormap]
        """,
    )
    palette_groups: typing.Any = Field(
        None,
        description="""Usually use the same palettes as used for coloring the abstracted graph.
        Original annotation is Sequence[str] | None
        """,
    )
    n_avg: int = Field(
        1,
        description="""Number of data points for computing running average.
        Original annotation is int
        """,
    )
    groups_key: str | None = Field(
        None,
        description="""Grouping key used for PAGA, defaults to adata.uns[\'paga\'][\'groups\'] if None.
        Original annotation is str | None
        """,
    )
    # xlim: tuple[int | None, int | None] = Field(
    #     (None, None),
    #     description="""No description available.
    #     Original annotation is tuple[int | None, int | None]
    #     """,
    # )
    title: str | None = Field(
        None,
        description="""No description available.
        Original annotation is str | None
        """,
    )
    left_margin: typing.Any = Field(
        None,
        description="""No description available.
        """,
    )
    ytick_fontsize: int | None = Field(
        None,
        description="""No description available.
        Original annotation is int | None
        """,
    )
    title_fontsize: int | None = Field(
        None,
        description="""No description available.
        Original annotation is int | None
        """,
    )
    show_node_names: bool = Field(
        True,
        description="""Plot node names on nodes bar.
        Original annotation is bool
        """,
    )
    show_yticks: bool = Field(
        True,
        description="""Show y ticks.
        Original annotation is bool
        """,
    )
    show_colorbar: bool = Field(
        True,
        description="""Show the colorbar.
        Original annotation is bool
        """,
    )
    legend_fontsize: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is float | _FontSize | None
        """,
    )
    legend_fontweight: typing.Any = Field(
        None,
        description="""No description available.
        Original annotation is int | _FontWeight | None
        """,
    )
    normalize_to_zero_one: bool = Field(
        False,
        description="""Shift and scale running average to [0, 1] per gene.
        Original annotation is bool
        """,
    )
    as_heatmap: bool = Field(
        True,
        description="""Plot timeseries as heatmap, annotations have no effect if not plotting as heatmap.
        Original annotation is bool
        """,
    )
    return_data: bool = Field(
        False,
        description="""Return timeseries data in addition to axes if True.
        Original annotation is bool
        """,
    )
    show: bool | None = Field(
        None,
        description="""Show the plot, do not return axis.
        Original annotation is bool | None
        """,
    )
    save: bool | str | None = Field(
        True,
        description="""Save the figure if True or a string, infer filetype from filename extension.
        Original annotation is bool | str | None
        """,
    )
    ax: typing.Any = Field(
        None,
        description="""A matplotlib axes object.
        Original annotation is Axes | None
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pl.paga_path")
    _products_str_repr: list[str] = PrivateAttr(default=[])
    _data_name: str = PrivateAttr(default="adata")


TOOLS_DICT = {
    "sc.pl.paga": ScPlPaga,
    "sc.pl.scatter": ScPlScatter,
    "sc.pl.umap": ScPlUmap,
    "sc.pl.tsne": ScPlTsne,
    "sc.pl.heatmap": ScPlHeatmap,
    "sc.pl.dotplot": ScPlDotplot,
    "sc.pl.violin": ScPlViolin,
    "sc.pl.dendrogram": ScPlDendrogram,
    "sc.pl.diffmap": ScPlDiffmap,
    "sc.pl.highly_variable_genes": ScPlHighlyVariableGenes,
    "sc.pl.pca": ScPlPca,
    "sc.pl.embedding_density": ScPlEmbeddingDensity,
    "sc.pl.rank_genes_groups": ScPlRankGenesGroups,
    "sc.pl.rank_genes_groups_dotplot": ScPlRankGenesGroupsDotplot,
    "sc.pl.rank_genes_groups_violin": ScPlRankGenesGroupsViolin,
    "sc.pl.rank_genes_groups_heatmap": ScPlRankGenesGroupsHeatmap,
    "sc.pl.rank_genes_groups_stacked_violin": ScPlRankGenesGroupsStackedViolin,
    "sc.pl.rank_genes_groups_matrixplot": ScPlRankGenesGroupsMatrixplot,
    "sc.pl.rank_genes_groups_tracksplot": ScPlRankGenesGroupsTracksplot,
    "sc.pl.highest_expr_genes": ScPlHighestExprGenes,
    "sc.pl.tracksplot": ScPlTracksplot,
    "sc.pl.clustermap": ScPlClustermap,
    "sc.pl.stacked_violin": ScPlStackedViolin,
    "sc.pl.matrixplot": ScPlMatrixplot,
    "sc.pl.scrublet_score_distribution": ScPlScrubletScoreDistribution,
    "sc.pl.pca_loadings": ScPlPcaLoadings,
    "sc.pl.draw_graph": ScPlDrawGraph,
    "sc.pl.paga_path": ScPlPagaPath,
}

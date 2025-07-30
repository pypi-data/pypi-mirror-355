from __future__ import annotations
from pydantic import ConfigDict, Field, PrivateAttr
from biochatter.api_agent.base.agent_abc import BaseAPI
import typing
from typing import *


class ScPpNeighbors(BaseAPI):
    """
    Compute the nearest neighbors distance matrix and a neighborhood graph of observations, with parameters specifying various options like neighborhood size, representation to use, method for computing connectivities, and more. Returns an AnnData object with specific fields set.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    n_neighbors: int = Field(
        15,
        description="""Specifies the size of the local neighborhood used for manifold approximation, with larger values providing more global views of the manifold.
        Original annotation is int
        """,
    )
    n_pcs: int | None = Field(
        None,
        description="""Defines the number of principal components (PCs) to use, with the option to automatically choose based on data characteristics if not specified.
        Original annotation is int | None
        """,
    )
    use_rep: str | None = Field(
        None,
        description="""Indicates the representation to be used, with options to automatically choose based on data size and characteristics if None is specified.
        Original annotation is str | None
        """,
    )
    knn: bool = Field(
        True,
        description="""Determines whether to use a hard threshold to restrict the number of neighbors or a Gaussian Kernel to assign weights based on distance.
        Original annotation is bool
        """,
    )
    method: typing.Any = Field(
        "umap",
        description="""Specifies the method to use for computing connectivities, with options like \'umap\' or \'gauss\' available.
        Original annotation is _Method
        """,
    )
    transformer: typing.Any = Field(
        None,
        description="""Defines the approximate kNN search implementation, with various known options like \'pynndescent\' or \'rapids\' available.
        Original annotation is KnnTransformerLike | _KnownTransformer | None
        """,
    )
    metric: typing.Any = Field(
        "euclidean",
        description="""Represents a known metric\'s name or a callable for returning a distance, with the option to be ignored if a transformer is used.
        Original annotation is _Metric | _MetricFn
        """,
    )
    # bug: it's incorrectly set to "{}". check gen_data_model.py
    metric_kwds: Mapping[str, Any] = Field(
        # "{}",
        {},
        description="""Provides options for the metric, to be ignored if a transformer is used.
        Original annotation is Mapping[str, Any]
        """,
    )
    random_state: typing.Any = Field(
        0,
        description="""Specifies a numpy random seed, to be ignored if a transformer is used.
        Original annotation is _LegacyRandom
        """,
    )
    # Jiahang (TODO): also mess up key_added = "umap" similar to method.
    key_added: str | None = Field(
        None,
        description="""Determines where the neighbors data is stored and how distances/connectivities are saved in the output.
        Original annotation is str | None
        """,
    )
    # Jiahang (TODO): copy arg does not follow the biomania design philosophy. 
    # in other words, it would never been predicted to be True by LLM.
    # by now we just comment it out. but we need to consider:
    # 1. which is better: comment out, remove, move to private attr?
    # 2. how to prompt developers to actively handle args which don't follow the design 
    # philosophy? similar question applies to figure save arg.
    # 3. how to handle these args more smoothly without the need for manual setting?

    # Jiahang (TODO): one more weird thing: when have "cells colored by louvain clustering"
    # prompt, copy is always predicted to be True. why?

    # Jiahang (TODO): some algorithmic improvements can be made: 
    # 1. arg modification verifier: ask llm whether this arg different from the default 
    # 2. retry llm arg prediction. (api prediction error only leads to logic error, rather
    # than bugs.)
    
    # copy: bool = Field(
    #     False,
    #     description="""Specifies whether to return a copy instead of modifying the original data.
    #     Original annotation is bool
    #     """,
    # )
    _api_name: str = PrivateAttr(default="sc.pp.neighbors")
    _products_str_repr: list[str] = PrivateAttr(
        default=[
            'data.uns["neighbors"]',
            'data.obsp["distances"]',
            'data.obsp["connectivities"]',
            'data.obsm["X_pca"]',
            'data.varm["PCs"]',
            'data.uns["pca"]["variance_ratio"]',
            'data.uns["pca"]["variance"]',
        ]
    )
    _data_name: str = PrivateAttr(default="adata")


class ScPpLogP(BaseAPI):
    """
    Logarithmize the data matrix. Computes :math:`X = \\log(X + 1)`, where :math:`log` denotes the natural logarithm unless a different base is given.
    """

    data: str = Field(
        "data",
        description="""The (annotated) data matrix of shape `n_obs` × `n_vars`. Rows correspond to cells and columns to genes.
        """,
    )
    base: int | None = Field(
        None,
        description="""Base of the logarithm. Natural logarithm is used by default.
        Original annotation is Number | None
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""If an :class:`~anndata.AnnData` is passed, determines whether a copy is returned.
    #     Original annotation is bool
    #     """,
    # )
    chunked: bool | None = Field(
        None,
        description="""Process the data matrix in chunks, which will save memory. Applies only to :class:`~anndata.AnnData`.
        Original annotation is bool | None
        """,
    )
    chunk_size: int | None = Field(
        None,
        description="""`n_obs` of the chunks to process the data in.
        Original annotation is int | None
        """,
    )
    layer: str | None = Field(
        None,
        description="""Entry of layers to transform.
        Original annotation is str | None
        """,
    )
    obsm: str | None = Field(
        None,
        description="""Entry of obsm to transform.
        Original annotation is str | None
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pp.log1p")
    _products_str_repr: list[str] = PrivateAttr(default=["data.X"])
    _data_name: str = PrivateAttr(default="data")


class ScPpHighlyVariableGenes(BaseAPI):
    """
    Annotate highly variable genes based on log-transformed or count data, with different methods depending on the specified flavor.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix with cells as rows and genes as columns.
        """,
    )
    layer: str | None = Field(
        None,
        description="""Option to use a specific layer in the data for expression values instead of the default.
        Original annotation is str | None
        """,
    )
    n_top_genes: int | None = Field(
        None,
        description="""Number of highly variable genes to retain, required when using \'seurat_v3\' flavor.
        Original annotation is int | None
        """,
    )
    min_disp: float = Field(
        0.5,
        description="""Minimum cutoff for normalized dispersion, ignored for \'seurat_v3\' flavor with specified n_top_genes.
        Original annotation is float
        """,
    )
    max_disp: float = Field(
        float("inf"),
        description="""Maximum cutoff for normalized dispersion, ignored for \'seurat_v3\' flavor with specified n_top_genes.
        Original annotation is float
        """,
    )
    min_mean: float = Field(
        0.0125,
        description="""Minimum cutoff for mean expression, ignored for \'seurat_v3\' flavor with specified n_top_genes.
        Original annotation is float
        """,
    )
    max_mean: float = Field(
        3,
        description="""Maximum cutoff for mean expression, ignored for \'seurat_v3\' flavor with specified n_top_genes.
        Original annotation is float
        """,
    )
    span: float = Field(
        0.3,
        description="""Fraction of data used for variance estimation when using \'seurat_v3\' flavor.
        Original annotation is float
        """,
    )
    n_bins: int = Field(
        20,
        description="""Number of bins for binning mean gene expression, used for normalization.
        Original annotation is int
        """,
    )
    flavor: typing.Any = Field(
        "seurat",
        description="""Method to identify highly variable genes, with different behaviors for each flavor.
        Original annotation is Literal['seurat', 'cell_ranger', 'seurat_v3', 'seurat_v3_paper']
        """,
    )
    subset: bool = Field(
        False,
        description="""Whether to subset to highly variable genes in place or just indicate them.
        Original annotation is bool
        """,
    )
    inplace: bool = Field(
        True,
        description="""Determines if calculated metrics should be placed in .var or returned.
        Original annotation is bool
        """,
    )
    batch_key: str | None = Field(
        None,
        description="""Key to specify batch for selecting highly variable genes, affecting the method used.
        Original annotation is str | None
        """,
    )
    check_values: bool = Field(
        True,
        description="""Option to check if counts in selected layer are integers, with a warning if set to True.
        Original annotation is bool
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pp.highly_variable_genes")
    _products_str_repr: list[str] = PrivateAttr(
        default=[
            'data.var["highly_variable"]',
            'data.var["means"]',
            'data.var["dispersions"]',
            'data.var["dispersions_norm"]',
            'data.var["variances"]',
            'data.var["variances_norm"]',
            'data.var["highly_variable_rank"]',
            'data.var["highly_variable_nbatches"]',
            'data.var["highly_variable_intersection"]',
        ]
    )
    _data_name: str = PrivateAttr(default="adata")


class ScPpPca(BaseAPI):
    """
    Principal component analysis :cite:p:`Pedregosa2011`. Computes PCA coordinates, loadings, and variance decomposition using various implementations and defaults for `svd_solver` as described in the documentation.
    """

    data: str = Field(
        "data",
        description="""The (annotated) data matrix of shape `n_obs` × `n_vars`. Rows correspond to cells and columns to genes.
        """,
    )
    n_comps: int | None = Field(
        None,
        description="""Number of principal components to compute. Defaults to 50, or 1 - minimum dimension size of selected representation.
        Original annotation is int | None
        """,
    )
    layer: str | None = Field(
        None,
        description="""Layer of `adata` to use as expression values.
        Original annotation is str | None
        """,
    )
    zero_center: bool = Field(
        True,
        description="""Determines whether to compute PCA from the covariance matrix or to perform a truncated SVD. Default PCA algorithms support implicit zero-centering.
        Original annotation is bool
        """,
    )
    svd_solver: typing.Any = Field(
        None,
        description="""SVD solver to use, with different options and defaults based on `chunked` and `zero_center` settings. Supports various solvers like `\'arpack\'`, `\'covariance_eigh\'`, `\'randomized\'`, and more.
        Original annotation is SvdSolver | None
        """,
    )
    chunked: bool = Field(
        False,
        description="""Controls whether to perform incremental PCA on segments of `chunk_size` or a full PCA/truncated SVD based on the settings of `svd_solver` and `zero_center`.
        Original annotation is bool
        """,
    )
    chunk_size: int | None = Field(
        None,
        description="""Number of observations to include in each chunk. Mandatory if `chunked=True` was passed.
        Original annotation is int | None
        """,
    )
    random_state: typing.Any = Field(
        0,
        description="""Parameter to change initial states for optimization.
        Original annotation is _LegacyRandom
        """,
    )
    return_info: bool = Field(
        False,
        description="""Relevant when not passing an `AnnData`, specifying what information to return.
        Original annotation is bool
        """,
    )
    mask_var: typing.Any = Field(
        "Empty.token",
        description="""Controls the selection of genes for PCA computation, defaulting to `.var[\'highly_variable\']` if available.
        Original annotation is NDArray[np.bool_] | str | None | Empty
        """,
    )
    use_highly_variable: bool | None = Field(
        None,
        description="""Determines whether to use highly variable genes only, with a deprecation notice for `mask_var` in version 1.10.0.
        Original annotation is bool | None
        """,
    )
    dtype: typing.Any = Field(
        "float32",
        description="""Numpy data type string for converting the result.
        Original annotation is DTypeLike
        """,
    )
    key_added: str | None = Field(
        None,
        description="""Specifies how the results are stored in the `AnnData` object if not explicitly provided.
        Original annotation is str | None
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""Determines whether a copy is returned when passing an `AnnData`. This parameter is ignored otherwise.
    #     Original annotation is bool
    #     """,
    # )
    _api_name: str = PrivateAttr(default="sc.pp.pca")
    _products_str_repr: list[str] = PrivateAttr(
        default=[
            'data.obsm["X_pca"]',
            'data.varm["PCs"]',
            'data.uns["pca"]["variance_ratio"]',
            'data.uns["pca"]["variance"]',
        ]
    )
    _data_name: str = PrivateAttr(default="data")


class ScPpCalculateQcMetrics(BaseAPI):
    """
    Calculate quality control metrics for an AnnData object based on calculateQCMetrics from scater. Can be time-consuming on first call but cached for later use. Returns various metrics at observation and variable levels.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    expr_type: str = Field(
        "counts",
        description="""Name of kind of values in X.
        Original annotation is str
        """,
    )
    var_type: str = Field(
        "genes",
        description="""The kind of thing the variables are.
        Original annotation is str
        """,
    )
    qc_vars: Collection[str] | str = Field(
        (),
        description="""Keys for boolean columns of .var to identify variables for control (e.g., \'ERCC\' or \'mito\').
        Original annotation is Collection[str] | str
        """,
    )
    percent_top: typing.Any = Field(
        (50, 100, 200, 500),
        description="""List of ranks where the cumulative proportion of expression is reported as a percentage, aiding in library complexity assessment.
        Original annotation is Collection[int] | None
        """,
    )
    layer: str | None = Field(
        None,
        description="""If provided, use adata.layers[layer] for expression values instead of adata.X.
        Original annotation is str | None
        """,
    )
    use_raw: bool = Field(
        False,
        description="""If True, use adata.raw.X for expression values instead of adata.X.
        Original annotation is bool
        """,
    )
    inplace: bool = Field(
        False,
        description="""Determines if calculated metrics are placed in adata\'s .obs and .var.
        Original annotation is bool
        """,
    )
    log1p: bool = Field(
        True,
        description="""Set to False to skip computing log1p transformed annotations.
        Original annotation is bool
        """,
    )
    parallel: bool | None = Field(
        None,
        description="""No description available.
        Original annotation is bool | None
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pp.calculate_qc_metrics")
    _products_str_repr: list[str] = PrivateAttr(
        default=[
            'data.obs["total_genes_by_counts"]',
            'data.obs["total_counts"]',
            'data.obs["pct_counts_in_top_50_genes"]',
            'data.obs["pct_counts_in_top_100_genes"]',
            'data.obs["pct_counts_in_top_200_genes"]',
        ]
    )
    _data_name: str = PrivateAttr(default="adata")


class ScPpFilterCells(BaseAPI):
    """
    Filter cell outliers based on counts and numbers of genes expressed. Only provide one of the optional parameters min_counts, min_genes, max_counts, max_genes per call.
    """

    data: str = Field(
        "data",
        description="""The (annotated) data matrix of shape n_obs x n_vars. Rows correspond to cells and columns to genes.
        """,
    )
    min_counts: int | None = Field(
        None,
        description="""Minimum number of counts required for a cell to pass filtering.
        Original annotation is int | None
        """,
    )
    min_genes: int | None = Field(
        None,
        description="""Minimum number of genes expressed required for a cell to pass filtering.
        Original annotation is int | None
        """,
    )
    max_counts: int | None = Field(
        None,
        description="""Maximum number of counts required for a cell to pass filtering.
        Original annotation is int | None
        """,
    )
    max_genes: int | None = Field(
        None,
        description="""Maximum number of genes expressed required for a cell to pass filtering.
        Original annotation is int | None
        """,
    )
    inplace: bool = Field(
        True,
        description="""Perform computation inplace or return result.
        Original annotation is bool
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""No description available.
    #     Original annotation is bool
    #     """,
    # )
    _api_name: str = PrivateAttr(default="sc.pp.filter_cells")
    _products_str_repr: list[str] = PrivateAttr(
        default=["data.X", 'data.obs["n_counts"]', 'data.obs["n_genes"]']
    )
    _data_name: str = PrivateAttr(default="data")


class ScPpFilterGenes(BaseAPI):
    """
    Filter genes based on number of cells or counts. Keep genes that have at least `min_counts` counts or are expressed in at least `min_cells` cells or have at most `max_counts` counts or are expressed in at most `max_cells` cells. Only provide one of the optional parameters `min_counts`, `min_cells`, `max_counts`, `max_cells` per call.
    """

    data: str = Field(
        "data",
        description="""An annotated data matrix of shape `n_obs` × `n_vars`. Rows correspond to cells and columns to genes.
        """,
    )
    min_counts: int | None = Field(
        None,
        description="""Minimum number of counts required for a gene to pass filtering.
        Original annotation is int | None
        """,
    )
    min_cells: int | None = Field(
        None,
        description="""Minimum number of cells expressed required for a gene to pass filtering.
        Original annotation is int | None
        """,
    )
    max_counts: int | None = Field(
        None,
        description="""Maximum number of counts required for a gene to pass filtering.
        Original annotation is int | None
        """,
    )
    max_cells: int | None = Field(
        None,
        description="""Maximum number of cells expressed required for a gene to pass filtering.
        Original annotation is int | None
        """,
    )
    inplace: bool = Field(
        True,
        description="""Perform computation inplace or return result.
        Original annotation is bool
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""No description available.
    #     Original annotation is bool
    #     """,
    # )
    _api_name: str = PrivateAttr(default="sc.pp.filter_genes")
    _products_str_repr: list[str] = PrivateAttr(
        default=["data.X", 'data.var["n_counts"]', 'data.var["n_genes"]']
    )
    _data_name: str = PrivateAttr(default="data")


class ScPpNormalizeTotal(BaseAPI):
    """
    Normalize counts per cell. Normalize each cell by total counts over all genes, so that every cell has the same total count after normalization. If choosing `target_sum=1e6`, this is CPM normalization. If `exclude_highly_expressed=True`, very highly expressed genes are excluded from the computation of the normalization factor (size factor) for each cell. This function is used in various software like Seurat, Cell Ranger, and SPRING.
    """

    adata: str = Field(
        "data",
        description="""The annotated data matrix of shape `n_obs` × `n_vars`. Rows correspond to cells and columns to genes.
        """,
    )
    target_sum: float | None = Field(
        None,
        description="""If `None`, after normalization, each observation (cell) has a total count equal to the median of total counts for observations (cells) before normalization.
        Original annotation is float | None
        """,
    )
    exclude_highly_expressed: bool = Field(
        False,
        description="""Exclude (very) highly expressed genes for the computation of the normalization factor (size factor) for each cell. A gene is considered highly expressed if it has more than `max_fraction` of the total counts in at least one cell. The not-excluded genes will sum up to `target_sum`. Providing this argument when `adata.X` is a :class:`~dask.array.Array` will incur blocking `.compute()` calls on the array.
        Original annotation is bool
        """,
    )
    max_fraction: float = Field(
        0.05,
        description="""If `exclude_highly_expressed=True`, consider cells as highly expressed that have more counts than `max_fraction` of the original total counts in at least one cell.
        Original annotation is float
        """,
    )
    key_added: str | None = Field(
        None,
        description="""Name of the field in `adata.obs` where the normalization factor is stored.
        Original annotation is str | None
        """,
    )
    layer: str | None = Field(
        None,
        description="""Layer to normalize instead of `X`. If `None`, `X` is normalized.
        Original annotation is str | None
        """,
    )
    inplace: bool = Field(
        True,
        description="""Whether to update `adata` or return a dictionary with normalized copies of `adata.X` and `adata.layers`.
        Original annotation is bool
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""Whether to modify the copied input object. Not compatible with inplace=False.
    #     Original annotation is bool
    #     """,
    # )
    _api_name: str = PrivateAttr(default="sc.pp.normalize_total")
    _products_str_repr: list[str] = PrivateAttr(default=["data.X"])
    _data_name: str = PrivateAttr(default="adata")


class ScPpRegressOut(BaseAPI):
    """
    Regress out (mostly) unwanted sources of variation. Uses simple linear regression. Inspired by Seurat\'s `regressOut` function in R. Overcorrection may occur in certain circumstances.
    """

    adata: str = Field(
        "data",
        description="""The annotated data matrix.
        """,
    )
    keys: str | Sequence[str] = Field(
        Ellipsis,
        description="""Keys for observation annotation on which to regress on.
        Original annotation is str | Sequence[str]
        """,
    )
    layer: str | None = Field(
        None,
        description="""If provided, which element of layers to regress on.
        Original annotation is str | None
        """,
    )
    n_jobs: int | None = Field(
        None,
        description="""Number of jobs for parallel computation. `None` means using `scanpy._settings.ScanpyConfig.n_jobs`.
        Original annotation is int | None
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""Determines whether a copy of `adata` is returned.
    #     Original annotation is bool
    #     """,
    # )
    _api_name: str = PrivateAttr(default="sc.pp.regress_out")
    _products_str_repr: list[str] = PrivateAttr(default=["data.X"])
    _data_name: str = PrivateAttr(default="adata")


class ScPpScale(BaseAPI):
    """
    Scale data to unit variance and zero mean. Variables that do not display any variation are retained and set to 0 if zero_center==True. Parameters include data, zero_center, max_value, copy, layer, obsm, and mask_obs. Returns an updated AnnData object with scaled count data matrix and statistics per gene.
    """

    data: str = Field(
        "data",
        description="""The (annotated) data matrix of shape `n_obs` × `n_vars`. Rows correspond to cells and columns to genes.
        """,
    )
    zero_center: bool = Field(
        True,
        description="""If `False`, omit zero-centering variables, which allows to handle sparse input efficiently.
        Original annotation is bool
        """,
    )
    max_value: float | None = Field(
        None,
        description="""Clip (truncate) to this value after scaling. If `None`, do not clip.
        Original annotation is float | None
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""Whether this function should be performed inplace. If an AnnData object is passed, this also determines if a copy is returned.
    #     Original annotation is bool
    #     """,
    # )
    layer: str | None = Field(
        None,
        description="""If provided, which element of layers to scale.
        Original annotation is str | None
        """,
    )
    obsm: str | None = Field(
        None,
        description="""If provided, which element of obsm to scale.
        Original annotation is str | None
        """,
    )
    mask_obs: typing.Any = Field(
        None,
        description="""Restrict both the derivation of scaling parameters and the scaling itself to a certain set of observations. The mask is specified as a boolean array or a string referring to an array in AnnData.obs. This will transform data from csc to csr format if issparse(data).
        Original annotation is NDArray[np.bool_] | str | None
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pp.scale")
    _products_str_repr: list[str] = PrivateAttr(
        default=["data.X", 'data.var["mean"]', 'data.var["std"]', 'data.var["var"]']
    )
    _data_name: str = PrivateAttr(default="data")


class ScPpSample(BaseAPI):
    """
    Sample observations or variables with or without replacement.
    """

    data: str = Field(
        "data",
        description="""The (annotated) data matrix of shape `n_obs` × `n_vars`. Rows correspond to cells and columns to genes.
        """,
    )
    fraction: float | None = Field(
        None,
        description="""Sample to this `fraction` of the number of observations or variables. This can be larger than 1.0, if `replace=True`. See `axis` and `replace`.
        Original annotation is float | None
        """,
    )
    n: int | None = Field(
        None,
        description="""Sample to this number of observations or variables. See `axis`.
        Original annotation is int | None
        """,
    )
    rng: typing.Any = Field(
        None,
        description="""Random seed to change subsampling.
        Original annotation is RNGLike | SeedLike | None
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""If an :class:`~anndata.AnnData` is passed, determines whether a copy is returned.
    #     Original annotation is bool
    #     """,
    # )
    replace: bool = Field(
        False,
        description="""If True, samples are drawn with replacement.
        Original annotation is bool
        """,
    )
    axis: typing.Any = Field(
        "obs",
        description="""Sample `observations` (axis 0) or `variables` (axis 1).
        Original annotation is Literal['obs', 0, 'var', 1]
        """,
    )
    p: typing.Any = Field(
        None,
        description="""Drawing probabilities (floats) or mask (bools). Either an `axis`-sized array, or the name of a column. If `p` is an array of probabilities, it must sum to 1.
        Original annotation is str | NDArray[np.bool_] | NDArray[np.floating] | None
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pp.sample")
    _products_str_repr: list[str] = PrivateAttr(default=["data.X"])
    _data_name: str = PrivateAttr(default="data")


class ScPpDownsampleCounts(BaseAPI):
    """
    Downsample counts from count matrix. If `counts_per_cell` is specified, each cell will be downsampled. If `total_counts` is specified, expression matrix will be downsampled to contain at most `total_counts`.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    counts_per_cell: int | Collection[int] | None = Field(
        None,
        description="""Target total counts per cell. If a cell has more than \'counts_per_cell\', it will be downsampled to this number. Resulting counts can be specified on a per cell basis by passing an array. Should be an integer or integer ndarray with the same length as the number of observations.
        Original annotation is int | Collection[int] | None
        """,
    )
    total_counts: int | None = Field(
        None,
        description="""Target total counts. If the count matrix has more than `total_counts`, it will be downsampled to have this number.
        Original annotation is int | None
        """,
    )
    random_state: typing.Any = Field(
        0,
        description="""Random seed for subsampling.
        Original annotation is _LegacyRandom
        """,
    )
    replace: bool = Field(
        False,
        description="""Whether to sample the counts with replacement.
        Original annotation is bool
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""Determines whether a copy of `adata` is returned.
    #     Original annotation is bool
    #     """,
    # )
    _api_name: str = PrivateAttr(default="sc.pp.downsample_counts")
    _products_str_repr: list[str] = PrivateAttr(default=["data.X"])
    _data_name: str = PrivateAttr(default="adata")


class ScPpCombat(BaseAPI):
    """
    ComBat function for batch effect correction. Corrects for batch effects by fitting linear models, gains statistical power via an EB framework where information is borrowed across genes. Uses the implementation combat.py.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix
        """,
    )
    key: str = Field(
        "batch",
        description="""Key to a categorical annotation from AnnData.obs that will be used for batch effect removal.
        Original annotation is str
        """,
    )
    covariates: typing.Any = Field(
        None,
        description="""Additional covariates besides the batch variable such as adjustment variables or biological condition. Refers to the design matrix X in Equation 2.1 in Johnson2006 and to the mod argument in the original combat function in the sva R package. Not including covariates may introduce bias or lead to the removal of biological signal in unbalanced designs.
        Original annotation is Collection[str] | None
        """,
    )
    inplace: bool = Field(
        True,
        description="""Whether to replace adata.X or to return the corrected data
        Original annotation is bool
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pp.combat")
    _products_str_repr: list[str] = PrivateAttr(default=["data.X"])
    _data_name: str = PrivateAttr(default="adata")


class ScPpScrublet(BaseAPI):
    """
    Predict doublets using Scrublet :cite:p:`Wolock2019`. Predict cell doublets using a nearest-neighbor classifier of observed transcriptomes and simulated doublets. This function is a wrapper around functions that pre-process using Scanpy and directly call functions of Scrublet().
    """

    adata: str = Field(
        "data",
        description="""The annotated data matrix of shape ``n_obs`` × ``n_vars``. Expected to be un-normalised where adata_sim is not supplied, in which case doublets will be simulated and pre-processing applied to both objects. If adata_sim is supplied, this should be the observed transcriptomes processed consistently (filtering, transform, normalisaton, hvg) with adata_sim.
        """,
    )
    adata_sim: typing.Any = Field(
        None,
        description="""(Advanced use case) Optional annData object generated by :func:`~scanpy.pp.scrublet_simulate_doublets`, with same number of vars as adata. This should have been built from adata_obs after filtering genes and cells and selecting highly-variable genes.
        Original annotation is AnnData | None
        """,
    )
    batch_key: str | None = Field(
        None,
        description="""Optional :attr:`~anndata.AnnData.obs` column name discriminating between batches.
        Original annotation is str | None
        """,
    )
    sim_doublet_ratio: float = Field(
        2.0,
        description="""Number of doublets to simulate relative to the number of observed transcriptomes.
        Original annotation is float
        """,
    )
    expected_doublet_rate: float = Field(
        0.05,
        description="""Where adata_sim not supplied, the estimated doublet rate for the experiment.
        Original annotation is float
        """,
    )
    stdev_doublet_rate: float = Field(
        0.02,
        description="""Where adata_sim not supplied, uncertainty in the expected doublet rate.
        Original annotation is float
        """,
    )
    synthetic_doublet_umi_subsampling: float = Field(
        1.0,
        description="""Where adata_sim not supplied, rate for sampling UMIs when creating synthetic doublets.
        Original annotation is float
        """,
    )
    knn_dist_metric: typing.Any = Field(
        "euclidean",
        description="""Distance metric used when finding nearest neighbors.
        Original annotation is _Metric | _MetricFn
        """,
    )
    normalize_variance: bool = Field(
        True,
        description="""If True, normalize the data such that each gene has a variance of 1.
        Original annotation is bool
        """,
    )
    log_transform: bool = Field(
        False,
        description="""Whether to use :func:`~scanpy.pp.log1p` to log-transform the data prior to PCA.
        Original annotation is bool
        """,
    )
    mean_center: bool = Field(
        True,
        description="""If True, center the data such that each gene has a mean of 0.
        Original annotation is bool
        """,
    )
    n_prin_comps: int = Field(
        30,
        description="""Number of principal components used to embed the transcriptomes prior to k-nearest-neighbor graph construction.
        Original annotation is int
        """,
    )
    use_approx_neighbors: bool | None = Field(
        None,
        description="""Use approximate nearest neighbor method (annoy) for the KNN classifier.
        Original annotation is bool | None
        """,
    )
    get_doublet_neighbor_parents: bool = Field(
        False,
        description="""If True, return (in .uns) the parent transcriptomes that generated the doublet neighbors of each observed transcriptome.
        Original annotation is bool
        """,
    )
    n_neighbors: int | None = Field(
        None,
        description="""Number of neighbors used to construct the KNN graph of observed transcriptomes and simulated doublets.
        Original annotation is int | None
        """,
    )
    threshold: float | None = Field(
        None,
        description="""Doublet score threshold for calling a transcriptome a doublet.
        Original annotation is float | None
        """,
    )
    verbose: bool = Field(
        True,
        description="""If True, log progress updates.
        Original annotation is bool
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""If True, return a copy of the input adata with Scrublet results added. Otherwise, Scrublet results are added in place.
    #     Original annotation is bool
    #     """,
    # )
    random_state: typing.Any = Field(
        0,
        description="""Initial state for doublet simulation and nearest neighbors.
        Original annotation is _LegacyRandom
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pp.scrublet")
    _products_str_repr: list[str] = PrivateAttr(
        default=[
            'data.obs["doublet_score"]',
            'data.obs["predicted_doublet"]',
            'data.uns["scrublet"]["doublet_scores_sim"]',
            'data.uns["scrublet"]["doublet_parents"]',
            'data.uns["scrublet"]["parameters"]',
        ]
    )
    _data_name: str = PrivateAttr(default="adata")


class ScPpScrubletSimulateDoublets(BaseAPI):
    """
    Simulate doublets by adding the counts of random observed transcriptome pairs.
    """

    adata: str = Field(
        "data",
        description="""The annotated data matrix of shape n_obs × n_vars. Rows correspond to cells and columns to genes. Genes should have been filtered for expression and variability, and the object should contain raw expression of the same dimensions.
        """,
    )
    layer: str | None = Field(
        None,
        description="""Layer of adata where raw values are stored, or \'X\' if values are in .X.
        Original annotation is str | None
        """,
    )
    sim_doublet_ratio: float = Field(
        2.0,
        description="""Number of doublets to simulate relative to the number of observed transcriptomes. If None, self.sim_doublet_ratio is used.
        Original annotation is float
        """,
    )
    synthetic_doublet_umi_subsampling: float = Field(
        1.0,
        description="""Rate for sampling UMIs when creating synthetic doublets. If 1.0, each doublet is created by simply adding the UMIs from two randomly sampled observed transcriptomes. For values less than 1, the UMI counts are added and then randomly sampled at the specified rate.
        Original annotation is float
        """,
    )
    random_seed: typing.Any = Field(
        0,
        description="""No description available.
        Original annotation is _LegacyRandom
        """,
    )
    _api_name: str = PrivateAttr(default="sc.pp.scrublet_simulate_doublets")
    _products_str_repr: list[str] = PrivateAttr(
        default=[
            'data.obsm["scrublet"]["doublet_parents"]',
            'data.uns["scrublet"]["parameters"]',
        ]
    )
    _data_name: str = PrivateAttr(default="adata")


TOOLS_DICT = {
    "sc.pp.neighbors": ScPpNeighbors,
    "sc.pp.log1p": ScPpLogP,
    "sc.pp.highly_variable_genes": ScPpHighlyVariableGenes,
    "sc.pp.pca": ScPpPca,
    "sc.pp.calculate_qc_metrics": ScPpCalculateQcMetrics,
    "sc.pp.filter_cells": ScPpFilterCells,
    "sc.pp.filter_genes": ScPpFilterGenes,
    "sc.pp.normalize_total": ScPpNormalizeTotal,
    "sc.pp.regress_out": ScPpRegressOut,
    "sc.pp.scale": ScPpScale,
    "sc.pp.sample": ScPpSample,
    "sc.pp.downsample_counts": ScPpDownsampleCounts,
    "sc.pp.combat": ScPpCombat,
    "sc.pp.scrublet": ScPpScrublet,
    "sc.pp.scrublet_simulate_doublets": ScPpScrubletSimulateDoublets,
}

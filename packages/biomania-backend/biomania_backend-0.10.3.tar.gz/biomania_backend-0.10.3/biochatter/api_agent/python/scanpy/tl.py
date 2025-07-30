from __future__ import annotations
from pydantic import ConfigDict, Field, PrivateAttr
from biochatter.api_agent.base.agent_abc import BaseAPI
import typing
from typing import *


class ScTlPaga(BaseAPI):
    """
    Map out the coarse-grained connectivity structures of complex manifolds using partition-based graph abstraction (PAGA) to generate a simpler abstracted graph representation.
    """

    adata: str = Field(
        "data",
        description="""An annotated data matrix used as input.
        """,
    )
    groups: str | None = Field(
        None,
        description="""Key for categorical data in the annotated data matrix. Default key is \'leiden\' or \'louvain\'.
        Original annotation is str | None
        """,
    )
    use_rna_velocity: bool = Field(
        False,
        description="""Option to utilize RNA velocity to orient edges in the abstracted graph and estimate transitions.
        Original annotation is bool
        """,
    )
    model: Literal["v1.2", "v1.0"] = Field(
        "v1.2",
        description="""The PAGA connectivity model to be applied.
        Original annotation is Literal['v1.2', 'v1.0']
        """,
    )
    neighbors_key: str | None = Field(
        None,
        description="""Parameter specifying where to look for neighbor settings and connectivities in the data matrix.
        Original annotation is str | None
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""Option to copy the data matrix before computation or perform computation in place.
    #     Original annotation is bool
    #     """,
    # )
    _api_name: str = PrivateAttr(default="sc.tl.paga")
    _products_str_repr: list[str] = PrivateAttr(
        default=[
            'data.uns["paga"]["connectivities"]',
            'data.uns["paga"]["connectivities_tree"]',
        ]
    )
    _data_name: str = PrivateAttr(default="adata")


class ScTlLeiden(BaseAPI):
    """
    Cluster cells into subgroups using the Leiden algorithm, an improved version of the Louvain algorithm, proposed for single-cell analysis. Requires running specific functions before clustering.
    """

    adata: str = Field(
        "data",
        description="""The annotated data matrix.
        """,
    )
    resolution: float = Field(
        1,
        description="""Parameter controlling clustering coarseness. Higher values lead to more clusters. Set to `None` in certain cases.
        Original annotation is float
        """,
    )
    restrict_to: typing.Any = Field(
        None,
        description="""Restrict clustering to specific categories within sample annotations.
        Original annotation is tuple[str, Sequence[str]] | None
        """,
    )
    random_state: typing.Any = Field(
        0,
        description="""Change optimization initialization.
        Original annotation is _LegacyRandom
        """,
    )
    key_added: str = Field(
        "leiden",
        description="""Key under which cluster labels are added to `adata.obs`.
        Original annotation is str
        """,
    )
    adjacency: typing.Any = Field(
        None,
        description="""Sparse adjacency matrix of the graph, defaults to neighbors connectivities.
        Original annotation is CSBase | None
        """,
    )
    directed: bool | None = Field(
        None,
        description="""Indicate if the graph is directed or undirected.
        Original annotation is bool | None
        """,
    )
    use_weights: bool = Field(
        True,
        description="""Use edge weights from the graph in computation, giving more weight to stronger edges.
        Original annotation is bool
        """,
    )
    n_iterations: int = Field(
        -1,
        description="""Number of iterations of the Leiden algorithm to perform, with options for termination conditions.
        Original annotation is int
        """,
    )
    partition_type: typing.Any = Field(
        None,
        description="""Type of partition to use for clustering.
        Original annotation is type[MutableVertexPartition] | None
        """,
    )
    neighbors_key: str | None = Field(
        None,
        description="""Specify how neighbors connectivities are used as adjacency.
        Original annotation is str | None
        """,
    )
    obsp: str | None = Field(
        None,
        description="""Specify adjacency matrix using `obsp`, cannot be used simultaneously with `neighbors_key`.
        Original annotation is str | None
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""Specify whether to modify `adata` in place or create a copy.
    #     Original annotation is bool
    #     """,
    # )
    flavor: typing.Any = Field(
        "leidenalg",
        description="""Select the implementation of a specific package.
        Original annotation is Literal['leidenalg', 'igraph']
        """,
    )
    clustering_args: typing.Any = Field(
        Ellipsis,
        description="""Additional arguments to pass to the clustering algorithm.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.tl.leiden")
    _products_str_repr: list[str] = PrivateAttr(
        default=['data.obs["leiden"]', 'data.uns["leiden"]']
    )
    _data_name: str = PrivateAttr(default="adata")


class ScTlLouvain(BaseAPI):
    """
    Cluster cells into subgroups using the Louvain algorithm, with options for different parameters and settings. Requires prior computation of neighbors or passing an adjacency matrix.
    """

    adata: str = Field(
        "data",
        description="""The annotated data matrix used for clustering.
        """,
    )
    resolution: float | None = Field(
        None,
        description="""A parameter that can be adjusted to control the granularity of the clusters identified by the algorithm.
        Original annotation is float | None
        """,
    )
    random_state: typing.Any = Field(
        0,
        description="""Parameter to change the initialization of the optimization process.
        Original annotation is _LegacyRandom
        """,
    )
    restrict_to: typing.Any = Field(
        None,
        description="""Option to limit the clustering to specific categories within the sample annotations.
        Original annotation is tuple[str, Sequence[str]] | None
        """,
    )
    key_added: str = Field(
        "louvain",
        description="""The key under which the cluster labels will be added in the output data structure.
        Original annotation is str
        """,
    )
    adjacency: typing.Any = Field(
        None,
        description="""The sparse adjacency matrix of the graph, which defaults to using neighbor connectivities for clustering.
        Original annotation is CSBase | None
        """,
    )
    flavor: typing.Any = Field(
        "vtraag",
        description="""Choice between different packages for performing the clustering algorithm, with options like \'vtraag\', \'igraph\', or \'rapids\'.
        Original annotation is Literal['vtraag', 'igraph', 'rapids']
        """,
    )
    directed: bool = Field(
        True,
        description="""Determines whether the adjacency matrix should be interpreted as a directed graph.
        Original annotation is bool
        """,
    )
    use_weights: bool = Field(
        False,
        description="""Option to incorporate weights from the knn graph into the clustering process.
        Original annotation is bool
        """,
    )
    partition_type: typing.Any = Field(
        None,
        description="""Specifies the type of partitioning to use, applicable only when the flavor is set to \'vtraag\'.
        Original annotation is type[MutableVertexPartition] | None
        """,
    )
    partition_kwargs: Mapping[str, Any] = Field(
        "{}",
        description="""Keyword arguments that can be passed for partitioning when the \'vtraag\' method is being used.
        Original annotation is Mapping[str, Any]
        """,
    )
    neighbors_key: str | None = Field(
        None,
        description="""Specifies the use of neighbors connectivities as the adjacency matrix for Louvain clustering.
        Original annotation is str | None
        """,
    )
    obsp: str | None = Field(
        None,
        description="""Specifies the use of a specific adjacency matrix, with a note that both \'obsp\' and \'neighbors_key\' cannot be specified simultaneously.
        Original annotation is str | None
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""Choice to either copy the annotated data matrix or modify it in place during the clustering process.
    #     Original annotation is bool
    #     """,
    # )
    _api_name: str = PrivateAttr(default="sc.tl.louvain")
    _products_str_repr: list[str] = PrivateAttr(
        default=['data.obs["louvain"]', 'data.uns["louvain"]']
    )
    _data_name: str = PrivateAttr(default="adata")


class ScTlUmap(BaseAPI):
    """
    Embed the neighborhood graph using UMAP. UMAP is a technique for visualizing high-dimensional data by optimizing the embedding to best reflect the data\'s topology.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    min_dist: float = Field(
        0.5,
        description="""The effective minimum distance between embedded points, influencing clustering in the embedding.
        Original annotation is float
        """,
    )
    spread: float = Field(
        1.0,
        description="""The effective scale of embedded points, determining clustering in the embedding.
        Original annotation is float
        """,
    )
    n_components: int = Field(
        2,
        description="""The number of dimensions of the embedding.
        Original annotation is int
        """,
    )
    maxiter: int | None = Field(
        None,
        description="""The number of iterations of the optimization process.
        Original annotation is int | None
        """,
    )
    alpha: float = Field(
        1.0,
        description="""The initial learning rate for the embedding optimization.
        Original annotation is float
        """,
    )
    gamma: float = Field(
        1.0,
        description="""Weighting applied to negative samples in low dimensional embedding optimization.
        Original annotation is float
        """,
    )
    negative_sample_rate: int = Field(
        5,
        description="""The number of negative edge samples used per positive edge sample in optimizing the embedding.
        Original annotation is int
        """,
    )
    init_pos: typing.Any = Field(
        "spectral",
        description="""How to initialize the low dimensional embedding, with options like \'paga\' or \'random\'.
        Original annotation is _InitPos | np.ndarray | None
        """,
    )
    random_state: typing.Any = Field(
        0,
        description="""Determines the randomness in the embedding process.
        Original annotation is _LegacyRandom
        """,
    )
    a: float | None = Field(
        None,
        description="""Specific parameters controlling the embedding, set automatically if None.
        Original annotation is float | None
        """,
    )
    b: float | None = Field(
        None,
        description="""Specific parameters controlling the embedding, set automatically if None.
        Original annotation is float | None
        """,
    )
    method: typing.Any = Field(
        "umap",
        description="""Chosen implementation, like \'umap\' or \'rapids\'.
        Original annotation is Literal['umap', 'rapids']
        """,
    )
    key_added: str | None = Field(
        None,
        description="""Specifies where the embedding and parameters are stored.
        Original annotation is str | None
        """,
    )
    neighbors_key: str = Field(
        "neighbors",
        description="""Indicates where UMAP looks for neighbor settings and connectivities.
        Original annotation is str
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""Option to return a copy instead of writing to the original data.
    #     Original annotation is bool
    #     """,
    # )
    _api_name: str = PrivateAttr(default="sc.tl.umap")
    _products_str_repr: list[str] = PrivateAttr(
        default=['data.obsm["X_umap"]', 'data.uns["umap"]']
    )
    _data_name: str = PrivateAttr(default="adata")


class ScTlTsne(BaseAPI):
    """
    t-SNE algorithm for visualizing single-cell data using scikit-learn implementation, with the option for a speedup using Multicore-tSNE.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    n_pcs: int | None = Field(
        None,
        description="""Number of principal components to use, defaulting to .X if use_rep is None.
        Original annotation is int | None
        """,
    )
    use_rep: str | None = Field(
        None,
        description="""Indicates the representation to use, automatically chosen if None, with specific behavior based on the number of variables.
        Original annotation is str | None
        """,
    )
    perplexity: float = Field(
        30,
        description="""Parameter related to the number of nearest neighbors for manifold learning in t-SNE, typically between 5 and 50.
        Original annotation is float
        """,
    )
    metric: str = Field(
        "euclidean",
        description="""Distance metric used to calculate neighbors.
        Original annotation is str
        """,
    )
    early_exaggeration: float = Field(
        12,
        description="""Parameter controlling the tightness of clusters in the original and embedded space in t-SNE.
        Original annotation is float
        """,
    )
    learning_rate: float = Field(
        1000,
        description="""Critical parameter in t-SNE optimization, with a recommended range between 100 and 1000.
        Original annotation is float
        """,
    )
    random_state: typing.Any = Field(
        0,
        description="""Allows changing the initial states for optimization, with None leading to non-reproducible results.
        Original annotation is _LegacyRandom
        """,
    )
    use_fast_tsne: bool = Field(
        False,
        description="""No description available.
        Original annotation is bool
        """,
    )
    n_jobs: int | None = Field(
        None,
        description="""Number of parallel jobs for computation, defaulting to scanpy settings.
        Original annotation is int | None
        """,
    )
    # Jiahang (TODO): when prompt with "louvain ...", it prediction wrong (to be "tsne").
    # key problem: when context is long, hallucination occurs a lot. 
    # these hallucinations include adata={}, copy=True, etc.
    # a feasible method is arg modification verifier and arg importance scorer.
    # but what if the clustering label name is really tsne? then we dont need that
    # dependency? right?
    key_added: str | None = Field(
        None,
        description="""Determines where the t-SNE embedding and parameters are stored in the AnnData object.
        Original annotation is str | None
        """,
    )
    # Jiahang (TODO): when arguments scale up, hallucination occurs a lot, predicting
    # copy to be True. sucks.
    # copy: bool = Field(
    #     False,
    #     description="""Option to return a copy of the data instead of modifying the original AnnData object.
    #     Original annotation is bool
    #     """,
    # )
    _api_name: str = PrivateAttr(default="sc.tl.tsne")
    _products_str_repr: list[str] = PrivateAttr(
        default=['data.obsm["X_tsne"]', 'data.uns["tsne"]']
    )
    _data_name: str = PrivateAttr(default="adata")


class ScTlDiffmap(BaseAPI):
    """
    Diffusion maps have been proposed for visualizing single-cell data using an adapted Gaussian kernel. The width of the connectivity kernel is determined by the number of neighbors used to compute the single-cell graph.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    n_comps: int = Field(
        15,
        description="""The number of dimensions of the representation.
        Original annotation is int
        """,
    )
    neighbors_key: str | None = Field(
        None,
        description="""Specifies where to look for neighbors settings and connectivities/distance in the data structure. If not specified, default storage places are used.
        Original annotation is str | None
        """,
    )
    random_state: typing.Any = Field(
        0,
        description="""A numpy random seed.
        Original annotation is _LegacyRandom
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""Option to return a copy instead of modifying the original data.
    #     Original annotation is bool
    #     """,
    # )
    _api_name: str = PrivateAttr(default="sc.tl.diffmap")
    _products_str_repr: list[str] = PrivateAttr(
        default=['data.obsm["X_diffmap"]', 'data.uns["diffmap_evals"]']
    )
    _data_name: str = PrivateAttr(default="adata")


class ScTlEmbeddingDensity(BaseAPI):
    """
    Calculate the density of cells in an embedding (per condition) using Gaussian kernel density estimation. Density values are scaled between 0 and 1, comparable only within the same category. KDE estimate may be unreliable with insufficient cells in a category.
    """

    adata: str = Field(
        "data",
        description="""The annotated data matrix.
        """,
    )
    basis: str = Field(
        "umap",
        description="""The embedding where density calculation is done, found in `adata.obsm[\'X_[basis]\']`.
        Original annotation is str
        """,
    )
    groupby: str | None = Field(
        None,
        description="""Key for categorical observation/cell annotation used to calculate densities per category.
        Original annotation is str | None
        """,
    )
    key_added: str | None = Field(
        None,
        description="""Name of the `.obs` covariate added with density estimates.
        Original annotation is str | None
        """,
    )
    components: str | Sequence[str] | None = Field(
        None,
        description="""Limited to two components, these are the embedding dimensions for density calculation.
        Original annotation is str | Sequence[str] | None
        """,
    )
    _api_name: str = PrivateAttr(default="sc.tl.embedding_density")
    _products_str_repr: list[str] = PrivateAttr(
        default=['data.obs["umap_density"]', 'data.uns["umap_density_params"]']
    )
    _data_name: str = PrivateAttr(default="adata")


class ScTlRankGenesGroups(BaseAPI):
    """
    Rank genes for characterizing groups. Expects logarithmized data. 
    """
    # Jiahang (TODO, high priority): add prompt to gen_data_model data model doc
    # simplification llm to reduce description of args. it is not needed in doc,
    # but already filled in each arg.
    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    groupby: str = Field(
        Ellipsis,
        description="""The key of the observations grouping to consider.
        Original annotation is str
        """,
    )
    mask_var: typing.Any = Field(
        None,
        description="""Select subset of genes to use in statistical tests.
        Original annotation is NDArray[np.bool_] | str | None
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""Use `raw` attribute of `adata` if present. The default behavior is to use `raw` if present.
        Original annotation is bool | None
        """,
    )
    groups: typing.Any = Field(
        "all",
        description="""Subset of groups for comparison or `all` for all groups. Clarifies behavior with `reference` argument.
        Original annotation is Literal['all'] | Iterable[str]
        """,
    )
    reference: str = Field(
        "rest",
        description="""Compare groups to rest or a specific group. Affects gene comparison behavior.
        Original annotation is str
        """,
    )
    n_genes: int | None = Field(
        None,
        description="""Number of genes to appear in the returned tables. Defaults to all genes.
        Original annotation is int | None
        """,
    )
    rankby_abs: bool = Field(
        False,
        description="""Rank genes by absolute value of the score. Returned scores are not absolute.
        Original annotation is bool
        """,
    )
    pts: bool = Field(
        False,
        description="""Compute the fraction of cells expressing the genes.
        Original annotation is bool
        """,
    )
    key_added: str | None = Field(
        None,
        description="""The key in `adata.uns` where information is stored.
        Original annotation is str | None
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""Whether to copy `adata` or modify it inplace.
    #     Original annotation is bool
    #     """,
    # )
    method: typing.Any = Field(
        None,
        description="""Method for gene ranking, default is `t-test`. Other methods available such as `wilcoxon`, `logreg`.
        Original annotation is _Method | None
        """,
    )
    corr_method: typing.Any = Field(
        "benjamini-hochberg",
        description="""P-value correction method for specific gene ranking methods.
        Original annotation is _CorrMethod
        """,
    )
    tie_correct: bool = Field(
        False,
        description="""Use tie correction for specific gene ranking methods.
        Original annotation is bool
        """,
    )
    layer: str | None = Field(
        None,
        description="""Key from `adata.layers` to use for tests.
        Original annotation is str | None
        """,
    )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""Parameters passed to test methods, influencing logistic regression behavior.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.tl.rank_genes_groups")
    _products_str_repr: list[str] = PrivateAttr(
        default=['data.uns["rank_genes_groups"]']
    )
    _data_name: str = PrivateAttr(default="adata")


class ScTlFilterRankGenesGroups(BaseAPI):
    """
    Filter out genes based on two criteria: log fold change and fraction of genes expressing the gene within and outside the `groupby` categories. Results stored in `adata.uns[key_added]` (default: \'rank_genes_groups_filtered\').
    """

    adata: str = Field(
        "data",
        description="""No description available.
        """,
    )
    key: str | None = Field(
        None,
        description="""No description available.
        Original annotation is str | None
        """,
    )
    groupby: str | None = Field(
        None,
        description="""No description available.
        Original annotation is str | None
        """,
    )
    use_raw: bool | None = Field(
        None,
        description="""No description available.
        Original annotation is bool | None
        """,
    )
    key_added: str = Field(
        "rank_genes_groups_filtered",
        description="""No description available.
        Original annotation is str
        """,
    )
    min_in_group_fraction: float = Field(
        0.25,
        description="""No description available.
        Original annotation is float
        """,
    )
    min_fold_change: float = Field(
        1,
        description="""No description available.
        Original annotation is float
        """,
    )
    max_out_group_fraction: float = Field(
        0.5,
        description="""No description available.
        Original annotation is float
        """,
    )
    compare_abs: bool = Field(
        False,
        description="""If `True`, compare absolute values of log fold change with `min_fold_change`.
        Original annotation is bool
        """,
    )
    _api_name: str = PrivateAttr(default="sc.tl.filter_rank_genes_groups")
    _products_str_repr: list[str] = PrivateAttr(
        default=['data.uns["rank_genes_groups"]']
    )
    _data_name: str = PrivateAttr(default="adata")


class ScTlMarkerGeneOverlap(BaseAPI):
    """
    Calculate an overlap score between data-derived marker genes and provided markers. The method returns a pandas dataframe which can be used to annotate clusters based on marker gene overlaps.
    """

    adata: str = Field(
        "data",
        description="""The annotated data matrix.
        """,
    )
    reference_markers: dict[str, set] | dict[str, list] = Field(
        Ellipsis,
        description="""A marker gene dictionary object. Keys should be strings with the cell identity name and values are sets or lists of strings which match format of `adata.var_name`.
        Original annotation is dict[str, set] | dict[str, list]
        """,
    )
    key: str = Field(
        "rank_genes_groups",
        description="""The key in `adata.uns` where the rank_genes_groups output is stored. By default this is `\'rank_genes_groups`\'.
        Original annotation is str
        """,
    )
    method: typing.Any = Field(
        "overlap_count",
        description="""Method to calculate marker gene overlap. `\'overlap_count\'` uses the intersection of the gene set, `\'overlap_coef\'` uses the overlap coefficient, and `\'jaccard\'` uses the Jaccard index.
        Original annotation is _Method
        """,
    )
    normalize: Literal["reference", "data"] | None = Field(
        None,
        description="""Normalization option for the marker gene overlap output. This parameter can only be set when `method` is set to `\'overlap_count\'`.
        Original annotation is Literal['reference', 'data'] | None
        """,
    )
    top_n_markers: int | None = Field(
        None,
        description="""The number of top data-derived marker genes to use. By default the top 100 marker genes are used. If `adj_pval_threshold` is set along with `top_n_markers`, then `adj_pval_threshold` is ignored.
        Original annotation is int | None
        """,
    )
    adj_pval_threshold: float | None = Field(
        None,
        description="""A significance threshold on the adjusted p-values to select marker genes. This can only be used when adjusted p-values are calculated by `sc.tl.rank_genes_groups()`.
        Original annotation is float | None
        """,
    )
    key_added: str = Field(
        "marker_gene_overlap",
        description="""Name of the `.uns` field that will contain the marker overlap scores.
        Original annotation is str
        """,
    )
    inplace: bool = Field(
        False,
        description="""Return a marker gene dataframe or store it inplace in `adata.uns`.
        Original annotation is bool
        """,
    )
    _api_name: str = PrivateAttr(default="sc.tl.marker_gene_overlap")
    _products_str_repr: list[str] = PrivateAttr(
        default=['data.uns["marker_gene_overlap"]']
    )
    _data_name: str = PrivateAttr(default="adata")


class ScTlScoreGenes(BaseAPI):
    """
    Score a set of genes. The score is the average expression of a set of genes after subtraction by the average expression of a reference set of genes. Parameters include annotated data matrix, gene list, control as reference, number of reference genes, gene pool, number of expression level bins, score name, random seed, copy option, using raw data, and layer key.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    gene_list: typing.Any = Field(
        Ellipsis,
        description="""List of gene names used for score calculation.
        Original annotation is Sequence[str] | pd.Index[str]
        """,
    )
    ctrl_as_ref: bool = Field(
        True,
        description="""Allow using control genes as reference, set to False in Scanpy 2.0.
        Original annotation is bool
        """,
    )
    ctrl_size: int = Field(
        50,
        description="""Number of reference genes to sample from each bin.
        Original annotation is int
        """,
    )
    gene_pool: typing.Any = Field(
        None,
        description="""Genes for sampling the reference set, default is all genes.
        Original annotation is Sequence[str] | pd.Index[str] | None
        """,
    )
    n_bins: int = Field(
        25,
        description="""Number of expression level bins for sampling.
        Original annotation is int
        """,
    )
    score_name: str = Field(
        "score",
        description="""Name of the field to be added in `.obs`.
        Original annotation is str
        """,
    )
    random_state: typing.Any = Field(
        0,
        description="""Random seed for sampling.
        Original annotation is _LegacyRandom
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""Option to copy `adata` or modify it inplace.
    #     Original annotation is bool
    #     """,
    # )
    use_raw: bool | None = Field(
        None,
        description="""Option to use `raw` attribute of `adata`, defaults to True if `.raw` is present.
        Original annotation is bool | None
        """,
    )
    layer: str | None = Field(
        None,
        description="""Key from `adata.layers` to perform tests on.
        Original annotation is str | None
        """,
    )
    _api_name: str = PrivateAttr(default="sc.tl.score_genes")
    _products_str_repr: list[str] = PrivateAttr(default=['data.obs["score"]'])
    _data_name: str = PrivateAttr(default="adata")


class ScTlScoreGenesCellCycle(BaseAPI):
    """
    Score cell cycle genes :cite:p:`Satija2015`. Given two lists of genes associated to S phase and G2M phase, calculates scores and assigns a cell cycle phase (G1, S or G2M). See :func:`~scanpy.tl.score_genes` for more explanation.
    """

    adata: str = Field(
        "data",
        description="""The annotated data matrix.
        """,
    )
    s_genes: typing.Any = Field(
        Ellipsis,
        description="""List of genes associated with S phase.
        Original annotation is Sequence[str]
        """,
    )
    g2m_genes: typing.Any = Field(
        Ellipsis,
        description="""List of genes associated with G2M phase.
        Original annotation is Sequence[str]
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""Copy `adata` or modify it inplace.
    #     Original annotation is bool
    #     """,
    # )
    _api_name: str = PrivateAttr(default="sc.tl.score_genes_cell_cycle")
    _products_str_repr: list[str] = PrivateAttr(
        default=['data.obs["S_score"]', 'data.obs["G2M_score"]', 'data.obs["phase"]']
    )
    _data_name: str = PrivateAttr(default="adata")


class ScTlDrawGraph(BaseAPI):
    """
    Force-directed graph drawing alternative to tSNE that often preserves the data topology. Requires running scanpy.pp.neighbors first. Offers multiple layout options and can be used to visualize single-cell data.
    """

    adata: str = Field(
        "data",
        description="""Annotated data matrix.
        """,
    )
    layout: typing.Any = Field(
        "fa",
        description="""\'fa\' (ForceAtlas2) or any valid igraph layout like \'fr\' (Fruchterman Reingold), \'grid_fr\' (Grid Fruchterman Reingold), \'kk\' (Kamadi Kawai), \'lgl\' (Large Graph), \'drl\' (Distributed Recursive Layout), \'rt\' (Reingold Tilford tree layout).
        Original annotation is _Layout
        """,
    )
    init_pos: str | bool | None = Field(
        None,
        description="""Defines precomputed coordinates for initialization or random initialization.
        Original annotation is str | bool | None
        """,
    )
    root: int | None = Field(
        None,
        description="""Root for tree layouts.
        Original annotation is int | None
        """,
    )
    random_state: typing.Any = Field(
        0,
        description="""For layouts with random initialization, changes the initial states for optimization.
        Original annotation is _LegacyRandom
        """,
    )
    n_jobs: int | None = Field(
        None,
        description="""No description available.
        Original annotation is int | None
        """,
    )
    adjacency: typing.Any = Field(
        None,
        description="""Sparse adjacency matrix of the graph, defaults to neighbors connectivities.
        Original annotation is SpBase | None
        """,
    )
    key_added_ext: str | None = Field(
        None,
        description="""By default, append \'layout\'.
        Original annotation is str | None
        """,
    )
    neighbors_key: str | None = Field(
        None,
        description="""Specifies where to look for connectivities in the data matrix.
        Original annotation is str | None
        """,
    )
    obsp: str | None = Field(
        None,
        description="""Specifies the adjacency matrix to be used. Cannot specify both obsp and neighbors_key simultaneously.
        Original annotation is str | None
        """,
    )
    # copy: bool = Field(
    #     False,
    #     description="""Returns a copy instead of modifying the original data.
    #     Original annotation is bool
    #     """,
    # )
    kwds: typing.Any = Field(
        Ellipsis,
        description="""No description available.
        """,
    )
    _api_name: str = PrivateAttr(default="sc.tl.draw_graph")
    _products_str_repr: list[str] = PrivateAttr(
        default=['data.uns["draw_graph"]', 'data.obsm["X_draw_graph_fa"]']
    )
    _data_name: str = PrivateAttr(default="adata")


TOOLS_DICT = {
    "sc.tl.paga": ScTlPaga,
    "sc.tl.leiden": ScTlLeiden,
    "sc.tl.louvain": ScTlLouvain,
    "sc.tl.umap": ScTlUmap,
    "sc.tl.tsne": ScTlTsne,
    "sc.tl.diffmap": ScTlDiffmap,
    "sc.tl.embedding_density": ScTlEmbeddingDensity,
    "sc.tl.rank_genes_groups": ScTlRankGenesGroups,
    "sc.tl.filter_rank_genes_groups": ScTlFilterRankGenesGroups,
    "sc.tl.marker_gene_overlap": ScTlMarkerGeneOverlap,
    "sc.tl.score_genes": ScTlScoreGenes,
    "sc.tl.score_genes_cell_cycle": ScTlScoreGenesCellCycle,
    "sc.tl.draw_graph": ScTlDrawGraph,
}

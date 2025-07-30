from importlib import import_module

# Jiahang (TODO): it worth reconsidering the key since it is completely the same as list index. 
# However, without such key, it would be difficult for developers to specify incremental 
# dependency discovery. 
#
# one way should bind each version of api_chains.py to its dependency graph. Then deploy
# code difference checker to conduct incremental dependency discovery.
# this would be too difficult. For now we use this dumb way to track the index.
DATA = {
    0:
    {
        'query': 'Plot umap embedding of cells.',
        'codes': \
        """
        sc.pp.neighbors(adata=data)
        sc.tl.umap(adata=data)
        sc.pl.scatter(adata=data, basis='umap')
        """
    },
    1:
    {
        'query': 'Plot umap embedding of cells, which are colored by leiden clustering.',
        'codes': \
        """
        sc.pp.neighbors(adata=data)
        sc.tl.umap(adata=data)
        sc.tl.leiden(adata=data)
        sc.pl.umap(adata=data, color='leiden')
        """
    },
    2:
    {
        
        'query': "Plot heatmap of gene expressions of genes ['Gata2', 'Gata1', 'Fog1'], where cells are clustered by louvain algorithm.",
        'codes': \
        """
        sc.pp.neighbors(adata=data)
        sc.tl.louvain(adata=data)
        sc.pl.heatmap(adata=data, var_names=['Gata2', 'Gata1', 'Fog1'], groupby='louvain')
        """
    },
    3:
    {
        'query': "Plot dotplot with dendrogram of gene expressions of genes ['Gata2', 'Gata1', 'Fog1'], where cells are clustered by louvain algorithm.",
        'codes': \
        """
        sc.pp.neighbors(adata=data)
        sc.tl.louvain(adata=data)
        sc.pl.dotplot(adata=data, var_names=['Gata2', 'Gata1', 'Fog1'], groupby='louvain')
        """
    },
    4:
    {
        'query': "Plot violinplot of gene expressions of genes ['Gata2', 'Gata1', 'Fog1'], where cells are clustered by louvain algorithm.",
        'codes': \
        """
        sc.pp.neighbors(adata=data)
        sc.tl.louvain(adata=data)
        sc.pl.violin(adata=data, var_names=['Gata2', 'Gata1', 'Fog1'], groupby='louvain')
        """
    },
    5:
    {
        'query': "visualize dendrogram of clusters defined by louvain algorithm on cells.",
        'codes': \
        """
        sc.pp.neighbors(adata=data)
        sc.tl.louvain(adata=data)
        sc.pl.dendrogram(adata=data, groupby='louvain')
        """
    },
    6:
    {
        'query': "visualize diffusion map embedding of cells which are clustered by leiden algorithm.",
        'codes': \
        """
        sc.pp.neighbors(adata=data)
        sc.tl.diffmap(adata=data)
        sc.tl.leiden(adata=data)
        sc.pl.diffmap(adata=data, color='leiden')
        """
    },
    7:
    {
        'query': "visualize dispersions versus mean expressions of genes in scatter plot.",
        'codes': \
        """
        sc.pp.log1p(data=data)
        sc.pp.highly_variable_genes(adata=data)
        sc.pl.highly_variable_genes(adata=data)
        """
    },
    8:
    {
        'query': "visualize PCA embedding of cells.",
        'codes': \
        """
        sc.pp.pca(data=data)
        sc.pl.pca(adata=data)
        """
    },
    9:
    {
        'query': "visualize PCA embedding of cells which are clustered by louvain algorithm.",
        'codes': \
        """
        sc.pp.neighbors(adata=data)
        sc.tl.louvain(adata=data)
        sc.pl.pca(adata=data, color='louvain')
        """
    },
    10:
    {
        'query': "visualize tSNE embedding of cells which are clustered by leiden algorithm.",
        'codes': \
        """
        sc.pp.neighbors(adata=data)
        sc.tl.tsne(adata=data)
        sc.tl.leiden(adata=data)
        sc.pl.tsne(adata=data, color='leiden')
        """
    },
    11:
    {
        'query': "visualize umap embedding density of cells.",
        'codes': \
        """
        sc.pp.neighbors(adata=data)
        sc.tl.umap(adata=data)
        sc.tl.embedding_density(adata=data, basis='umap')
        sc.pl.embedding_density(adata=data, basis='umap')
        """
    },
    12:
    {
        'query': None,
        'codes': \
        """
        sc.pp.pca(data=data)
        sc.pl.pca_variance_ratio(adata=data)
        """
    },
    13:
    {
        'query': None,
        'codes': \
        """
        sc.pp.neighbors(adata=data)
        sc.tl.leiden(adata=data)
        sc.tl.rank_genes_groups(adata=data, groupby='leiden')
        sc.pl.rank_genes_groups_dotplot(adata=data, groupby='leiden')
        """
    },
    14:
    {
        'query': None,
        'codes': \
        """
        sc.pp.neighbors(adata=data)
        sc.tl.leiden(adata=data)
        sc.pl.correlation_matrix(adata=data, groupby='leiden')        
        """
    },
    # compile above before 06.03.2025
    # Jiahang (TODO): incremental dependency discovery.


}
from resource.constants import BUILTIN, NO_FIRST_ARG_NAME

SCANPY_PP_SINGLE_LINE_SIMPLE_ARG = [
    # single line + at most 3 args (simple args), all scanpy.pp
    [
        {
            'query': "filter out cells which have number of gene expression counts less than 20.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pp.filter_cells',
            'prep': "",
            'args': {
                'data': 'adata',
                'min_counts': 20
            }
        }
    ],

    [
        {
            'query': "filter out genes which have number of expressed cells larger than 1000.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pp.filter_genes',
            'prep': "",
            'args': {
                'data': 'adata',
                'max_cells': 1000
            }
        }
    ],

    [
        {
            'query': "logarithmize gene expression data.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pp.log1p',
            'prep': "",
            'args': {
                'data': 'adata'
            }
        }
    ],


    [
        {
            'query': "perform PCA on the data.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pp.pca',
            'prep': "",
            'args': {
                'data': 'adata'
            }
        }
    ],

    [
        {
            'query': "normalize data such that every cell has the same total counts.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pp.normalize_total',
            'prep': "",
            'args': {
                'adata': 'adata'
            }
        }
    ],

    [
        {
            'query': "randomly and uniformly sample 80% of observations from data.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pp.sample',
            'prep': "",
            'args': {
                'data': 'adata',
                'fraction': '0.8'
            }
        }
    ],

    [
        {
            'query': "perform z-score normalization on data.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pp.scale',
            'prep': "",
            'args': {
                'data': 'adata'
            }
        }
    ],

    [
        {
            'query': "logarithmize gene expression data with base 5.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pp.log1p',
            'prep': "",
            'args': {
                'data': 'adata',
                'base': 5
            }
        }
    ],

    [
        {
            'query': "perform PCA on the data while preserving 10 principal components.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pp.pca',
            'prep': "",
            'args': {
                'data': 'adata',
                'n_comps': 10
            }
        }
    ],

    [
        {
            'query': "normalize data such that every cell has the same total counts 100.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pp.normalize_total',
            'prep': "",
            'args': {
                'adata': 'adata',
                'target_sum': 100
            }
        }
    ],

    [
        {
            'query': "normalize data to make every cell have the same total counts 100 with highly expressed genes being removed for normalization factor computation.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pp.normalize_total',
            'prep': "",
            'args': {
                'adata': 'adata',
                'target_sum': 100,
                'exclude_highly_expressed': True
            }
        }
    ],

    [
        {
            'query': "Compute kNN graph of cells, with k being 10.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata',
                'n_neighbors': 10
            }
        }
    ],

    # single line 


    # [
    #     {
    #         'api': 'sc.pp.highly_variable_genes',
    #         'prep': "",
    #         'args': {
    #             'adata': 'adata',
    #             'n_top_genes': '50'
    #         }
    #     },
    #     {
    #         'api': 'sc.pp.log1p',
    #         'args': {
    #             'data': 'adata'
    #         }
    #     }
    # ], 

    

    

    # # single line a little complex args
    # {
    #     'api': 'sc.pp.normalize_total',
    #     'dependent_api': [],
    #     'query': "normalize data to make every cell have the same total counts 100 with highly expressed genes being removed for normalization factor computation.",
    #     'prep': "",
    #     'args': {
    #         'data': 'adata',
    #         'target_sum': '100',
    #         'exclude_highly_expressed': 'True'
    #     }
    # },

    # {
    #     'query': "calculate quality control metrics for 'pre-mRNA processing factor 31' genes with name starting with 'RP11', 'microRNA' genes with name starting with 'MIR', and 'ribosomal protein' genes with name starting with 'RPL' in the data.",
    #     'prep': 'adata.var["RP11"] = adata.var_names.str.startswith("RP11")\nadata.var["MIR"] = adata.var_names.str.startswith("MIR")\nadata.var["RPL"] = adata.var_names.str.startswith("RPL")',
    #     'args': {
    #         'data': 'adata',
    #         'qc_vars': '["RP11", "MIR", "RPL"]',
    #         'inplace': 'True'
    #     }
    # },
]

SCANPY_TL_MULTI_LINE_SIMPLE_ARG = [
    # multiple lines + at most 3 args (simple args) for each API, all scanpy.tl
    # 0
    [
        {
            'query': "compute t-SNE coordinates of data.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.tl.tsne',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': []
        }
    ],

    # 1
    [
        {
            'query': "compute UMAP embedding of data.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.tl.umap',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            'produce': [
                'adata.obsm["X_umap"]',
                'adata.uns["umap"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    # 2
    [
        {
            'query': 'compute diffusion map embedding of data.',
            'state_name': "scanpy"
        },
        {
            'api': 'sc.tl.diffmap',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obsm["X_diffmap"]',
                'adata.uns["diffmap_evals"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    # 3
    [
        {
            'query': 'compute cell embedding density of diffusiom map embedding.',
            'state_name': "scanpy"
        },
        {
            'api': 'sc.tl.embedding_density',
            'prep': "",
            'args': {
                'adata': 'adata',
                'basis': 'diffmap'
            },
            'arg_types': {
                'adata': 'object',
                'basis': 'str'
            },
            
            'produce': []
        },
        {
            'api': 'sc.tl.diffmap',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obsm["X_diffmap"]',
                'adata.uns["diffmap_evals"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    # 4
    [
        {
            'query': 'clutsering cells using Leiden algorithm.',
            'state_name': "scanpy"
        },
        {
            'api': 'sc.tl.leiden',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    # 5
    [
        {
            'query': 'clutsering cells using Louvain algorithm.',
            'state_name': "scanpy"
        },
        {
            'api': 'sc.tl.louvain',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    # 6
    [
        {
            'query': "perform hierarchical clustering of cells based on louvain clustering.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.tl.dendrogram',
            'prep': "",
            'args': {
                'adata': 'adata',
                'groupby': 'louvain'
            },
            'arg_types': {
                'adata': 'object',
                'groupby': 'str'
            },
        },
        {
            'api': 'sc.tl.louvain',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            'produce': [
                'adata.obs["louvain"]',
                'adata.uns["louvain"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    # 7
    [
        {
            'query': "compute diffusion pseudotime of cells given that the 0-th cell is set to the root cell.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.tl.dpt',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
        },
        {
            'api': 'adata.uns.__setitem__',
            'prep': "",
            'args': {
                'key': 'iroot',
                'value': 0
            },
            'arg_types': {
                'key': 'str',
                'value': 'int'
            },
            "produce": [
                'adata.uns["iroot"]'
            ],
            "special": [BUILTIN]
        },
        {
            'api': 'sc.tl.diffmap',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            'produce': [
                'adata.obsm["X_diffmap"]',
                'adata.uns["diffmap_evals"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],
    # 8
    [
        {
            'query': "rank genes based on their expression in different clusters of cells, where cells are clustered by louvain algorithm.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.tl.rank_genes_groups',
            'prep': "",
            'args': {
                'adata': 'adata',
                'groupby': 'louvain'
            },
            'arg_types': {
                'adata': 'object',
                'groupby': 'str'
            },
        },
        {
            'api': 'sc.tl.louvain',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obs["louvain"]',
                'adata.uns["louvain"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        },
        {
            'api': 'sc.pp.log1p',
            'prep': "",
            'args': {
                'data': 'adata'
            },
            'arg_types': {
                'data': 'object'
            },
            
            'produce': [
                'adata.X'
            ],
            'special': [NO_FIRST_ARG_NAME]
        }
    ]

    # 9

]

SCANPY_PL_MULTI_LINE_SIMPLE_ARG = [
    # multiple lines + at most 3 args (simple args) for each API, all scanpy.pl
    [
        {
            'query': 'Plot umap embedding of cells.',
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pl.scatter',
            'prep': "",
            'args': {
                'adata': 'adata',
                'basis': 'umap'
            },
            'arg_types': {
                'adata': 'object',
                'basis': 'str'
            },
        },
        {
            'api': 'sc.tl.umap',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obsm["X_umap"]',
                'adata.uns["umap"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    [
        {
            'query': 'Plot umap embedding of cells, where cells are colored by louvain clustering.',
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pl.umap',
            'prep': "",
            'args': {
                'adata': 'adata',
                'color': 'leiden'
            },
            'arg_types': {
                'adata': 'object',
                'color': 'str'
            },
        },
        {
            'api': 'sc.tl.leiden',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obs["leiden"]',
                'adata.uns["leiden"]'
            ]
        },
        {
            'api': 'sc.tl.umap',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obsm["X_umap"]',
                'adata.uns["umap"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    [
        {
            'query': "Plot heatmap of gene expressions of genes ['TMSB4X', 'MALAT1', 'B2M'], where cells are clustered by louvain algorithm.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pl.heatmap',
            'prep': "",
            'args': {
                'adata': 'adata',
                'var_names': ['TMSB4X', 'MALAT1', 'B2M'],
                'groupby': 'louvain'
            },
            'arg_types': {
                'adata': 'object',
                'var_names': 'list',
                'groupby': 'str'
            },
        },
        {
            'api': 'sc.tl.louvain',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obs["louvain"]',
                'adata.uns["louvain"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    [
        {
            'query': "Plot dotplot with dendrogram of gene expressions of genes ['TMSB4X', 'MALAT1', 'B2M'], where cells are clustered by louvain algorithm.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pl.dotplot',
            'prep': "",
            'args': {
                'adata': 'adata',
                'var_names': ['TMSB4X', 'MALAT1', 'B2M'],
                'groupby': 'louvain'
            },
            'arg_types': {
                'adata': 'object',
                'var_names': 'list',
                'groupby': 'str'
            },
        },
        {
            'api': 'sc.tl.louvain',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obs["louvain"]',
                'adata.uns["louvain"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    [
        {
            'query': "Plot violin of gene expressions of genes ['TMSB4X', 'MALAT1', 'B2M'], where cells are clustered by louvain algorithm. ",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pl.violin',
            'prep': "",
            'args': {
                'adata': 'adata',
                'keys': ['TMSB4X', 'MALAT1', 'B2M'],
                'groupby': 'louvain'
            },
            'arg_types': {
                'adata': 'object',
                'keys': 'list',
                'groupby': 'str'
            },
        },
        {
            'api': 'sc.tl.louvain',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obs["louvain"]',
                'adata.uns["louvain"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    [
        {
            'query': "visualize dendrogram of clusters defined by louvain algorithm on cells.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pl.dendrogram',
            'prep': "",
            'args': {
                'adata': 'adata',
                'groupby': 'louvain'
            },
            'arg_types': {
                'adata': 'object',
                'groupby': 'str'
            },
        },
        {
            'api': 'sc.tl.louvain',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obs["louvain"]',
                'adata.uns["louvain"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    [
        {
            'query': "visualize diffusion map embedding of cells which are colored by leiden algorithm.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pl.diffmap',
            'prep': "",
            'args': {
                'adata': 'adata',
                'color': 'leiden'
            },
            'arg_types': {
                'adata': 'object',
                'color': 'str'
            },
        },
        {
            'api': 'sc.tl.leiden',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obs["leiden"]',
                'adata.uns["leiden"]'
            ]
        },
        {
            'api': 'sc.tl.diffmap',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obsm["X_diffmap"]',
                'adata.uns["diffmap_evals"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    [
        {
            'query': "visualize PCA embedding of cells which are colored by louvain algorithm.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pl.pca',
            'prep': "",
            'args': {
                'adata': 'adata',
                'color': 'louvain'
            },
            'arg_types': {
                'adata': 'object',
                'color': 'str'
            },
        },
        {
            'api': 'sc.tl.louvain',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obs["louvain"]',
                'adata.uns["louvain"]'
            ]
        },
        {
            'api': 'sc.tl.pca',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
        }
    ],

    [
        {
            'query': "visualize dispersions and mean expressions of highly variable genes in scatter plot.",
            'state_name': "scanpy",
        },
        {
            'api': 'sc.pl.highly_variable_genes',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
        },
        {
            'api': 'sc.pp.highly_variable_genes',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.var["highly_variable"]',
                'adata.var["means"]',
                'adata.var["dispersions"]',
                'adata.var["dispersions_norm"]',
                'adata.var["variances"]',
                'adata.var["variances_norm"]',
                'adata.var["highly_variable_rank"]',
                'adata.var["highly_variable_nbatches"]',
                'adata.var["highly_variable_intersection"]'
            ],
            '_comment': "These products are curated from doc, from 'variances' to the end are actually non-existent."
                        "Products are not always fully generated, such as the current case."
                        "When testing dependencies, results would show non-existent dependencies. "
                        "Although we already fixed this problem in dependency finder program,"
                        "this is still a problematic software design making return values unclear and unfixed."
                        "We should encourage fixed api name, arguments and return values."
                        "In the meanwhile, returning an object is acceptable only if it is fixed."
                        "Note that we hope products can be automatically extracted from doc through LLM."
                        "If doc provides vague information products, then we believe it is poorly designed."
        },
        {
            'api': 'sc.pp.log1p',
            'prep': "",
            'args': {
                'data': 'adata'
            },
            'arg_types': {
                'data': 'object',
            },
            'produce': [
                'adata.X'
            ],
            'special': [NO_FIRST_ARG_NAME]
        }
    ],

    [
        {
            'query': "visualize the top 2 principal components of PCA of data in a scatter plot, where cells are colored by louvain clustering.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pl.pca',
            'prep': "",
            'args': {
                'adata': 'adata',
                'color': 'louvain'
            },
            'arg_types': {
                'adata': 'object',
                'color': 'str'
            },
        },
        {
            'api': 'sc.tl.louvain',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obs["louvain"]',
                'adata.uns["louvain"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    [
        {
            'query': "visualize density of cells in UMAP embedding.",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pl.embedding_density',
            'prep': "",
            'args': {
                'adata': 'adata',
                'basis': 'umap'
            },
            'arg_types': {
                'adata': 'object',
                'basis': 'str'
            },
        },
        {
            'api': 'sc.tl.embedding_density',
            'prep': "",
            'args': {
                'adata': 'adata',
                'basis': 'umap'
            },
            'arg_types': {
                'adata': 'object',
                'basis': 'str'
            },
            'produce': [
                'adata.obs["umap_density"]',
                'adata.uns["umap_density_params"]'
            ]
        },
        {
            'api': 'sc.tl.umap',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obsm["X_umap"]',
                'adata.uns["umap"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object',
            },
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    [
        {
            'query': "",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pl.pca_variance_ratio',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': []
        },
        {
            'api': 'sc.pp.pca',
            'prep': "",
            'args': {
                'data': 'adata'
            },
            'arg_types': {
                'data': 'object'
            },
            
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]'
            ]
        },
    ],

    [
        {
            'query': "",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pl.rank_genes_groups_dotplot',
            'prep': "",
            'args': {
                'adata': 'adata',
                'groupby': 'leiden'
            },
            'arg_types': {
                'adata': 'object',
                'groupby': 'str'
            },
            
        },
        {
            'api': 'sc.tl.rank_genes_groups',
            'prep': "",
            'args': {
                'adata': 'adata',
                'groupby': 'leiden'
            },
            'arg_types': {
                'adata': 'object',
                'groupby': 'str'
            },
            
            'produce': [
                'adata.uns["rank_genes_groups"]'
            ]
        },
        {
            'api': 'sc.tl.leiden',
            'prep': "",
            'args': {
                'adata': 'adata',
            },
            'arg_types': {
                'adata': 'object',
            },
            
            'produce': [
                'adata.obs["leiden"]',
                'adata.uns["leiden"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

    [
        {
            'query': "",
            'state_name': "scanpy"
        },
        {
            'api': 'sc.pl.correlation_matrix',
            'prep': "",
            'args': {
                'adata': 'adata',
                'groupby': 'leiden'
            },
            'arg_types': {
                'adata': 'object',
                'groupby': 'str'
            },
            
        },
        {
            'api': 'sc.tl.leiden',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obs["leiden"]',
                'adata.uns["leiden"]'
            ]
        },
        {
            'api': 'sc.pp.neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obsm["X_pca"]',
                'adata.varm["PCs"]',
                'adata.uns["pca"]',
                'adata.uns["neighbors"]',
                'adata.obsp["distances"]',
                'adata.obsp["connectivities"]'
            ]
        }
    ],

]

SQUIDPY_PL_MULTI_LINE_FROM_DOC = [
    [
        {
            'query': "",
            'state_name': "squidpy"
        },
        {
            'api': 'sq.pl.co_occurrence',
            'prep': "",
            'args': {
                'adata': 'adata',
                'cluster_key': 'cell type',
                'clusters': ['basal CK tumor cell', 'T cells']
            },
            'arg_types': {
                'adata': 'object',
                'cluster_key': 'str',
                'clusters': 'list'
            },
            
            
        },
        {
            'api': 'sq.gr.co_occurrence',
            'prep': "",
            'args': {
                'adata': 'adata',
                'cluster_key': 'cell type',
            },
            'arg_types': {
                'adata': 'object',
                'cluster_key': 'str',
            },
            
            'produce': [
                'adata.uns["cell type_co_occurrence"]',
            ]
        },
        # {
        #     'api': 'sq.datasets.imc',
        #     'prep': "",
        #     'args': {},
        #     'arg_types': {},
        #     'produce': [
        #         'adata.obs["cell type"]',
        #         'adata.uns["cell type_colors"]',
        #         'adata.obsm["spatial"]',
        #     ],
        #     'return': 'adata',
        # }
    ],

    [
        {
            'query': "visualize neighborhood enrichment of cell types.",
            'state_name': "squidpy"
        },
        {
            'api': 'sq.pl.nhood_enrichment',
            'prep': "",
            'args': {
                'adata': 'adata',
                'cluster_key': 'cell type'
            },
            'arg_types': {
                'adata': 'object',
                'cluster_key': 'str'
            },
            
        },
        {
            'api': 'sq.gr.nhood_enrichment',
            'prep': "",
            'args': {
                'adata': 'adata',
                'cluster_key': 'cell type'
            },
            'arg_types': {
                'adata': 'object',
                'cluster_key': 'str'
            },
            
            'produce': [
                'adata.uns["cell type_nhood_enrichment"]',
            ]
        },
        {
            'api': 'sq.gr.spatial_neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obsp["spatial_connectivities"]',
                'adata.obsp["spatial_distances"]',
                'adata.uns["spatial_neighbors"]'
            ],
            "_comment": "The produce key spatial_neighbor is incorrectly written as spatial in doc."
        },
        # {
        #     'api': 'sq.datasets.imc',
        #     'prep': "",
        #     'args': {},
        #     'arg_types': {},
        #     'produce': [
        #         'adata.obs["cell type"]',
        #         'adata.uns["cell type_colors"]',
        #         'adata.obsm["spatial"]',
        #     ],
        #     'return': 'adata',
        # }
    ],

    [
        {
            'query': "visualize interaction matrix of cell types.",
            'state_name': "squidpy"
        },
        {
            'api': 'sq.pl.interaction_matrix',
            'prep': "",
            'args': {
                'adata': 'adata',
                'cluster_key': 'cell type'
            },
            'arg_types': {
                'adata': 'object',
                'cluster_key': 'str'
            },
            
        },
        {
            'api': 'sq.gr.interaction_matrix',
            'prep': "",
            'args': {
                'adata': 'adata',
                'cluster_key': 'cell type'
            },
            'arg_types': {
                'adata': 'object',
                'cluster_key': 'str'
            },
            
            'produce': [
                'adata.uns["cell type_interactions"]',
            ]
        },
        {
            'api': 'sq.gr.spatial_neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obsp["spatial_connectivities"]',
                'adata.obsp["spatial_distances"]',
                'adata.uns["spatial_neighbors"]'
            ],
        },
        # {
        #     'api': 'sq.datasets.imc',
        #     'prep': "",
        #     'args': {},
        #     'arg_types': {},
        #     'produce': [
        #         'adata.obs["cell type"]',
        #         'adata.uns["cell type_colors"]',
        #         'adata.obsm["spatial"]',
        #     ],
        #     'return': 'adata',
        # },
    ],

    [
        {
            'query': "visualize centrality scores of cell types.",
            'state_name': "squidpy"
        },
        {
            'api': 'sq.pl.centrality_scores',
            'prep': "",
            'args': {
                'adata': 'adata',
                'cluster_key': 'cell type',
                'figsize': (20, 5),
                's': 200,
            },
            'arg_types': {
                'adata': 'object',
                'cluster_key': 'str',
                'figsize': 'tuple',
                's': 'int',
            },
            
            '_comment': "figsize and s are not necessary arguments, but they are used in the example "
                        "since I found the figure is too poor and scatter too small to be visible to users "
                        "if not setting them.",
        },
        {
            'api': 'sq.gr.centrality_scores',
            'prep': "",
            'args': {
                'adata': 'adata',
                'cluster_key': 'cell type'
            },
            'arg_types': {
                'adata': 'object',
                'cluster_key': 'str'
            },
            
            'produce': [
                'adata.uns["cell type_centrality_scores"]',
            ],
        },
        {
            'api': 'sq.gr.spatial_neighbors',
            'prep': "",
            'args': {
                'adata': 'adata',
            },
            'arg_types': {
                'adata': 'object',
            },
            
            'produce': [
                'adata.obsp["spatial_connectivities"]',
                'adata.obsp["spatial_distances"]',
                'adata.uns["spatial_neighbors"]',
            ],
        },
        # {
        #     'api': 'sq.datasets.imc',
        #     'prep': "",
        #     'args': {},
        #     'arg_types': {},
        #     'produce': [
        #         'adata.obs["cell type"]',
        #         'adata.uns["cell type_colors"]',
        #         'adata.obsm["spatial"]',
        #     ],
        #     'return': 'adata',
        # },
    ],

    [
        {
            'query': "",
            'state_name': "squidpy"
        },
        {
            'api': 'sq.pl.ripley',
            'prep': "",
            'args': {
                'adata': 'adata',
                'cluster_key': 'cell type'
            },
            'arg_types': {
                'adata': 'object',
                'cluster_key': 'str'
            },
            
        },
        {
            'api': 'sq.gr.ripley',
            'prep': "",
            'args': {
                'adata': 'adata',
                'cluster_key': 'cell type'
            },
            'arg_types': {
                'adata': 'object',
                'cluster_key': 'str'
            },
            
            'produce': [
                'adata.uns["cell type_ripley_F"]',
            ],
            "_comment": "The produce key cell type_ripley_F is unclear in doc."
        },
        {
            'api': 'sq.gr.spatial_neighbors',
            'prep': "",
            'args': {
                'adata': 'adata'
            },
            'arg_types': {
                'adata': 'object'
            },
            
            'produce': [
                'adata.obsp["spatial_connectivities"]',
                'adata.obsp["spatial_distances"]',
                'adata.uns["spatial_neighbors"]'
            ],
        },
        # {
        #     'api': 'sq.datasets.imc',
        #     'prep': "",
        #     'args': {},
        #     'arg_types': {},
        #     'produce': [
        #         'adata.obs["cell type"]',
        #         'adata.uns["cell type_colors"]',
        #         'adata.obsm["spatial"]',
        #     ],
        #     'return': 'adata',
        # },
    ],

    
]  

ALL_API = {
    'SCANPY_PP_SINGLE_LINE_SIMPLE_ARG': SCANPY_PP_SINGLE_LINE_SIMPLE_ARG,
    'SCANPY_TL_MULTI_LINE_SIMPLE_ARG': SCANPY_TL_MULTI_LINE_SIMPLE_ARG,
    'SCANPY_PL_MULTI_LINE_SIMPLE_ARG': SCANPY_PL_MULTI_LINE_SIMPLE_ARG,
    'SQUIDPY_PL_MULTI_LINE_FROM_DOC': SQUIDPY_PL_MULTI_LINE_FROM_DOC
}
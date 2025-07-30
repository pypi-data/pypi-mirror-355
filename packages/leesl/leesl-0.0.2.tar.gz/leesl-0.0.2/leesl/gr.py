from scipy import sparse

def generate_matrix(adata, gene_list1, gene_list2=None):
    """
    Generate matrices X and Y from the given gene lists and store them in adata.uns.

    Parameters:
    -----------
    adata : AnnData
        Annotated data matrix.
    gene_list1 : list
        List of genes for the first matrix.
    gene_list2 : list, optional
        List of genes for the second matrix. If None, uses gene_list1.

    This function updates adata in-place.
    """
    #is there gene_list2
    was_there_gene_list2 = False if gene_list2 is None else True

    if gene_list2 is None:
        gene_list2 = gene_list1
    else:
        #make sure two lists are of the same length
        if len(gene_list1) != len(gene_list2):
            print(f"Length of gene_list1 is {len(gene_list1)} and length of gene_list2 is {len(gene_list2)}")
            print(f"gene_list1: {gene_list1}")
            print(f"gene_list2: {gene_list2}")
            raise ValueError("gene_list1 and gene_list2 must have the same length")
    
    gene_indices1 = [adata.var_names.get_loc(gene) for gene in gene_list1]
    gene_indices2 = [adata.var_names.get_loc(gene) for gene in gene_list2]
    
    X = adata.X[:, gene_indices1]
    Y = adata.X[:, gene_indices2]
    if not sparse.issparse(X):
        X = sparse.csr_matrix(X)
    
    
    if not sparse.issparse(Y):
        Y = sparse.csr_matrix(Y)
        
    # Store X and Y in adata.uns
    adata.uns['lee_X'] = X
    adata.uns['lee_Y'] = Y
    adata.uns['lee_gene_list1'] = gene_list1
    adata.uns['lee_gene_list2'] = gene_list2
    adata.uns['lee_was_there_gene_list2'] = was_there_gene_list2

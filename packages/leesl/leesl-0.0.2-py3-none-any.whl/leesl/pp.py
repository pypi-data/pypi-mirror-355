
import numpy as np
import pandas as pd
from esda import Spatial_Pearson
from scipy import sparse
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm
from joblib import Parallel, delayed
from statsmodels.stats.multitest import multipletests
from leesl.gr import generate_matrix

def permute_and_compute_L(Z, VTV, denominator):
    """
    Permute Z and compute L for a single permutation.
    """
    Z_permuted = np.random.permutation(Z)
    numerator_permuted = Z_permuted.T @ VTV @ Z_permuted
    return numerator_permuted / denominator

def run_lees_l(adata, n_permutations=10, n_jobs=-1):
    """
    Run Lee's L statistic calculation with parallelized permutations.

    Parameters:
    -----------
    adata : AnnData
        Annotated data matrix.
    n_permutations : int, optional
        Number of permutations for the test. Default is 10.
    n_jobs : int, optional
        Number of jobs to run in parallel. Default is -1 (use all available cores).

    This function updates adata in-place.
    """
    n = adata.n_obs
    W = adata.obsp["spatial_connectivities"]
    
    X = adata.uns['lee_X']
    Y = adata.uns['lee_Y']
    
    # Standardize X and Y
    X_z = StandardScaler().fit_transform(X.toarray())
    Y_z = StandardScaler().fit_transform(Y.toarray())

    # Combine X_z and Y_z into a single matrix Z
    Z = np.hstack((X_z, Y_z))

    # Compute V^T * V
    VTV = W.T @ W
    
    # Compute L according to equation 18
    numerator = Z.T @ VTV @ Z
    ones = np.ones(VTV.shape[0])
    denominator = ones.T @ VTV @ ones
    L_orig = numerator / denominator

    batch_size = min(100, n_permutations // 10)  # Process in batches of 100 or 10% of total, whichever is larger
    L_permuted = []

    with tqdm(total=n_permutations, desc="Permutations") as pbar:
        for i in range(0, n_permutations, batch_size):
            batch_permutations = range(min(batch_size, n_permutations - i))
            batch_results = Parallel(n_jobs=n_jobs)(
                delayed(permute_and_compute_L)(Z, VTV, denominator)
                for _ in batch_permutations
            )
            L_permuted.extend(batch_results)
            pbar.update(len(batch_results))

    L_permuted = np.array(L_permuted)

    # Compute final p-values
    p_values = np.mean(L_permuted >= L_orig, axis=0)

    # Store results in adata
    adata.uns['lee_L'] = L_orig
    adata.uns['lee_p_values'] = p_values

def spatial_corr(adata, n_permutations=10, n_jobs=1, two_rounds=False, engine="leesl"):
    """
    Perform spatial correlation analysis using Lee's L statistic.

    Parameters:
    -----------
    adata : AnnData
        Annotated data matrix.
    gene_list1 : list
        List of genes for the first set.
    gene_list2 : list, optional
        List of genes for the second set. If None, uses gene_list1.
    n_permutations : int, optional
        Number of permutations for the test. Default is 10.
    n_jobs : int, optional
        Number of jobs to run in parallel. Default is -1 (use all available cores).
    two_rounds : bool, optional
        Whether to run the test in two rounds. Default is False.
    engine : str, optional
        Which engine to use for the test. Default is "leesl". Other option is "pysal".
        Pysal is very slow, and therefore two_rounds if forced to be False. In addition,
        a warning will be printed if pysal is used for more than 10 gene pairs.

    This function updates adata in-place.
    """
    

    

    gene_list1 = adata.uns['lee_gene_list1']
    gene_list2 = adata.uns['lee_gene_list2']
    
    was_there_gene_list2 = adata.uns['lee_was_there_gene_list2']

    

    if was_there_gene_list2:
        print("Running Lee's L for", len(gene_list1), "gene pairs")

    if two_rounds and engine == "pysal":
        print("Pysal is very slow, and therefore two_rounds if forced to be False.")
        two_rounds = False

    if engine == "pysal" and len(gene_list1) > 10:
        print("""Pysal is very slow, and will take ages for more than 10 gene pairs,
              therefore gene pairs are truncated to 10.""")
        gene_list1 = gene_list1[:10]
        gene_list2 = gene_list2[:10]
        generate_matrix(adata, gene_list1, gene_list2)


    n_combinations = len(gene_list1) ** 2 if not was_there_gene_list2 else len(gene_list1)
    print("Running Lee's L for", n_combinations, "gene pairs")

    
    if two_rounds:
        n_permutations = 1000
        

        run_lees_l(adata, n_permutations, n_jobs)
    
        L = adata.uns['lee_L']
        p_values = adata.uns['lee_p_values']

        #save L and P to adata
        adata.uns["leeL_check"] = L
        adata.uns["leeP_check"] = p_values
        
        results = []
        if not isinstance(gene_list1, list):
            gene_list1 = gene_list1.tolist()
        if not isinstance(gene_list2, list):
            gene_list2 = gene_list2.tolist()

        all_genes = gene_list1 + gene_list2
        
        print("all_genes",all_genes)
        for i, gene_A in enumerate(all_genes):
            for j, gene_B in enumerate(all_genes):
                if i <= j:  # This ensures we only get the upper triangle including diagonal
                    results.append({
                        "gene_A": gene_A,
                        "gene_B": gene_B,
                        "L": L[i, j],
                        "P": p_values[i, j]
                    })
        
        df = pd.DataFrame(results)
        
        if was_there_gene_list2:
            print("There was a gene_list2")
            pairs = list(zip(gene_list1, gene_list2))
            pairs_set = set(pairs)
            #only keep rows where pairs occur
            df = df[df.apply(lambda x: (x["gene_A"],x["gene_B"]) in pairs_set, axis=1)]
            #remove dups
            df = df.drop_duplicates(subset=["gene_A","gene_B"])
            

        df = df.sort_values(by=['P','L'], ascending=[True,False])
        
        #reset index
        df = df.reset_index(drop=True)
        
        # Print number of significant genes
        print("Number of nominally significant gene pairs:", sum(df['P'] < 0.05))
        
        nominal_df = df.copy()
        adata.uns["nominal_leeL"] = nominal_df


        df = df[df["P"] < 0.05]
        nominal_df = nominal_df[nominal_df["P"] > 0.05]

        gene_set_a = df["gene_A"]
        gene_set_b = df["gene_B"]

        generate_matrix(adata, gene_set_a, gene_set_b)
        
        n_combinations = len(gene_set_a) ** 2 if not was_there_gene_list2 else len(gene_set_a)
        n_permutations = n_combinations/0.05
        
        #round
        n_permutations = round(n_permutations)
        print("Running Lee's L for", n_combinations, "gene pairs")
        print("and with", n_permutations, "permutations")
        
        run_lees_l(adata, n_permutations, n_jobs)

        L = adata.uns['lee_L']
        p_values = adata.uns['lee_p_values']
        
        all_genes = gene_set_a.tolist() + gene_set_b.tolist()
        results = []
        for i, gene_A in enumerate(all_genes):
            for j, gene_B in enumerate(all_genes):
                if i <= j:  # This ensures we only get the upper triangle including diagonal
                    results.append({
                        "gene_A": gene_A,
                        "gene_B": gene_B,
                        "L": L[i, j],
                        "P": p_values[i, j]
                    })
        
        df = pd.DataFrame(results)
        
        #sort by p-value
        df = df.sort_values(by=['P','L'], ascending=[True,False])
        
        #reset index
        df = df.reset_index(drop=True)
        
        #merge with nominal
        df = pd.concat([df,nominal_df],axis=0)

        if was_there_gene_list2:
            pairs = list(zip(gene_list1, gene_list2))
            pairs_set = set(pairs)

            #only keep rows where pairs occur
            df = df[df.apply(lambda x: (x["gene_A"],x["gene_B"]) in pairs_set, axis=1)]

            print(f"Only keeping this many rows: {len(df)}")
        
        
        #remove dups
        df["genes_concat_in_abc"] = df.apply(lambda x: "".join(sorted([x["gene_A"],x["gene_B"]])),axis=1)
        df = df.drop_duplicates(subset="genes_concat_in_abc")
        df = df.drop(columns="genes_concat_in_abc")

        df['P_adj'] = multipletests(df['P'], method='fdr_bh')[1]
        
        # Print number of significant genes
        print("Number of significant gene pairs:", sum(df['P_adj'] < 0.05))
        
        # Store the results in adata.uns
        adata.uns["leeL"] = df


    else:
        if engine == "leesl":

            run_lees_l(adata, n_permutations, n_jobs)
            
            L = adata.uns['lee_L']
            p_values = adata.uns['lee_p_values']
            
            results = []
            #check if they are lists, if not convert to list
            if not isinstance(gene_list1, list):
                gene_list1 = gene_list1.tolist()
            if not isinstance(gene_list2, list):
                gene_list2 = gene_list2.tolist()

            all_genes = gene_list1 + gene_list2
            for i, gene_A in enumerate(all_genes):
                for j, gene_B in enumerate(all_genes):
                    if i <= j:  # This ensures we only get the upper triangle including diagonal
                        results.append({
                            "gene_A": gene_A,
                            "gene_B": gene_B,
                            "L": L[i, j],
                            "P": p_values[i, j]
                        })
            
            df = pd.DataFrame(results)

            if was_there_gene_list2:

                pairs = list(zip(gene_list1, gene_list2))
                pairs_set = set(pairs)
                #only keep rows where pairs occur
                df = df[df.apply(lambda x: (x["gene_A"],x["gene_B"]) in pairs_set, axis=1)]
            
            # calc padj
            
            #remove dups
            df["genes_concat_in_abc"] = df.apply(lambda x: "".join(sorted([x["gene_A"],x["gene_B"]])),axis=1)
            df = df.drop_duplicates(subset="genes_concat_in_abc")
            df = df.drop(columns="genes_concat_in_abc")
            df['P_adj'] = multipletests(df['P'], method='fdr_bh')[1]
            
            #sort by p-value
            df = df.sort_values(by=['P','L'], ascending=[True,False])
            
            #reset index
            df = df.reset_index(drop=True)
            
            # Print number of significant genes
            print("Number of significant gene pairs:", sum(df['P_adj'] < 0.05))
            
            # Store the results in adata.uns
            adata.uns["leeL"] = df
        elif engine == "pysal":
            # PySAL implementation
            W = adata.obsp["spatial_connectivities"]
            X = adata.uns['lee_X']
            Y = adata.uns['lee_Y']

            # Initialize Spatial_Pearson
            sp = Spatial_Pearson(connectivity=W, permutations=n_permutations)

            results = []
            for i, (gene_A, gene_B) in enumerate(zip(gene_list1, gene_list2)):
                x = X[:, i].toarray().flatten().reshape(-1, 1)  # Reshape to 2D array
                y = Y[:, i].toarray().flatten().reshape(-1, 1)  # Reshape to 2D array

                # Fit the Spatial_Pearson model
                sp.fit(x, y)

                # Extract results
                L = sp.association_[0, 1]  # The spatial correlation coefficient
                P = sp.significance_[0, 1]  # The p-value

                results.append({
                    "gene_A": gene_A,
                    "gene_B": gene_B,
                    "L": L,
                    "P": P
                })

            df = pd.DataFrame(results)

            # Calculate adjusted p-values
            df['P_adj'] = multipletests(df['P'], method='fdr_bh')[1]

            # Sort by p-value and L
            df = df.sort_values(by=['P', 'L'], ascending=[True, False])

            # Reset index
            df = df.reset_index(drop=True)

            # Print number of significant genes
            print("Number of significant gene pairs:", sum(df['P_adj'] < 0.05))

            # Store the results in adata.uns
            adata.uns["leeL"] = df
            
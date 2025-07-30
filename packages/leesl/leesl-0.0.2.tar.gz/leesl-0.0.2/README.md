# leesl

A Python package for computing Lee's L spatial correlation statistic with rapid matrix multiplications and parallelized permutation testing.

## Installation

```bash
pip install leesl
```

## Overview

leesl implements Lee's L statistic for measuring spatial correlation between gene expression patterns in spatial transcriptomics data. The package supports both single-gene and gene-pair analysis with efficient parallel permutation testing.

## Key Features

- Parallelized permutation testing for fast computation
- Two-round adaptive testing for multiple comparisons
- Support for both leesl and pysal engines
- Automatic FDR correction
- Integration with AnnData objects

## Usage

### Basic spatial correlation analysis

```python
import scanpy as sc
import leesl

# Load your spatial data
adata = sc.read_h5ad("spatial_data.h5ad")

# Generate matrices for genes of interest
from leesl.gr import generate_matrix
gene_list = ["GENE1", "GENE2", "GENE3"]
generate_matrix(adata, gene_list)

# Run Lee's L analysis
from leesl.pp import spatial_corr
spatial_corr(adata, n_permutations=1000, n_jobs=-1)

# Results stored in adata.uns["leeL"]
results = adata.uns["leeL"]
print(f"Significant pairs: {sum(results['P_adj'] < 0.05)}")
```

### Gene pair analysis

```python
# Compare specific gene pairs
gene_list1 = ["GENE1", "GENE2"]
gene_list2 = ["GENE3", "GENE4"]
generate_matrix(adata, gene_list1, gene_list2)

spatial_corr(adata, n_permutations=1000)
```

### Two-round adaptive testing

```python
# Use two-round testing for better power with multiple comparisons
spatial_corr(adata, n_permutations=1000, two_rounds=True)
```

## Requirements

- numpy
- pandas
- scipy
- scikit-learn
- statsmodels
- tqdm
- joblib
- esda (optional, for pysal engine)

## Output

Results are stored in `adata.uns["leeL"]` as a DataFrame with columns:
- `gene_A`, `gene_B`: Gene pair
- `L`: Lee's L statistic
- `P`: Raw p-value
- `P_adj`: FDR-adjusted p-value

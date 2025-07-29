# anticor_features

Anti-correlation based feature selection for single cell (and other) omics datasets.

## Features

- Unsupervised feature selection based on gene-gene anti-correlations.
- Automatically filters out genes in mitochondrial, ribosomal, and other pathways (customizable).
- Scales to large datasets using HDF5-backed intermediate files.
- Integrated Python API and command-line interface.
- Passes null-dataset tests for robust selection.

## Installation

Requires Python 3.6 or higher.

Install from PyPI:

```bash
pip install anticor_features
```

Or install from source:

```bash
git clone https://bitbucket.org/scottyler892/anticor_features.git
cd anticor_features
pip install .
```

## Dependencies

- h5py
- numpy
- pandas
- scipy
- seaborn
- matplotlib
- numba
- ray
- gprofiler-official (>=0.3.5)
- psutil

## Quickstart Python API

```python
from anticor_features.anticor_features import get_anti_cor_genes

# exprs: array-like or HDF5 dataset with genes in rows and cells in columns
# feature_ids: list of gene IDs matching rows of exprs
# species: g:Profiler species code (e.g., "hsapiens" or "mmusculus")
anti_cor_table = get_anti_cor_genes(exprs, feature_ids, species="hsapiens")

# Filter selected genes
selected = anti_cor_table.loc[anti_cor_table["selected"], "gene"].tolist()
print(selected)
```

See the g:Profiler organism list for valid species codes:
https://biit.cs.ut.ee/gprofiler/page/organism-list

## Customization

- `pre_remove_features`: list of gene IDs to exclude before analysis.
- `pre_remove_pathways`: list of GO term codes whose genes will be removed.
- `min_express_n`: minimum number of cells a gene must be expressed in to be considered (set to -1 to disable filtering, e.g., for non-expression or non-single-cell data).
- `scratch_dir`: directory for temporary HDF5 files (default: system temp directory).
- `bin_size`: number of features per batch when computing correlation matrix.
- `FPR` and `FDR`: false positive rate and false discovery rate for negative correlations.
- `num_pos_cor`: minimum number of positive correlations to select a feature.

## Using with Non-Expression or Other Omics Data

For datasets that are not single-cell or gene-expression matrices (e.g., bulk omics, proteomics, metabolomics, or other feature embeddings), you can skip the minimum-expression filter and run only the anti-correlation statistics by setting `min_express_n=-1`. For example:

```python
anti_cor_df = get_anti_cor_genes(
    embed_df,
    feature_ids=embed_df.index.tolist(),
    pre_remove_features=[],
    pre_remove_pathways=[],
    min_express_n=-1
)
```

Setting `min_express_n=-1` disables the minimum-expression requirement (only meaningful for count-based single-cell data), allowing all features to be included in the statistical analysis.

## Scanpy Integration

When using Scanpy (`AnnData`), transpose the data matrix:

```python
from anticor_features.anticor_features import get_anti_cor_genes

anti_cor_table = get_anti_cor_genes(
    adata.X.T,
    adata.var.index.tolist(),
    species="hsapiens"
)

import pandas as pd
adata.var = pd.concat([adata.var, anti_cor_table], axis=1)
selected = anti_cor_table.loc[anti_cor_table["selected"], "gene"].tolist()
adata.raw = adata
adata = adata[:, selected]
```

## Command-Line Interface

```bash
python3 -m anticor_features.anticor_features \
  -i exprs.tsv \
  -species mmusculus \
  -out_file anti_cor_features.tsv \
  -scratch_dir /path/to/tmp \
  -use_default_pathway_removal
```

Options:

- `-i`, `--infile`: input expression matrix (TSV or HDF5).
- `-species`: g:Profiler species code (default: "hsapiens").
- `-out_file`: output file path for the results table.
- `-hdf5`: treat input as HDF5 with dataset key "infile".
- `-ids`: file with feature (gene) IDs (no header) for HDF5 input.
- `-cols`: file with sample (cell) IDs (with header) for HDF5 input.
- `-scratch_dir`: directory for temporary files.
- `-use_default_pathway_removal`: remove default mitochondrial, ribosomal, and related pathways.
- `-h, --help`: display full help message.

## Performance

Computing time scales with number of features and batch size. Selecting anti-correlated features on ~10k genes and ~3k cells typically takes 1–2 minutes (network time for g:Profiler). Larger datasets may take longer.

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

## Contact

Scott Tyler <scottyler89+bitbucket@gmail.com>
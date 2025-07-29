# calmcarz

>A Python package for batch correction (CALM) and activity scoring (CARZ, TAS) of perturbed expression data

`calmcarz` is a lightweight and easy-to-use Python package for normalizing high-throughput gene expression data from perturbation screens. It provides a simple, function-based workflow to remove technical batch effects and calculate robust, interpretable scores for transcriptional activity.

The pipeline consists of three main steps:
- **CALM (Control-Anchored Linear Model)**: Removes batch effects by fitting a linear model on control samples.
- **CARZ (Control-Anchored Robust Z-score)**: Standardizes gene expression relative to the control distribution using robust statistics.
- **TAS (Transcriptional Activity Score)**: Summarizes the overall degree of perturbation for each cell based on the number of significantly altered genes.

## Installation
You can install `calmcarz` directly from PyPI using pip:

```
pip install calmcarz
```
Ensure you have the necessary dependencies (or it will be installed automatically: numpy, pandas, anndata, statsmodels, scipy, and tqdm)

## Usage
The library is designed to work seamlessly with AnnData objects.

```
import anndata as ad
from calmcarz import calm_correction, calculate_carz, calculate_tas

# 1. Load your data into an AnnData object
# This assumes your data is in a log-transformed layer (e.g., 'log1p_counts')
# and adata.obs contains 'batch' and 'treatment' columns.
adata = ad.read_h5ad("path/to/your/data.h5ad")

# 2. Apply CALM for batch correction
# The corrected data will be stored in a new layer, 'calm_corrected'.
calm_correction(
    adata,
    plate_column='rna_plate',
    treatment_column='cmap_name',
    control_treatment_value='DMSO',
    corrected_layer_name='X_CALM' # the CALM-corrected expression will be store in layer 'X_CALM'
)

# 3. Calculate CARZ scores
# CARZ scores will be stored in a new layer, 'carz_scores'.
calculate_carz(
    adata,
    plate_key="rna_plate",
    layer="X_CALM", # calculate using CALM-corrected expression
    pert_type_key="pert_type",
    control_categories=["ctl_vehicle"], # calculate using plate controls
    key_added="X_CARZ", # the CARZ matrix will be stored in layer 'X_CARZ'
    copy=False,
)

# 4. Calculate Transcriptional Activity Score (TAS)
# The final TAS will be added to adata.obs.
calculate_tas(
    adata,
    layer='X_CARZ',
    tas_obs_key='TAS_score',
    alpha=2.5 # Set the significance threshold for CARZ scores
)

# View the results
print(adata.obs[['cmap_name', 'TAS_score']].head())
```

## API Overview
`calm_correction(adata, ...)`

Corrects for batch effects using a control-anchored linear model.

- `adata`: AnnData object. Assumes expression data in adata.X (cells x genes). adata.obs must contain the `plate_column` and `treatment_column`.
- `plate_column`: Name of the column in adata.obs that identifies the plate.
- `treatment_column`: Name of the column in adata.obs that identifies the treatment.
- `control_treatment_value`: Value in `treatment_column` that identifies control samples.
- `corrected_layer_name`: Name of the layer in adata to store the corrected expression data. Original adata.X is not modified.
- `min_control_samples_per_gene_for_fitting`: Minimum number of total control samples (across all plates) required for a gene to attempt model fitting.
- `min_control_variance_for_fitting`: Minimum variance of expression in control samples for a gene to attempt model fitting.
- `verbose`: If True, prints progress information.

`calculate_carz(adata, ...)`

Calculates robust Z-scores relative to the control distribution.

- `adata`: Annotated data matrix (cells x genes).
- `plate_key`: Key in `adata.obs` for plate identifiers.
- `pert_type_key`: Key in `adata.obs` indicating perturbation type.
- `control_categories`: List of strings in `adata.obs[pert_type_key]` that identify control samples.
- `layer`: Layer in `adata.layers` to use as input. If None, `adata.X`.
- `key_added`: Name of the layer to store results. If None, overwrites input.
- `copy`: Whether to modify adata inplace (False) or return a copy (True).

`calculate_tas(adata, ...)`

Calculates transcriptional activity score (TAS).

- `adata`: AnnData object with Z-scored expression data in `adata.X`. `adata.X` should have cells as rows and genes as columns.
- `layer`: Layer in `adata.layers` to use as input. If None, `adata.X`.
- `alpha`: The threshold for the absolute Z-score.
- `tas_obs_key`: The key under which the TAS will be stored in `adata.obs`. Defaults to "TAS_score".
- `gene_subset`: Optional list of gene names (strings). If provided, TAS will be calculated only for these genes. If None, all genes in `adata.X` will be used. Defaults to None.

## Contributing
Contributions are welcome! If you have suggestions for improvements or find a bug, please feel free to open an issue or submit a pull request on the GitHub repository.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

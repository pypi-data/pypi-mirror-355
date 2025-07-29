# src/calmcarz/carz.py
import numpy as np
import anndata as ad
from scipy.stats import median_abs_deviation
from typing import Optional, List

# Scaling constant for MAD
MAD_CONSTANT = 1.4826

def calculate_mad(series):
    """Calculates the Median Absolute Deviation from the Median for a pandas Series."""
    # Filter out NaNs if any, although median handles them often
    valid_series = series.dropna()

    if valid_series.empty:
        return np.nan # Or 0, depending on desired handling of all-NaN input
    series_median = np.median(valid_series)

    # calculate median deviance
    mad = np.median(np.abs(valid_series - series_median))

    return mad

def calculate_carz(
    adata: ad.AnnData,
    plate_key: str,
    pert_type_key: str,
    control_categories: list[str],
    layer: str | None = None,
    key_added: str | None = None,
    epsilon: float = 1e-2,
    copy: bool = False,
) -> ad.AnnData | None:
    """
    Robustly z-scores data within plates using control median and MAD.

    Calculates median and Median Absolute Deviation (MAD) for each gene using
    only control samples within each plate. Then applies robust z-score
    transformation (x - median) / (MAD * 1.4826) to *all* samples within
    that plate.

    Args:
        adata: Annotated data matrix (cells x genes).
        plate_key: Key in `adata.obs` for plate identifiers.
        pert_type_key: Key in `adata.obs` indicating perturbation type.
        control_categories: List of strings in `adata.obs[pert_type_key]`
                            that identify control samples.
        layer: Layer in `adata.layers` to use as input. If None, `adata.X`.
        key_added: Name of the layer to store results. If None, overwrites
                   input. Recommended: 'X_rzscore_control'.
        copy: Whether to modify adata inplace (False) or return a copy (True).

    Returns:
        Modified AnnData object or None.

    Raises:
        ValueError: If keys are not found, control_categories is empty,
                    no control samples are found, or some plates lack controls.
        TypeError: If data is unsuitable type.
        MemoryError: If dense conversion fails.

    Notes:
        - Uses Median Absolute Deviation (MAD) for robust scaling.
        - The scaling factor 1.4826 makes MAD comparable to standard deviation
          for normally distributed data.
        - If MAD is 0 for a gene/plate (e.g., >50% controls have the median value),
          the denominator is set to 1, resulting in robust z-scores of 0 for
          cells with the median value.
        - Calculation of MAD using groupby().apply() may be slower than std()
          for very large datasets.
    """
    if copy:
        adata = adata.copy()

    # --- Input Validation ---
    if plate_key not in adata.obs:
        raise ValueError(f"Plate key '{plate_key}' not found in adata.obs.")
    if pert_type_key not in adata.obs:
        raise ValueError(f"Perturbation type key '{pert_type_key}' not found in adata.obs.")
    if not control_categories or not isinstance(control_categories, (list, tuple)):
        raise ValueError("`control_categories` must be a non-empty list or tuple of strings.")

    # --- 1. Select Data ---
    if layer is None:
        X = adata.X
        data_name = "adata.X"
        target_layer = None
    elif layer in adata.layers:
        X = adata.layers[layer]
        data_name = f"adata.layers['{layer}']"
        target_layer = layer
    else:
        raise ValueError(f"Layer '{layer}' not found in adata.layers.")

    # --- 2. Prepare Data (Dense, Float) ---
    if issparse(X):
        warnings.warn(
            f"Input data {data_name} is sparse. Converting to dense numpy array. "
            "This may consume significant memory.",
            UserWarning, stacklevel=2
        )
        try:
            X_dense = X.toarray().astype(np.float64)
        except MemoryError as e:
            raise MemoryError(f"Could not convert {data_name} to dense.") from e
        except Exception as e:
             raise TypeError(f"Could not convert {data_name} to dense array: {e}") from e
    elif isinstance(X, np.ndarray):
        X_dense = X.astype(np.float64, copy=False)
    else:
        raise TypeError(f"Input data {data_name} has unhandled type: {type(X)}.")

    # --- 3. Create DataFrame & Identify Controls ---
    print("Preparing data and identifying controls...")
    df = pd.DataFrame(X_dense, index=adata.obs_names, columns=adata.var_names)
    # Ensure plate and pert type are categorical for efficient grouping
    df['_plate'] = adata.obs[plate_key].astype('category')
    df['_pert_type'] = adata.obs[pert_type_key].astype('category')

    control_mask = df['_pert_type'].isin(control_categories)
    if not control_mask.any():
        raise ValueError(f"No cells found matching control categories {control_categories} "
                         f"in adata.obs['{pert_type_key}'].")

    df_control = df[control_mask]

    # --- 4. Calculate Control Statistics (Median & MAD) per Plate ---
    print("Calculating median and MAD from control samples within each plate...")
    gene_cols = adata.var_names.tolist()
    try:
        # Calculate median per gene per plate
        control_medians = df_control.groupby('_plate', observed=True)[gene_cols].median()

        # --- Explicitly calculate MAD column-wise for each plate group ---
        control_mads_list = []
        # Group controls by plate
        grouped_controls = df_control.groupby('_plate', observed=True)

        # Iterate through each plate's control group
        print("Calculating MAD explicitly per plate...")
        for plate_id, group_df in tqdm(grouped_controls, desc="Calculating MAD per plate", total=grouped_controls.ngroups):
            # Apply the MAD function column-wise (axis=0) to the gene columns of this group
            plate_mads = group_df[gene_cols].apply(calculate_mad, axis=0)

            # Assign the plate ID as the name of the resulting Series
            plate_mads.name = plate_id
            control_mads_list.append(plate_mads)

        # Check if any MADs were calculated
        if not control_mads_list:
             raise ValueError("No control groups found to calculate MAD.")

    except Exception as e:
        raise RuntimeError(f"Error calculating control statistics per plate: {e}") from e

    # --- 5. Check for Missing Plates & Handle NaN/Zero MADs ---
    all_plates = df['_plate'].cat.categories
    missing_plates = all_plates.difference(control_medians.index) # Check based on median index
    if not missing_plates.empty:
        raise ValueError(f"Plates found with no control samples matching categories "
                         f"{control_categories}: {missing_plates.tolist()}. "
                         "Cannot calculate control statistics for these plates.")
    # Combine the list of Series into a DataFrame
    control_mads = pd.DataFrame(control_mads_list)

    # print(f"Number of NaN MADs before fillna: {control_mads.isna().sum().sum()}")
    # control_mads_filled = control_mads.fillna(0) # Keep original separate if needed
    # print(f"Number of Zero MADs after fillna: {(np.abs(control_mads_filled) < 1e-12).sum().sum()}")
    # print(f"Percentage of Zero MADs: {100 * (np.abs(control_mads_filled) < 1e-12).sum().sum() / control_mads_filled.size:.2f}%")

    # Handle cases where MAD is NaN (e.g., all NaNs in input) or 0.
    # Fill NaN with 0 first, then handle 0 MAD in the denominator calculation later.
    control_mads = control_mads.fillna(0)

    # --- 6. Map Control Statistics to All Cells ---
    print("Mapping control statistics to all cells...")
    cell_plate_ids = df['_plate']
    try:
        # Use reindex based on the cell's plate ID; ensures correct order
        mapped_medians = control_medians.reindex(cell_plate_ids).values
        mapped_mads = control_mads.reindex(cell_plate_ids).values

    except Exception as e:
        raise RuntimeError(f"Error mapping control statistics back to cells: {e}. ")

    # --- 7. Apply Robust Z-Score Transformation ---
    print("Applying robust z-score transformation...")
    # Denominator = MAD * constant
    # Important: Handle MAD = 0 case to avoid division by zero
    expression_values = df[gene_cols].values
    # Calculate raw deviations
    deviations = expression_values - mapped_medians
    # Calculate denominator, keep track of where MAD is zero
    denominator = mapped_mads * MAD_CONSTANT
    is_mad_zero = np.abs(denominator) < epsilon # Or np.abs(mapped_mads) < epsilon

    # Initialize transformed matrix (maybe with NaNs or zeros)
    transformed_matrix = np.zeros_like(deviations, dtype=np.float64) # Or np.full_like..., np.nan

    # Calculate z-score only where MAD is NOT zero
    valid_mask = ~is_mad_zero
    transformed_matrix[valid_mask] = deviations[valid_mask] / denominator[valid_mask]


    # --- 8. Store Result ---
    if key_added is None:
        if target_layer is None:
            print(f"Overwriting adata.X with robust z-scores based on control stats.")
            adata.X = transformed_matrix
        else:
            print(f"Overwriting adata.layers['{target_layer}'] with robust z-scores.")
            adata.layers[target_layer] = transformed_matrix
    else:
        print(f"Storing robust z-scores based on control stats in adata.layers['{key_added}'].")
        if key_added in adata.layers:
             warnings.warn(f"Layer `adata.layers['{key_added}']` already exists and will be overwritten.",
                           UserWarning, stacklevel=2)
        adata.layers[key_added] = transformed_matrix

    print("Robust z-score transformation using control statistics complete.")
    return adata if copy else None

def calculate_tas(
    adata: ad.AnnData,
    alpha: float,
    tas_obs_key: str = "TAS_score",
    layer: str | None = None,
    gene_subset: Optional[List[str]] = None
) -> None:
    """
    This is a modified version of calculate_tas().
    Calculates the Transcriptional Activity Score (TAS) for each cell and
    stores it in adata.obs.

    The TAS is defined as the percentage of genes (either all genes or a
    specified subset) with an absolute Z-score value equal to or higher than alpha.

    Args:
        adata: AnnData object with Z-scored expression data in adata.X.
               adata.X should have cells as rows and genes as columns.
        layer: Layer in adata.layers to use as input. If None, adata.X.
        alpha: The threshold for the absolute Z-score.
        tas_obs_key: The key under which the TAS will be stored in adata.obs.
                     Defaults to "TAS_score".
        gene_subset: Optional list of gene names (strings). If provided,
                     TAS will be calculated only for these genes. If None,
                     all genes in adata.X will be used. Defaults to None.

    Returns:
        None. Modifies adata.obs in place.
    """
    if not isinstance(adata, ad.AnnData):
        raise TypeError("Input 'adata' must be an AnnData object.")
    if not isinstance(alpha, (int, float)):
        raise TypeError("Input 'alpha' must be a numeric value.")
    if alpha < 0:
        raise ValueError("Input 'alpha' must be non-negative.")

    # Select Data
    if layer is None:
        X = adata.X
        data_name = "adata.X"
        target_layer = None
    elif layer in adata.layers:
        X = adata.layers[layer]
        data_name = f"adata.layers['{layer}']"
        target_layer = layer
    else:
        raise ValueError(f"Layer '{layer}' not found in adata.layers.")

    z_scores_to_process = X
    n_genes_in_scope = adata.n_vars

    if gene_subset is not None:
        if not isinstance(gene_subset, list) or not all(isinstance(g, str) for g in gene_subset):
            raise TypeError("'gene_subset' must be a list of strings (gene names).")

        if not gene_subset: # Empty list provided
             print(f"Warning: An empty 'gene_subset' was provided. "
                  f"TAS scores in '{tas_obs_key}' will be 0, as no genes are selected.")
             adata.obs[tas_obs_key] = np.zeros(adata.n_obs)
             return

        # Identify which genes from the subset are present in adata.var_names
        # gene_mask_in_adata is a boolean array aligned with adata.var_names
        gene_mask_in_adata = adata.var_names.isin(gene_subset)

        # Get the actual integer indices of these genes in adata
        gene_indices_for_slicing = np.where(gene_mask_in_adata)[0]

        if len(gene_indices_for_slicing) == 0:
            print(f"Warning: None of the genes provided in 'gene_subset' were found in adata.var_names. "
                  f"TAS scores in '{tas_obs_key}' will be 0.")
            adata.obs[tas_obs_key] = np.zeros(adata.n_obs)
            return

        # Slice adata.X to get Z-scores for the selected genes
        z_scores_to_process = adata.X[:, gene_indices_for_slicing]
        n_genes_in_scope = len(gene_indices_for_slicing) # This is the number of genes used for calculation

        # For clarity, count how many of user's requested genes were found vs. requested
        requested_gene_count = len(set(gene_subset)) # Use set to count unique requested genes
        found_gene_count = n_genes_in_scope
        print(f"Calculating TAS using {found_gene_count} genes out of {requested_gene_count} unique genes "
              f"requested in 'gene_subset' (genes not found in AnnData object are ignored).")
    else:
        print(f"Calculating TAS using all {n_genes_in_scope} genes in the AnnData object.")

    # This check covers cases where adata initially had 0 vars, or gene_subset resulted in 0 usable genes.
    if n_genes_in_scope == 0:
        print(f"Warning: Number of genes for TAS calculation ('n_genes_in_scope') is 0. "
              f"TAS scores in '{tas_obs_key}' will be 0.")
        adata.obs[tas_obs_key] = np.zeros(adata.n_obs)
        return

    # Calculate absolute Z-scores for the selected genes
    abs_z_scores = np.abs(z_scores_to_process)

    # Identify genes with absolute Z-score >= alpha
    active_genes_mask = abs_z_scores >= alpha

    # Count the number of such genes per cell
    if issparse(active_genes_mask): # Check if it's a sparse matrix
        count_active_genes_per_cell = np.asarray(active_genes_mask.sum(axis=1)).flatten()
    else: # It's a dense numpy array
        count_active_genes_per_cell = active_genes_mask.sum(axis=1)

    # Calculate the percentage based on the number of genes in scope
    tas_scores = (count_active_genes_per_cell / n_genes_in_scope)

    # Store the TAS in adata.obs
    adata.obs[tas_obs_key] = tas_scores
    print(f"TAS scores calculated and stored in adata.obs['{tas_obs_key}']")

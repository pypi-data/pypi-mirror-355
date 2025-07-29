# src/calmcarz/calm.py
import numpy as np
import pandas as pd
import anndata as ad
import statsmodels.formula.api as smf
from tqdm import tqdm

def calm_correction(
    adata: ad.AnnData,
    plate_column: str = 'rna_plate',
    treatment_column: str = 'cmap_name',
    control_treatment_value: str = 'DMSO',
    corrected_layer_name: str = 'X_corrected',
    min_control_samples_per_gene_for_fitting: int = 5, # Minimum number of total control samples for a gene to attempt fitting
    min_control_variance_for_fitting: float = 1e-6, # Minimum variance in control samples for a gene
    verbose: bool = True
) -> ad.AnnData:
    """
    Regresses out plate effects estimated from control samples using gene-wise linear models.

    The method trains a linear model for each gene using only control samples,
    where `expression ~ C(plate)`. It then calculates the difference between the
    predicted mean expression on each plate (from the model fitted on controls)
    and the overall mean expression of that gene across all control samples.
    This difference (the "plate bias") is then subtracted from all samples
    (both control and treated) belonging to that specific plate.

    Args:
        adata: AnnData object. Assumes expression data in adata.X (cells x genes).
               adata.obs must contain the `plate_column` and `treatment_column`.
        plate_column: Name of the column in adata.obs that identifies the plate.
        treatment_column: Name of the column in adata.obs that identifies the treatment.
        control_treatment_value: Value in `treatment_column` that identifies control samples.
        corrected_layer_name: Name of the layer in adata to store the corrected expression data.
                              Original adata.X is not modified.
        min_control_samples_per_gene_for_fitting: Minimum number of total control samples
                                                  (across all plates) required for a gene
                                                  to attempt model fitting.
        min_control_variance_for_fitting: Minimum variance of expression in control samples
                                          for a gene to attempt model fitting.
        verbose: If True, prints progress information.

    Returns:
        AnnData object with the corrected expression data stored in adata.layers[corrected_layer_name].
    """

    if plate_column not in adata.obs.columns:
        raise ValueError(f"Plate column '{plate_column}' not found in adata.obs.")
    if treatment_column not in adata.obs.columns:
        raise ValueError(f"Treatment column '{treatment_column}' not found in adata.obs.")
    if not any(adata.obs[treatment_column] == control_treatment_value):
        raise ValueError(f"No control samples found with treatment '{control_treatment_value}' in column '{treatment_column}'.")

    # Ensure plate column is categorical for statsmodels and consistent use
    adata.obs[plate_column] = adata.obs[plate_column].astype('category')

    # Identify control samples
    control_mask = adata.obs[treatment_column] == control_treatment_value
    adata_controls = adata[control_mask, :]

    if adata_controls.n_obs == 0:
        raise ValueError(f"No control samples selected. Check `treatment_column` and `control_treatment_value`.")

    # Prepare corrected expression matrix
    # It's often safer to work with a dense matrix for corrections if memory allows,
    # as subtractions can make sparse matrices dense anyway if biases are varied.
    if isinstance(adata.X, np.ndarray):
        corrected_X = adata.X.copy()
    else: # Handles scipy.sparse matrices
        corrected_X = adata.X.toarray().copy()

    num_genes = adata.n_vars

    # This list will store dictionaries. Each dictionary maps a plate_id to its calculated bias for one gene.
    # Index of the list corresponds to the gene_idx.
    plate_biases_for_all_genes = [{} for _ in range(num_genes)]

    if verbose:
        print(f"Found {adata_controls.n_obs} control samples across {adata_controls.obs[plate_column].nunique()} unique plates in the control set.")
        print(f"Starting gene-wise linear model fitting to estimate plate biases...")

    # --- Training phase: Learn plate biases from control samples ---
    # Determine the number of unique plates present in the control data.
    # This is important for the minimum samples check for model fitting.
    n_unique_control_plates = adata_controls.obs[plate_column].nunique()

    # Adjust min_control_samples_per_gene_for_fitting if it's too low for the number of plate parameters
    # Number of parameters for C(plate) will be n_unique_control_plates (one for intercept, n-1 for plate dummies)
    # A more robust minimum would be n_unique_control_plates + 1, or an absolute minimum.
    actual_min_samples_needed = max(n_unique_control_plates + 1, min_control_samples_per_gene_for_fitting)


    gene_iterator = tqdm(range(num_genes), desc="Fitting models (genes)", disable=not verbose, unit="gene")

    for gene_idx in gene_iterator:
        gene_name = adata.var_names[gene_idx]

        gene_expr_controls = adata_controls.X[:, gene_idx]
        if not isinstance(gene_expr_controls, np.ndarray): # If X was sparse
            gene_expr_controls = gene_expr_controls.toarray().flatten()

        plate_ids_controls = adata_controls.obs[plate_column]

        df_gene_controls = pd.DataFrame({
            'expression': gene_expr_controls,
            plate_column: plate_ids_controls # This is already a pd.Series of categories
        })

        # Filter out any NaN/inf expression values if they exist, for model stability
        df_gene_controls = df_gene_controls.replace([np.inf, -np.inf], np.nan).dropna()

        if df_gene_controls['expression'].var() < min_control_variance_for_fitting or \
           df_gene_controls.shape[0] < actual_min_samples_needed:
            if verbose and num_genes < 200 and gene_idx < 200 : # Avoid excessive printing for many genes
                 print(f"Skipping gene {gene_name} (index {gene_idx}): Insufficient data (var: {df_gene_controls['expression'].var():.2e}, "
                       f"samples: {df_gene_controls.shape[0]}, need: {actual_min_samples_needed}) for model fitting.")
            plate_biases_for_all_genes[gene_idx] = {} # Ensure it's an empty dict, so no correction
            continue

        try:
            model = smf.ols(f'expression ~ C({plate_column})', data=df_gene_controls).fit()
            overall_control_mean_gene = df_gene_controls['expression'].mean()

            current_gene_plate_biases = {}
            # Predict effect only for plates that were actually present in the control data for this gene
            for plate_id in df_gene_controls[plate_column].unique():
                # Create a DataFrame with the correct categorical type for prediction
                predict_df = pd.DataFrame({plate_column: pd.Categorical([plate_id], categories=df_gene_controls[plate_column].cat.categories)})
                predicted_mean_on_plate = model.predict(predict_df)[0]
                bias = predicted_mean_on_plate - overall_control_mean_gene
                current_gene_plate_biases[plate_id] = bias

            plate_biases_for_all_genes[gene_idx] = current_gene_plate_biases

        except Exception as e:
            if verbose and num_genes < 200 and gene_idx < 200:
                print(f"Could not fit model for gene {gene_name} (index {gene_idx}): {e}")
            plate_biases_for_all_genes[gene_idx] = {} # No correction if model fails
            continue

    # --- Correction phase: Apply learned biases to all samples in the original AnnData ---
    if verbose:
        print(f"\nApplying corrections to all {adata.n_obs} samples...")

    # Get all unique plate categories from the full dataset
    # This ensures that when we apply corrections, we use the correct plate categories.
    all_adata_plate_categories = adata.obs[plate_column].cat.categories

    correction_iterator = tqdm(range(num_genes), desc="Applying correction (genes)", disable=not verbose, unit="gene")
    for gene_idx in correction_iterator:
        # gene_plate_biases is a dict: {plate_id_category_value: bias}
        # These plate_id_category_values are from the control set's plate categories.
        gene_plate_biases_for_current_gene = plate_biases_for_all_genes[gene_idx]

        if not gene_plate_biases_for_current_gene: # Skip if no biases were computed for this gene
            continue

        # Iterate over each plate_id that has a computed bias for this gene
        for plate_id_value, bias_to_subtract in gene_plate_biases_for_current_gene.items():
            # Find all cells in the *full dataset* that belong to this plate_id_value
            # Ensure comparison is with the actual values of the category, not just codes
            cells_on_this_plate_mask = (adata.obs[plate_column] == plate_id_value)

            if np.any(cells_on_this_plate_mask): # If there are any cells on this plate
                current_expression_values = corrected_X[cells_on_this_plate_mask, gene_idx]
                corrected_X[cells_on_this_plate_mask, gene_idx] = current_expression_values - bias_to_subtract

    adata.layers[corrected_layer_name] = corrected_X
    if verbose:
        print(f"\nCorrection complete. Corrected data stored in adata.layers['{corrected_layer_name}'].")

    return adata

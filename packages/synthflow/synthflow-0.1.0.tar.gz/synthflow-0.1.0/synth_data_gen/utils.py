import numpy as np
import pandas as pd
import random
import logging
from typing import List, Dict, Any, Union, Optional, Tuple
from scipy.stats import pearsonr # For correlation
from sklearn.metrics import mean_squared_error # For basic evaluation in some contexts

logger = logging.getLogger(__name__)

def set_random_seed(seed: int) -> None:
    """
    Sets the random seed for reproducibility across different libraries.

    Args:
        seed (int): The integer seed to set.
    """
    random.seed(seed)
    np.random.seed(seed)
    # If PyTorch or TensorFlow were used, their seeds would be set here too:
    # import torch
    # torch.manual_seed(seed)
    # import tensorflow as tf
    # tf.random.set_seed(seed)
    logger.info(f"Random seed set to {seed} for reproducibility.")

def check_input_data_type(data: Union[pd.DataFrame, pd.Series, np.ndarray],
                          expected_type: Union[type, Tuple[type, ...]]) -> None:
    """
    Checks if the input data is of the expected type(s).

    Args:
        data (Union[pd.DataFrame, pd.Series, np.ndarray]): The input data to check.
        expected_type (Union[type, Tuple[type, ...]]): The expected type(s) (e.g., pd.DataFrame,
                                                      (pd.DataFrame, pd.Series)).

    Raises:
        TypeError: If the data is not of the expected type.
    """
    if not isinstance(data, expected_type):
        type_name = expected_type.__name__ if isinstance(expected_type, type) else ", ".join([t.__name__ for t in expected_type])
        raise TypeError(f"Input data must be of type {type_name}, but got {type(data).__name__}.")
    logger.debug(f"Input data type check passed for {type(data).__name__}.")


def get_statistical_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes a DataFrame and returns a summary of its statistical properties.
    This includes numerical statistics (mean, std, min, max, quantiles, correlations)
    and categorical frequencies.

    Args:
        df (pd.DataFrame): The DataFrame to analyze.

    Returns:
        Dict[str, Any]: A dictionary containing the statistical profile.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty statistical profile.")
        return {"summary": "Empty DataFrame"}

    profile: Dict[str, Any] = {
        "overall_shape": df.shape,
        "column_info": {}
    }

    numerical_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(include='object').columns.tolist() # Or 'category' type

    # Numerical statistics
    if numerical_cols:
        profile["numerical_statistics"] = df[numerical_cols].describe().to_dict()
        
        # Calculate correlations only if there's more than one numerical column
        if len(numerical_cols) > 1:
            try:
                # Pearson correlation matrix
                profile["numerical_correlations"] = df[numerical_cols].corr(method='pearson').to_dict()
            except Exception as e:
                logger.warning(f"Could not calculate numerical correlations: {e}")
                profile["numerical_correlations"] = "Error calculating correlations."
        else:
            profile["numerical_correlations"] = "Requires more than one numerical column for correlation."
    else:
        profile["numerical_statistics"] = "No numerical columns found."
        profile["numerical_correlations"] = "No numerical columns found."

    # Categorical frequencies
    if categorical_cols:
        profile["categorical_frequencies"] = {
            col: df[col].value_counts(normalize=True).to_dict()
            for col in categorical_cols
        }
    else:
        profile["categorical_frequencies"] = "No categorical columns found."

    logger.info("Statistical profile generated.")
    return profile

def evaluate_synthetic_data(real_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compares a synthetic dataset to a real dataset based on various statistical measures,
    providing a quantitative assessment of generation quality.

    Args:
        real_df (pd.DataFrame): The original, real DataFrame.
        synthetic_df (pd.DataFrame): The generated synthetic DataFrame.

    Returns:
        Dict[str, Any]: A dictionary containing evaluation metrics.
    """
    if real_df.empty or synthetic_df.empty:
        logger.warning("One or both DataFrames are empty. Cannot perform meaningful evaluation.")
        return {"evaluation_status": "Cannot evaluate with empty DataFrames."}

    # Ensure columns match for fair comparison
    common_cols = list(set(real_df.columns) & set(synthetic_df.columns))
    if not common_cols:
        logger.warning("No common columns found between real and synthetic data for evaluation.")
        return {"evaluation_status": "No common columns for evaluation."}

    real_df_eval = real_df[common_cols]
    synthetic_df_eval = synthetic_df[common_cols]

    metrics: Dict[str, Any] = {
        "real_shape": real_df_eval.shape,
        "synthetic_shape": synthetic_df_eval.shape,
        "column_presence_real_only": list(set(real_df.columns) - set(synthetic_df.columns)),
        "column_presence_synthetic_only": list(set(synthetic_df.columns) - set(real_df.columns)),
        "numerical_metrics": {},
        "categorical_metrics": {},
        "correlation_similarity": {}
    }

    numerical_cols = real_df_eval.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = real_df_eval.select_dtypes(include='object').columns.tolist() # Or 'category' type

    # 1. Numerical Column Similarity (Mean, Std, MSE on distribution shapes)
    for col in numerical_cols:
        real_mean = real_df_eval[col].mean()
        synthetic_mean = synthetic_df_eval[col].mean()
        real_std = real_df_eval[col].std()
        synthetic_std = synthetic_df_eval[col].std()

        # Simple distribution comparison: quantiles
        real_quantiles = real_df_eval[col].quantile([0.25, 0.5, 0.75]).tolist()
        synthetic_quantiles = synthetic_df_eval[col].quantile([0.25, 0.5, 0.75]).tolist()
        
        metrics["numerical_metrics"][col] = {
            "mean_diff": abs(real_mean - synthetic_mean),
            "std_diff": abs(real_std - synthetic_std),
            "real_mean": real_mean,
            "synthetic_mean": synthetic_mean,
            "real_std": real_std,
            "synthetic_std": synthetic_std,
            "real_quantiles": real_quantiles,
            "synthetic_quantiles": synthetic_quantiles,
            # More advanced metrics like Wasserstein distance or K-S test could be added here
        }

    # 2. Categorical Column Similarity (Frequency distribution)
    for col in categorical_cols:
        real_freq = real_df_eval[col].value_counts(normalize=True)
        synthetic_freq = synthetic_df_eval[col].value_counts(normalize=True)

        # Calculate Jensen-Shannon Divergence or a simple frequency error
        # For simplicity, we'll compare individual value frequencies for now.
        common_categories = list(set(real_freq.index) & set(synthetic_freq.index))
        freq_diffs = {}
        for cat in common_categories:
            diff = abs(real_freq.get(cat, 0) - synthetic_freq.get(cat, 0))
            freq_diffs[cat] = diff
        
        metrics["categorical_metrics"][col] = {
            "total_categories_real": len(real_freq),
            "total_categories_synthetic": len(synthetic_freq),
            "frequency_differences_common_cats": freq_diffs,
            "real_freq_top5": real_freq.head(5).to_dict(),
            "synthetic_freq_top5": synthetic_freq.head(5).to_dict()
        }
        # Consider categories present in one but not the other
        metrics["categorical_metrics"][col]["real_only_categories"] = list(set(real_freq.index) - set(synthetic_freq.index))
        metrics["categorical_metrics"][col]["synthetic_only_categories"] = list(set(synthetic_freq.index) - set(real_freq.index))


    # 3. Correlation Matrix Similarity (for numerical columns)
    if len(numerical_cols) > 1:
        try:
            real_corr = real_df_eval[numerical_cols].corr(method='pearson')
            synthetic_corr = synthetic_df_eval[numerical_cols].corr(method='pearson')

            # Calculate the Frobenius norm of the difference between correlation matrices
            # Or element-wise absolute difference
            corr_diff_matrix = (real_corr - synthetic_corr).abs()
            metrics["correlation_similarity"]["mean_abs_corr_diff"] = corr_diff_matrix.values.mean()
            metrics["correlation_similarity"]["max_abs_corr_diff"] = corr_diff_matrix.values.max()
            metrics["correlation_similarity"]["details"] = corr_diff_matrix.to_dict() # For detailed inspection
        except Exception as e:
            logger.warning(f"Could not calculate correlation similarity: {e}")
            metrics["correlation_similarity"] = "Error calculating correlation similarity."
    else:
        metrics["correlation_similarity"] = "Requires more than one numerical column for correlation similarity."

    logger.info("Synthetic data evaluation completed.")
    return metrics

# Example Usage (for testing and demonstration)
if __name__ == "__main__":
    print("--- Testing Utils Module ---")

    # Test set_random_seed
    set_random_seed(42)
    print(f"First random number (numpy): {np.random.rand()}")
    set_random_seed(42) # Should produce the same sequence
    print(f"First random number (numpy, after reset): {np.random.rand()}")
    print("-" * 50)

    # Test check_input_data_type
    df_test = pd.DataFrame({'A': [1, 2], 'B': ['x', 'y']})
    try:
        check_input_data_type(df_test, pd.DataFrame)
        print("check_input_data_type passed for DataFrame.")
    except TypeError as e:
        print(f"Error: {e}")

    try:
        check_input_data_type([1, 2, 3], pd.DataFrame)
    except TypeError as e:
        print(f"Caught expected error (check_input_data_type for list): {e}")
    print("-" * 50)

    # Test get_statistical_profile
    data = {
        'Age': [25, 30, 35, 28, 40, 25, 30, 50, 45, 33],
        'Income': [50000, 60000, 75000, 55000, 80000, 52000, 62000, 90000, 85000, 70000],
        'Gender': ['Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female'],
        'City': ['NY', 'LA', 'NY', 'CHI', 'LA', 'NY', 'CHI', 'LA', 'NY', 'CHI']
    }
    df_real_profile = pd.DataFrame(data)
    profile = get_statistical_profile(df_real_profile)
    print("\nStatistical Profile of Real Data:")
    import json
    print(json.dumps(profile, indent=4))
    print("-" * 50)

    # Test evaluate_synthetic_data
    # Create a synthetic-like DataFrame for testing evaluation
    synthetic_data = {
        'Age': [26, 31, 34, 29, 39, 24, 31, 52, 44, 32], # Slightly shifted
        'Income': [51000, 61000, 74000, 54000, 79000, 53000, 63000, 91000, 84000, 69000], # Slightly noisy
        'Gender': ['Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female'], # Same distribution
        'City': ['NY', 'LA', 'CHI', 'NY', 'LA', 'NY', 'LA', 'CHI', 'NY', 'CHI'] # Slightly different distribution
    }
    df_synthetic_eval = pd.DataFrame(synthetic_data)

    print("\nEvaluating Synthetic Data Quality:")
    evaluation_report = evaluate_synthetic_data(df_real_profile, df_synthetic_eval)
    print(json.dumps(evaluation_report, indent=4))
    print("-" * 50)

    # Test with empty DFs for evaluation
    print("\nTest evaluation with empty DataFrames:")
    empty_report = evaluate_synthetic_data(pd.DataFrame(), pd.DataFrame())
    print(json.dumps(empty_report, indent=4))

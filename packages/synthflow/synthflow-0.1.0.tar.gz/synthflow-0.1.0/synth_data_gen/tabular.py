import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Union, Optional, Tuple
from scipy.stats import multivariate_normal # For correlated numerical data

# Import utilities from the same package
from .utils import set_random_seed, get_statistical_profile, evaluate_synthetic_data

# Set up logging for this module
logger = logging.getLogger(__name__)

class TabularSynthesizer:
    """
    A class to generate synthetic tabular data that mimics the statistical properties
    of a real dataset. It captures univariate distributions, and inter-feature
    correlations for numerical columns, and value frequencies for categorical columns.
    """
    def __init__(self):
        self.numerical_cols: List[str] = []
        self.categorical_cols: List[str] = []
        
        self.numerical_mean: Optional[np.ndarray] = None
        self.numerical_cov: Optional[np.ndarray] = None
        
        self.categorical_distributions: Dict[str, Dict[Any, float]] = {} # {col: {value: probability}}
        
        self.trained = False
        logger.info("TabularSynthesizer initialized.")

    def fit(self, df: pd.DataFrame) -> None:
        """
        Learns the statistical properties from the input DataFrame.

        Args:
            df (pd.DataFrame): The real DataFrame from which to learn distributions.
                               Should contain numerical and/or categorical columns.
        """
        if df.empty:
            logger.error("Input DataFrame is empty. Cannot fit the synthesizer.")
            raise ValueError("Input DataFrame cannot be empty.")

        self.numerical_cols = df.select_dtypes(include=np.number).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
        
        if not self.numerical_cols and not self.categorical_cols:
            logger.error("No numerical or categorical columns found in the DataFrame. Cannot fit.")
            raise ValueError("DataFrame must contain at least one numerical or categorical column.")

        logger.info(f"Fitting TabularSynthesizer on DataFrame with {len(df)} samples.")
        logger.info(f"  Detected numerical columns: {self.numerical_cols}")
        logger.info(f"  Detected categorical columns: {self.categorical_cols}")

        # Learn numerical distributions (mean and covariance for multivariate normal)
        if self.numerical_cols:
            numerical_data = df[self.numerical_cols].dropna() # Drop NaNs for mean/cov calculation
            if numerical_data.empty:
                logger.warning("Numerical data is empty after dropping NaNs. Cannot calculate mean/covariance.")
                self.numerical_mean = None
                self.numerical_cov = None
            elif len(numerical_data) < len(self.numerical_cols):
                 logger.warning("Not enough samples in numerical data after dropping NaNs to calculate covariance. Falling back to univariate normal for each numerical feature.")
                 self.numerical_mean = numerical_data.mean().values
                 self.numerical_cov = np.diag(numerical_data.var().values) # Diagonal covariance (no correlation)
            else:
                self.numerical_mean = numerical_data.mean().values
                self.numerical_cov = numerical_data.cov().values
                # Check if covariance matrix is positive semi-definite (needed for multivariate_normal)
                # If not, add a small epsilon to the diagonal for stability
                try:
                    np.linalg.cholesky(self.numerical_cov)
                except np.linalg.LinAlgError:
                    logger.warning("Covariance matrix not positive semi-definite. Adding a small epsilon to diagonal for stability.")
                    self.numerical_cov += np.eye(self.numerical_cov.shape[0]) * 1e-6 # Add small noise to diagonal

        # Learn categorical distributions (value frequencies)
        self.categorical_distributions = {}
        for col in self.categorical_cols:
            value_counts = df[col].value_counts(normalize=True).to_dict()
            self.categorical_distributions[col] = value_counts
            if not value_counts:
                logger.warning(f"Categorical column '{col}' has no valid entries after value counts. Skipping.")

        self.trained = True
        logger.info("TabularSynthesizer fitting complete.")

    def generate(self, num_samples: int) -> pd.DataFrame:
        """
        Generates synthetic tabular data based on the learned distributions.

        Args:
            num_samples (int): The number of synthetic samples to generate.

        Returns:
            pd.DataFrame: A DataFrame containing the generated synthetic data.
        """
        if not self.trained:
            logger.error("Synthesizer has not been fitted. Call .fit() first.")
            raise RuntimeError("Synthesizer must be fitted before generating data.")
        if num_samples <= 0:
            logger.error("Number of samples to generate must be positive.")
            raise ValueError("`num_samples` must be a positive integer.")

        logger.info(f"Generating {num_samples} synthetic samples.")
        
        synthetic_data = pd.DataFrame()

        # Generate numerical data
        if self.numerical_cols and self.numerical_mean is not None and self.numerical_cov is not None:
            try:
                # Generate from multivariate normal distribution, preserving correlations
                synthetic_numerical = multivariate_normal.rvs(
                    mean=self.numerical_mean,
                    cov=self.numerical_cov,
                    size=num_samples
                )
                synthetic_data = pd.DataFrame(synthetic_numerical, columns=self.numerical_cols)
            except Exception as e:
                logger.error(f"Error generating numerical data from multivariate normal: {e}. Check data or covariance matrix.")
                # Fallback to independent normal if multivariate fails
                synthetic_numerical = np.zeros((num_samples, len(self.numerical_cols)))
                for i, col in enumerate(self.numerical_cols):
                    synthetic_numerical[:, i] = np.random.normal(self.numerical_mean[i], np.sqrt(self.numerical_cov[i, i]), num_samples)
                synthetic_data = pd.DataFrame(synthetic_numerical, columns=self.numerical_cols)
                logger.warning("Falling back to independent normal sampling for numerical features.")
        elif self.numerical_cols: # Case where numerical_mean/cov were not set during fit (e.g., all NaNs)
            logger.warning("No valid numerical statistics found to generate numerical data.")
            for col in self.numerical_cols:
                synthetic_data[col] = np.full(num_samples, np.nan) # Fill with NaNs

        # Generate categorical data
        for col, dist in self.categorical_distributions.items():
            if not dist: # Handle empty distribution (e.g., column had no valid values)
                synthetic_data[col] = np.full(num_samples, np.nan)
                logger.warning(f"Categorical column '{col}' has no distribution. Filling with NaNs.")
                continue

            values = list(dist.keys())
            probabilities = list(dist.values())
            
            # Ensure probabilities sum to 1 (handle floating point errors)
            prob_sum = sum(probabilities)
            if prob_sum > 0:
                probabilities = [p / prob_sum for p in probabilities]
            else:
                logger.warning(f"Probabilities for categorical column '{col}' sum to zero. Cannot sample. Filling with NaNs.")
                synthetic_data[col] = np.full(num_samples, np.nan)
                continue

            synthetic_categorical = np.random.choice(a=values, size=num_samples, p=probabilities)
            # Ensure categorical type in output
            synthetic_data[col] = pd.Series(synthetic_categorical, dtype='category')
            
            # If numerical data was generated first, ensure consistent index alignment
            if self.numerical_cols:
                synthetic_data.index = synthetic_data.index # Ensures same index as numerical part

        # Reorder columns to match original if both types exist
        original_columns_order = self.numerical_cols + self.categorical_cols
        missing_cols_in_synthetic = [col for col in original_columns_order if col not in synthetic_data.columns]
        if missing_cols_in_synthetic:
            logger.warning(f"Some original columns not generated: {missing_cols_in_synthetic}. They might have been empty or invalid during fit.")
            # Add missing columns filled with NaN to maintain structure
            for col in missing_cols_in_synthetic:
                synthetic_data[col] = np.full(num_samples, np.nan)
        
        # Ensure correct column order
        synthetic_data = synthetic_data[original_columns_order]

        logger.info(f"Synthetic data generation complete. Generated {len(synthetic_data)} samples.")
        return synthetic_data

# --- Example Usage ---
if __name__ == "__main__":
    print("--- Testing synth_data_gen.tabular ---")

    # Set random seed for reproducibility
    set_random_seed(42)

    # --- Create a dummy real DataFrame with mixed data types and correlations ---
    num_real_samples = 1000
    
    # Numerical data with correlation
    np.random.seed(42)
    mean = [0, 5, 10]
    cov = [[1.0, 0.8, 0.2], 
           [0.8, 2.0, 0.5], 
           [0.2, 0.5, 3.0]]
    numerical_data = np.random.multivariate_normal(mean, cov, num_real_samples)
    df_numerical = pd.DataFrame(numerical_data, columns=['Age', 'Income', 'Score'])

    # Categorical data
    gender_choices = ['Male', 'Female', 'Non-binary']
    gender_probs = [0.45, 0.50, 0.05]
    education_choices = ['High School', 'Bachelor', 'Master', 'PhD']
    education_probs = [0.3, 0.4, 0.2, 0.1]

    df_categorical = pd.DataFrame({
        'Gender': np.random.choice(gender_choices, num_real_samples, p=gender_probs),
        'Education': np.random.choice(education_choices, num_real_samples, p=education_probs)
    })
    # Ensure categorical columns are of 'category' dtype for consistency
    df_categorical['Gender'] = df_categorical['Gender'].astype('category')
    df_categorical['Education'] = df_categorical['Education'].astype('category')

    # Combine into a single DataFrame
    df_real = pd.concat([df_numerical, df_categorical], axis=1)

    print("--- Original Real DataFrame (Head) ---")
    print(df_real.head())
    print(f"\nOriginal DataFrame shape: {df_real.shape}")
    print("\nOriginal Statistical Profile (first 50 values for categorical for brevity):")
    original_profile = get_statistical_profile(df_real)
    print(original_profile)
    print("-" * 50)

    # Initialize and fit the synthesizer
    synthesizer = TabularSynthesizer()
    synthesizer.fit(df_real)

    # Generate synthetic data
    num_synthetic_samples = 500
    synthetic_df = synthesizer.generate(num_synthetic_samples)

    print("\n--- Synthetic DataFrame (Head) ---")
    print(synthetic_df.head())
    print(f"\nSynthetic DataFrame shape: {synthetic_df.shape}")
    print("\nSynthetic Statistical Profile (first 50 values for categorical for brevity):")
    synthetic_profile = get_statistical_profile(synthetic_df)
    print(synthetic_profile)
    print("-" * 50)

    # --- Evaluate the quality of the synthetic data ---
    print("\n--- Evaluating Synthetic Data Quality ---")
    quality_report = evaluate_synthetic_data(df_real, synthetic_df)
    print(json.dumps(quality_report, indent=4))
    print("-" * 50)

    # --- Test Edge Cases ---
    print("\n--- Testing Edge Cases ---")
    # Test with only numerical data
    synthesizer_num_only = TabularSynthesizer()
    synthesizer_num_only.fit(df_real[['Age', 'Income']])
    synthetic_num_only = synthesizer_num_only.generate(100)
    print(f"\nSynthetic (Numerical Only) shape: {synthetic_num_only.shape}")

    # Test with only categorical data
    synthesizer_cat_only = TabularSynthesizer()
    synthesizer_cat_only.fit(df_real[['Gender', 'Education']])
    synthetic_cat_only = synthesizer_cat_only.generate(100)
    print(f"\nSynthetic (Categorical Only) shape: {synthetic_cat_only.shape}")

    # Test with empty DataFrame (should raise error)
    try:
        synthesizer.fit(pd.DataFrame())
    except ValueError as e:
        print(f"\nCaught expected error: {e}")

    # Test with 0 samples (should raise error)
    try:
        synthesizer.generate(0)
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    print("\n--- synth_data_gen.tabular testing complete ---")

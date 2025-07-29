import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Union, Optional, Tuple, Callable

# Try to import SMOTE from imbalanced-learn
try:
    from imblearn.over_sampling import SMOTE # type: ignore
    from imblearn.over_sampling import BorderlineSMOTE, SVMSMOTE, ADASYN # Optional advanced SMOTE variants
    IMBLEARN_AVAILABLE = True
    logger.info("imbalanced-learn (for SMOTE) library found.")
except ImportError:
    IMBLEARN_AVAILABLE = False
    logging.warning("imbalanced-learn not installed. Run 'pip install imbalanced-learn' to use SMOTE-based augmentation features.")

# Import utilities from the same package
from .utils import set_random_seed, check_input_data_type

# Set up logging for this module
logger = logging.getLogger(__name__)

class DataAugmenter:
    """
    A class providing methods for data augmentation, particularly useful for
    addressing class imbalance in tabular data and expanding datasets.
    """
    def __init__(self):
        logger.info("DataAugmenter initialized.")

    def smote_tabular(self, 
                      X: pd.DataFrame, 
                      y: pd.Series, 
                      sampling_strategy: Union[str, float, Dict] = 'auto',
                      k_neighbors: int = 5,
                      smote_type: str = 'regular',
                      random_state: Optional[int] = None) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Applies Synthetic Minority Over-sampling Technique (SMOTE) to address
        class imbalance in tabular datasets. SMOTE generates synthetic samples
        for minority classes.

        Args:
            X (pd.DataFrame): The input features DataFrame.
            y (pd.Series): The target labels Series (must be categorical/discrete).
                           This Series defines the minority/majority classes.
            sampling_strategy (Union[str, float, Dict]): Sampling strategy for SMOTE.
                                                         'auto', float (ratio), or dict {class: num_samples}.
            k_neighbors (int): Number of nearest neighbors to use for SMOTE.
            smote_type (str): Type of SMOTE to use ('regular', 'borderline', 'svm', 'adasyn').
                              Requires `imbalanced-learn` for all types.
            random_state (Optional[int]): Seed for reproducibility.

        Returns:
            Tuple[pd.DataFrame, pd.Series]: A tuple containing the augmented features (X_resampled)
                                            and labels (y_resampled).
        """
        if not IMBLEARN_AVAILABLE:
            logger.error("imbalanced-learn is not installed. SMOTE-based augmentation is unavailable.")
            return X, y

        set_random_seed(random_state)
        logger.info(f"Applying SMOTE (type: '{smote_type}') to address class imbalance.")
        logger.info(f"  Original class distribution: {y.value_counts().to_dict()}")

        smote_instance: Optional[SMOTE] = None
        if smote_type == 'regular':
            smote_instance = SMOTE(sampling_strategy=sampling_strategy, k_neighbors=k_neighbors, random_state=random_state)
        elif smote_type == 'borderline':
            smote_instance = BorderlineSMOTE(sampling_strategy=sampling_strategy, k_neighbors=k_neighbors, random_state=random_state)
        elif smote_type == 'svm':
            smote_instance = SVMSMOTE(sampling_strategy=sampling_strategy, k_neighbors=k_neighbors, random_state=random_state)
        elif smote_type == 'adasyn':
            smote_instance = ADASYN(sampling_strategy=sampling_strategy, n_neighbors=k_neighbors, random_state=random_state)
        else:
            logger.error(f"Invalid SMOTE type '{smote_type}'. Using 'regular' SMOTE.")
            smote_instance = SMOTE(sampling_strategy=sampling_strategy, k_neighbors=k_neighbors, random_state=random_state)
        
        try:
            X_resampled, y_resampled = smote_instance.fit_resample(X, y)
            logger.info(f"SMOTE applied. New class distribution: {y_resampled.value_counts().to_dict()}")
            return X_resampled, y_resampled
        except Exception as e:
            logger.error(f"Error applying SMOTE: {e}. Ensure features are numerical and labels are discrete.")
            logger.error("SMOTE typically requires numerical features. Consider encoding categorical features first.")
            return X, y # Return original data on error

    def feature_space_augmentation(self, 
                                   X: Union[np.ndarray, pd.DataFrame],
                                   num_augmented_samples: int,
                                   noise_level: float = 0.05,
                                   strategy: str = 'add_noise', # 'add_noise', 'interpolate'
                                   interpolation_factor: float = 0.5, # For 'interpolate' strategy
                                   random_state: Optional[int] = None) -> Union[np.ndarray, pd.DataFrame]:
        """
        Augments numerical data by adding random noise or interpolating between existing samples.
        This technique creates new samples within the existing feature space.

        Args:
            X (Union[np.ndarray, pd.DataFrame]): The input numerical features.
            num_augmented_samples (int): The number of synthetic samples to generate.
            noise_level (float): The standard deviation of the Gaussian noise to add for 'add_noise' strategy.
                                 Or the maximum perturbation for interpolation.
            strategy (str): The augmentation strategy ('add_noise' or 'interpolate').
            interpolation_factor (float): For 'interpolate' strategy, a value between 0 and 1.
                                          0.5 means exactly halfway between two samples.
            random_state (Optional[int]): Seed for reproducibility.

        Returns:
            Union[np.ndarray, pd.DataFrame]: The newly generated augmented samples.
        """
        if num_augmented_samples <= 0:
            logger.warning("`num_augmented_samples` must be positive. Returning empty data.")
            return pd.DataFrame() if isinstance(X, pd.DataFrame) else np.array([])
        if X.empty:
            logger.error("Input data is empty. Cannot perform feature space augmentation.")
            return pd.DataFrame() if isinstance(X, pd.DataFrame) else np.array([])

        set_random_seed(random_state)
        logger.info(f"Applying feature space augmentation with strategy: '{strategy}', generating {num_augmented_samples} samples.")

        X_np = X.to_numpy() if isinstance(X, pd.DataFrame) else X
        if X_np.ndim == 1: # Reshape 1D array to (n_samples, 1)
            X_np = X_np.reshape(-1, 1)

        num_original_samples, num_features = X_np.shape
        augmented_samples_np = np.zeros((num_augmented_samples, num_features))

        if strategy == 'add_noise':
            if noise_level <= 0:
                logger.warning("`noise_level` must be positive for 'add_noise' strategy. Using 0.05.")
                noise_level = 0.05
            
            # Randomly pick existing samples to perturb
            indices = np.random.choice(num_original_samples, num_augmented_samples, replace=True)
            for i, original_idx in enumerate(indices):
                noise = np.random.normal(0, noise_level, num_features)
                augmented_samples_np[i] = X_np[original_idx] + noise
        
        elif strategy == 'interpolate':
            if not (0 <= interpolation_factor <= 1):
                logger.warning("`interpolation_factor` must be between 0 and 1 for 'interpolate' strategy. Using 0.5.")
                interpolation_factor = 0.5

            for i in range(num_augmented_samples):
                # Randomly pick two distinct original samples
                idx1, idx2 = np.random.choice(num_original_samples, 2, replace=False)
                sample1 = X_np[idx1]
                sample2 = X_np[idx2]
                
                # Interpolate between them: new = sample1 + factor * (sample2 - sample1)
                augmented_samples_np[i] = sample1 + interpolation_factor * (sample2 - sample1)
                # Add a small random noise to further diversify (optional)
                augmented_samples_np[i] += np.random.normal(0, noise_level * 0.1, num_features)
        else:
            logger.error(f"Unsupported augmentation strategy: '{strategy}'. Returning empty data.")
            return pd.DataFrame() if isinstance(X, pd.DataFrame) else np.array([])

        logger.info(f"Feature space augmentation complete. Generated {num_augmented_samples} samples.")
        
        if isinstance(X, pd.DataFrame):
            # Maintain original column names if input was DataFrame
            return pd.DataFrame(augmented_samples_np, columns=X.columns)
        return augmented_samples_np


# --- Example Usage ---
if __name__ == "__main__":
    print("--- Testing synth_data_gen.augmentation ---")

    # Set random seed for reproducibility
    set_random_seed(42)

    # --- Create a dummy imbalanced DataFrame for SMOTE ---
    num_majority = 1000
    num_minority = 100
    
    # Majority class data
    X_majority = np.random.normal(loc=5, scale=1, size=(num_majority, 2))
    y_majority = np.zeros(num_majority)

    # Minority class data (distinct from majority to make SMOTE interesting)
    X_minority = np.random.normal(loc=10, scale=1, size=(num_minority, 2))
    y_minority = np.ones(num_minority)

    X_imb = pd.DataFrame(np.vstack([X_majority, X_minority]), columns=['Feature_A', 'Feature_B'])
    y_imb = pd.Series(np.hstack([y_majority, y_minority]), name='Target')

    print("--- Original Imbalanced Dataset ---")
    print(f"Original X shape: {X_imb.shape}")
    print(f"Original y distribution: {y_imb.value_counts().to_dict()}")
    print("-" * 50)

    aug = DataAugmenter()

    # --- Test 1: SMOTE Tabular Augmentation ---
    if IMBLEARN_AVAILABLE:
        print("\n--- Test 1: Applying SMOTE (regular) ---")
        X_resampled, y_resampled = aug.smote_tabular(X_imb, y_imb, smote_type='regular', random_state=42)
        print(f"SMOTE Regular - Resampled X shape: {X_resampled.shape}")
        print(f"SMOTE Regular - Resampled y distribution: {y_resampled.value_counts().to_dict()}")
        print("-" * 50)

        print("\n--- Test 1.1: Applying BorderlineSMOTE ---")
        X_resampled_bl, y_resampled_bl = aug.smote_tabular(X_imb, y_imb, smote_type='borderline', random_state=42)
        print(f"BorderlineSMOTE - Resampled X shape: {X_resampled_bl.shape}")
        print(f"BorderlineSMOTE - Resampled y distribution: {y_resampled_bl.value_counts().to_dict()}")
        print("-" * 50)
    else:
        print("\nSkipping SMOTE tests: imbalanced-learn not installed.")
        print("To run, please install: pip install imbalanced-learn")
        print("-" * 50)

    # --- Test 2: Feature Space Augmentation ---
    print("\n--- Test 2: Feature Space Augmentation (Add Noise) ---")
    X_numerical_data = pd.DataFrame(np.random.rand(100, 3), columns=['F1', 'F2', 'F3'])
    
    augmented_X_noise = aug.feature_space_augmentation(
        X_numerical_data,
        num_augmented_samples=50,
        noise_level=0.1,
        strategy='add_noise',
        random_state=42
    )
    print(f"Add Noise Augmentation - Generated X shape: {augmented_X_noise.shape}")
    print("Generated Augmented Samples (first 5):")
    print(augmented_X_noise.head())
    print("-" * 50)

    print("\n--- Test 2.1: Feature Space Augmentation (Interpolate) ---")
    augmented_X_interpolate = aug.feature_space_augmentation(
        X_numerical_data,
        num_augmented_samples=50,
        interpolation_factor=0.7, # 70% towards the second point
        strategy='interpolate',
        random_state=42
    )
    print(f"Interpolate Augmentation - Generated X shape: {augmented_X_interpolate.shape}")
    print("Generated Augmented Samples (first 5):")
    print(augmented_X_interpolate.head())
    print("-" * 50)

    # --- Test Edge Cases ---
    print("\n--- Testing Edge Cases ---")
    # Test SMOTE with non-numerical data (should return original)
    if IMBLEARN_AVAILABLE:
        X_non_num = pd.DataFrame({'cat': ['A', 'B', 'A', 'B'], 'num': [1,2,3,4]})
        y_non_num = pd.Series([0, 1, 0, 1])
        X_res_non_num, y_res_non_num = aug.smote_tabular(X_non_num, y_non_num, random_state=42)
        print(f"\nSMOTE on non-numerical data (expected original): {X_res_non_num.shape}, {y_res_non_num.value_counts().to_dict()}")

    # Test feature augmentation with 0 samples (should return empty)
    empty_aug = aug.feature_space_augmentation(X_numerical_data, 0, strategy='add_noise')
    print(f"Feature Augmentation 0 samples: {empty_aug.shape}")

    # Test feature augmentation with empty input (should return empty)
    empty_input_aug = aug.feature_space_augmentation(pd.DataFrame(), 10, strategy='add_noise')
    print(f"Feature Augmentation empty input: {empty_input_aug.shape}")

    print("\n--- synth_data_gen.augmentation testing complete ---")

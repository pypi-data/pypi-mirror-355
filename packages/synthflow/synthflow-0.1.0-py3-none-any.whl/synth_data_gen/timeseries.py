import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Union, Optional, Tuple
from statsmodels.tsa.seasonal import seasonal_decompose # For time series decomposition
from sklearn.linear_model import LinearRegression # For trend fitting
from sklearn.metrics import mean_squared_error, r2_score # For evaluation
import matplotlib.pyplot as plt
import seaborn as sns
import datetime # For generating date ranges

# Import utilities from the same package
from .utils import set_random_seed, get_statistical_profile, evaluate_synthetic_data

# Set up logging for this module
logger = logging.getLogger(__name__)

class TimeSeriesSynthesizer:
    """
    A class to generate synthetic time series data by decomposing a real time series
    into its trend, seasonal, and residual components, and then synthesizing new
    data based on the learned patterns of these components.

    It supports single or multiple time series (DataFrame columns).
    """
    def __init__(self):
        self.decomposition_results: Dict[str, Any] = {} # Stores results of seasonal_decompose for each series
        self.trend_models: Dict[str, LinearRegression] = {}
        self.seasonal_patterns: Dict[str, np.ndarray] = {}
        self.residual_stats: Dict[str, Dict[str, float]] = {} # mean, std of residuals
        self.index_freq: Optional[str] = None
        self.seasonal_period: Optional[int] = None
        self.trained = False
        logger.info("TimeSeriesSynthesizer initialized.")

    def fit(self, ts_data: Union[pd.Series, pd.DataFrame], seasonal_period: int, model_type: str = 'additive') -> None:
        """
        Learns the trend, seasonal, and residual components from the input time series data.

        Args:
            ts_data (Union[pd.Series, pd.DataFrame]): The real time series data.
                                                       Must have a DatetimeIndex and no NaNs.
            seasonal_period (int): The number of observations in a seasonal cycle (e.g., 7 for daily data with weekly seasonality).
            model_type (str): Type of seasonal model ('additive' or 'multiplicative'). Defaults to 'additive'.
        """
        if ts_data.empty:
            logger.error("Input time series data is empty. Cannot fit the synthesizer.")
            raise ValueError("Input time series data cannot be empty.")
        if not isinstance(ts_data.index, pd.DatetimeIndex):
            logger.error("Input time series must have a pandas DatetimeIndex.")
            raise ValueError("Input time series must have a pandas DatetimeIndex.")
        if ts_data.isnull().any().any():
            logger.warning("Input time series contains NaN values. Decomposition and fitting may be affected.")
            # Optionally, fill NaNs or raise error: ts_data = ts_data.interpolate(method='linear')
        if seasonal_period <= 1:
            logger.error("Seasonal period must be greater than 1 for seasonal decomposition.")
            raise ValueError("`seasonal_period` must be greater than 1.")
        
        self.seasonal_period = seasonal_period
        self.index_freq = pd.infer_freq(ts_data.index)
        if self.index_freq is None:
            logger.warning("Could not infer frequency from DatetimeIndex. Ensure consistent frequency for generation.")
            # Set a default frequency if needed, or rely on user specifying start_date + num_steps

        logger.info(f"Fitting TimeSeriesSynthesizer on data with {len(ts_data)} steps.")
        logger.info(f"  Seasonal Period: {self.seasonal_period}, Decomposition Model: '{model_type}'")

        # Handle multiple series if DataFrame, otherwise process single Series
        series_names = [ts_data.name] if isinstance(ts_data, pd.Series) else ts_data.columns.tolist()
        
        self.decomposition_results = {}
        self.trend_models = {}
        self.seasonal_patterns = {}
        self.residual_stats = {}

        for series_name in series_names:
            series = ts_data[series_name] if isinstance(ts_data, pd.DataFrame) else ts_data
            
            # Decompose the time series
            try:
                # `extrapolate_trend='freq'` handles NaN values at the beginning/end of trend
                decomposition = seasonal_decompose(series, model=model_type, period=self.seasonal_period, extrapolate_trend='freq')
                self.decomposition_results[series_name] = decomposition
                logger.info(f"Decomposition successful for series '{series_name}'.")

                # Learn Trend: Fit a linear regression model
                if decomposition.trend is not None and not decomposition.trend.dropna().empty:
                    trend_data = decomposition.trend.dropna()
                    X_trend = np.arange(len(trend_data)).reshape(-1, 1) # Time index as feature
                    y_trend = trend_data.values
                    
                    trend_model = LinearRegression()
                    trend_model.fit(X_trend, y_trend)
                    self.trend_models[series_name] = trend_model
                    logger.info(f"  Trend model fitted for '{series_name}'.")
                else:
                    logger.warning(f"  Trend component for '{series_name}' is empty or all NaN. Cannot fit trend model.")
                    self.trend_models[series_name] = None # Mark as unavailable

                # Learn Seasonality: Store the actual seasonal pattern
                if decomposition.seasonal is not None and not decomposition.seasonal.dropna().empty:
                    # Take one full cycle of the seasonal component
                    self.seasonal_patterns[series_name] = decomposition.seasonal.dropna().values[:self.seasonal_period]
                    logger.info(f"  Seasonal pattern learned for '{series_name}'.")
                else:
                    logger.warning(f"  Seasonal component for '{series_name}' is empty or all NaN. Cannot learn seasonal pattern.")
                    self.seasonal_patterns[series_name] = None # Mark as unavailable

                # Learn Residuals: Store mean and std deviation
                if decomposition.resid is not None and not decomposition.resid.dropna().empty:
                    resid_data = decomposition.resid.dropna()
                    self.residual_stats[series_name] = {
                        'mean': resid_data.mean(),
                        'std': resid_data.std() if resid_data.shape[0] > 1 else 0.0 # Handle single residual case
                    }
                    if self.residual_stats[series_name]['std'] < 1e-9: # Prevent very small std leading to no noise
                        self.residual_stats[series_name]['std'] = 1e-6
                    logger.info(f"  Residual statistics learned for '{series_name}'.")
                else:
                    logger.warning(f"  Residual component for '{series_name}' is empty or all NaN. Cannot learn residual statistics.")
                    self.residual_stats[series_name] = None # Mark as unavailable

            except Exception as e:
                logger.error(f"Error during decomposition or fitting for series '{series_name}': {e}")
                self.decomposition_results[series_name] = None # Mark as failed
                self.trend_models[series_name] = None
                self.seasonal_patterns[series_name] = None
                self.residual_stats[series_name] = None

        self.trained = True
        logger.info("TimeSeriesSynthesizer fitting complete.")

    def generate(self, num_steps: int, start_date: Optional[str] = None) -> Union[pd.Series, pd.DataFrame]:
        """
        Generates synthetic time series data based on the learned components.

        Args:
            num_steps (int): The number of time steps to generate.
            start_date (Optional[str]): The start date for the synthetic time series (e.g., '2023-01-01').
                                        If None, uses current date or a default.

        Returns:
            Union[pd.Series, pd.DataFrame]: The generated synthetic time series data.
        """
        if not self.trained:
            logger.error("Synthesizer has not been fitted. Call .fit() first.")
            raise RuntimeError("Synthesizer must be fitted before generating data.")
        if num_steps <= 0:
            logger.error("Number of steps to generate must be positive.")
            raise ValueError("`num_steps` must be a positive integer.")

        logger.info(f"Generating {num_steps} synthetic time series steps.")

        # Determine the datetime index for the synthetic data
        if start_date:
            try:
                start_dt = pd.to_datetime(start_date)
            except ValueError:
                logger.warning(f"Invalid start_date '{start_date}'. Using current date.")
                start_dt = pd.to_datetime(datetime.date.today())
        else:
            start_dt = pd.to_datetime(datetime.date.today())

        # If original frequency was inferred, use it. Otherwise, assume daily or 'D'
        if self.index_freq:
            synthetic_index = pd.date_range(start=start_dt, periods=num_steps, freq=self.index_freq)
        else:
            synthetic_index = pd.date_range(start=start_dt, periods=num_steps, freq='D')
            logger.warning(f"Original frequency not inferred. Defaulting to daily ('D') frequency for synthetic index.")

        synthetic_series_dict = {}

        # Iterate through each series that was fitted
        for series_name in self.trend_models.keys():
            if self.trend_models[series_name] is None and self.seasonal_patterns[series_name] is None and self.residual_stats[series_name] is None:
                logger.warning(f"Skipping generation for series '{series_name}' due to failed fitting.")
                synthetic_series_dict[series_name] = pd.Series(np.full(num_steps, np.nan), index=synthetic_index)
                continue

            # Generate Trend Component
            if self.trend_models[series_name]:
                X_gen_trend = np.arange(num_steps).reshape(-1, 1) # Time index for synthetic series
                synthetic_trend = self.trend_models[series_name].predict(X_gen_trend)
            else:
                synthetic_trend = np.full(num_steps, self.decomposition_results[series_name].trend.mean() if self.decomposition_results[series_name].trend is not None else 0.0) # Flat trend if no model
                logger.warning(f"  No trend model for '{series_name}'. Generating flat trend.")


            # Generate Seasonal Component
            if self.seasonal_patterns[series_name] is not None and self.seasonal_period:
                # Repeat the learned seasonal pattern to match num_steps
                synthetic_seasonal = np.tile(self.seasonal_patterns[series_name], int(np.ceil(num_steps / self.seasonal_period)))[:num_steps]
            else:
                synthetic_seasonal = np.zeros(num_steps) # No seasonality
                logger.warning(f"  No seasonal pattern for '{series_name}'. Generating no seasonality.")

            # Generate Residual Component
            if self.residual_stats[series_name]:
                resid_mean = self.residual_stats[series_name]['mean']
                resid_std = self.residual_stats[series_name]['std']
                synthetic_residuals = np.random.normal(loc=resid_mean, scale=resid_std, size=num_steps)
            else:
                synthetic_residuals = np.zeros(num_steps) # No noise
                logger.warning(f"  No residual statistics for '{series_name}'. Generating no residuals (noise).")

            # Combine components based on original model type (additive or multiplicative)
            # Assuming additive model for simplicity if not explicitly stored
            original_model_type = self.decomposition_results[series_name].model if self.decomposition_results[series_name] else 'additive'

            if original_model_type == 'multiplicative':
                # Ensure trend and seasonal are non-zero for multiplicative
                synthetic_trend_safe = np.where(synthetic_trend == 0, 1e-9, synthetic_trend)
                synthetic_seasonal_safe = np.where(synthetic_seasonal == 0, 1e-9, synthetic_seasonal)
                synthetic_values = synthetic_trend_safe * synthetic_seasonal_safe * (1 + synthetic_residuals) # Residuals are % change
            else: # Additive
                synthetic_values = synthetic_trend + synthetic_seasonal + synthetic_residuals
            
            synthetic_series_dict[series_name] = pd.Series(synthetic_values, index=synthetic_index, name=series_name)

        if len(synthetic_series_dict) == 1 and isinstance(ts_data, pd.Series):
            return synthetic_series_dict[list(synthetic_series_dict.keys())[0]]
        else:
            return pd.DataFrame(synthetic_series_dict, index=synthetic_index)

# --- Example Usage ---
if __name__ == "__main__":
    print("--- Testing synth_data_gen.timeseries ---")

    # Set random seed for reproducibility
    set_random_seed(42)

    # --- Create a dummy real time series with trend, seasonality, and noise ---
    num_days = 365 * 2 # Two years of daily data
    date_range = pd.date_range(start='2022-01-01', periods=num_days, freq='D')

    # Simulate trend: increasing over time
    trend = np.linspace(0, 100, num_days)

    # Simulate weekly seasonality
    weekly_seasonality = np.sin(np.arange(num_days) / 7 * 2 * np.pi) * 10 # Weekly cycle with amplitude 10

    # Simulate daily pattern within week (e.g., higher on weekdays)
    day_of_week_pattern = np.array([0, 0, 0, 0, 0, 5, 5]) # Mon-Fri low, Sat-Sun high
    daily_seasonality = np.tile(day_of_week_pattern, int(np.ceil(num_days / 7)))[:num_days]

    # Combine seasonal patterns
    seasonal = weekly_seasonality + daily_seasonality

    # Simulate noise (residuals)
    noise = np.random.normal(0, 2, num_days)

    # Combine all components (additive model)
    real_ts_values = trend + seasonal + noise
    real_ts = pd.Series(real_ts_values, index=date_range, name='Daily_Metric')

    print("--- Original Real Time Series (Head) ---")
    print(real_ts.head(10))
    print(f"\nOriginal Time Series shape: {real_ts.shape}")
    
    # Plot original time series
    plt.figure(figsize=(12, 6))
    sns.lineplot(x=real_ts.index, y=real_ts.values, label='Original Data')
    plt.title('Original Real Time Series (Daily_Metric)')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.grid(True)
    plt.savefig("original_time_series.png")
    plt.show()
    print("-" * 50)

    # Initialize and fit the synthesizer
    # Use seasonal_period = 7 for weekly seasonality
    synthesizer = TimeSeriesSynthesizer()
    synthesizer.fit(real_ts, seasonal_period=7, model_type='additive')

    # Generate synthetic time series data
    num_synthetic_steps = 365 # Generate one year of synthetic data
    synthetic_ts = synthesizer.generate(num_synthetic_steps, start_date='2024-01-01')

    print("\n--- Synthetic Time Series (Head) ---")
    print(synthetic_ts.head(10))
    print(f"\nSynthetic Time Series shape: {synthetic_ts.shape}")

    # Plot synthetic time series
    plt.figure(figsize=(12, 6))
    sns.lineplot(x=synthetic_ts.index, y=synthetic_ts.values, label='Synthetic Data', color='orange')
    plt.title('Synthetic Time Series (Daily_Metric)')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.grid(True)
    plt.savefig("synthetic_time_series.png")
    plt.show()
    print("-" * 50)

    # --- Evaluate the quality of the synthetic data (simple comparison of stats) ---
    print("\n--- Evaluating Synthetic Time Series Quality ---")
    # For time series, a simple `evaluate_synthetic_data` might be less meaningful than visual inspection
    # and comparing ACF/PACF, but we'll use the existing utility for structural consistency.
    # Note: `evaluate_synthetic_data` focuses on static statistical profiles, not temporal dynamics.
    
    # Create simple dataframes for evaluation utility for consistency
    df_real_eval = pd.DataFrame(real_ts)
    df_synthetic_eval = pd.DataFrame(synthetic_ts)

    quality_report = evaluate_synthetic_data(df_real_eval, df_synthetic_eval)
    print(json.dumps(quality_report, indent=4))
    print("-" * 50)

    # --- Test with multiple time series (DataFrame) ---
    print("\n--- Testing with Multiple Time Series (DataFrame) ---")
    num_cols = 3
    multi_ts_data = pd.DataFrame(index=date_range)
    for i in range(num_cols):
        multi_ts_data[f'Metric_{i+1}'] = trend + (i * 5) + (weekly_seasonality * (i+1)/2) + np.random.normal(0, 1.5, num_days)

    print("\nOriginal Multi-Series Data (Head):")
    print(multi_ts_data.head())

    multi_synthesizer = TimeSeriesSynthesizer()
    multi_synthesizer.fit(multi_ts_data, seasonal_period=7, model_type='additive')
    synthetic_multi_ts = multi_synthesizer.generate(num_synthetic_steps, start_date='2024-01-01')
    print("\nSynthetic Multi-Series Data (Head):")
    print(synthetic_multi_ts.head())
    print(f"\nSynthetic Multi-Series shape: {synthetic_multi_ts.shape}")
    print("-" * 50)


    # --- Test Edge Cases ---
    print("\n--- Testing Edge Cases ---")
    # Test with empty DataFrame (should raise error)
    try:
        synthesizer.fit(pd.Series(dtype='float64'), seasonal_period=7)
    except ValueError as e:
        print(f"\nCaught expected error (empty Series): {e}")

    # Test with 0 steps (should raise error)
    try:
        synthesizer.generate(0)
    except ValueError as e:
        print(f"Caught expected error (0 steps): {e}")
    
    # Cleanup generated plot files
    if os.path.exists("original_time_series.png"): os.remove("original_time_series.png")
    if os.path.exists("synthetic_time_series.png"): os.remove("synthetic_time_series.png")
    print("\n--- synth_data_gen.timeseries testing complete ---")

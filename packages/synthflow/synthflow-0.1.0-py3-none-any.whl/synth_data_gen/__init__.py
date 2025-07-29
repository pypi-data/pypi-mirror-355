# This file makes 'synth_data_gen' a Python package.

# Define the package version
__version__ = "0.1.0"

# Import key classes and functions directly into the package namespace
# This allows users to do `from synth_data_gen import TabularSynthesizer`
# instead of `from synth_data_gen.tabular import TabularSynthesizer`.

# Core data generation modules
from .tabular import TabularSynthesizer # Placeholder for future class
from .timeseries import TimeSeriesSynthesizer # Placeholder for future class
from .augmentation import DataAugmenter # Placeholder for future class
from .privacy import PrivacyPreservingSynthesizer # Placeholder for future class
from .text import TextSynthesizer # Placeholder for future class
from .config import ConfigManager # Placeholder for future class

# General utilities
from .utils import set_random_seed, get_statistical_profile, evaluate_synthetic_data

# Set up a NullHandler for the package's logger to prevent "No handlers could be found" warnings
# if the consuming application doesn't configure logging.
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())


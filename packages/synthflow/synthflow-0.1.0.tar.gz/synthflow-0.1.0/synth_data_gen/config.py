import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    A class to manage configuration for synthetic data generation, allowing for
    profile-based or constraint-driven synthesis.
    """
    def __init__(self):
        self.config: Dict[str, Any] = {}
        logger.info("ConfigManager initialized.")

    def load_config(self, config_data: Dict[str, Any]) -> None:
        """
        Loads configuration data into the manager.

        Args:
            config_data (Dict[str, Any]): A dictionary containing configuration parameters.
                                          This could include statistical profiles, constraints,
                                          or generation parameters.
        """
        if not isinstance(config_data, dict):
            raise TypeError("Config data must be a dictionary.")
        if not config_data:
            logger.warning("Loading an empty configuration. No settings will be applied.")

        self.config.update(config_data)
        logger.info(f"Configuration loaded with {len(config_data)} new items.")

    def get_config(self, key: Optional[str] = None) -> Union[Any, Dict[str, Any]]:
        """
        Retrieves a specific configuration value or the entire configuration.

        Args:
            key (Optional[str]): The key of the configuration item to retrieve.
                                 If None, the entire configuration dictionary is returned.

        Returns:
            Union[Any, Dict[str, Any]]: The value associated with the key, or the
                                        entire configuration dictionary.

        Raises:
            KeyError: If the specified key does not exist in the configuration.
        """
        if key is None:
            return self.config
        if key not in self.config:
            raise KeyError(f"Configuration key '{key}' not found.")
        return self.config[key]

    def set_config(self, key: str, value: Any) -> None:
        """
        Sets or updates a specific configuration item.

        Args:
            key (str): The key of the configuration item to set.
            value (Any): The value to assign to the configuration item.
        """
        self.config[key] = value
        logger.info(f"Configuration item '{key}' set to '{value}'.")

    def validate_config(self) -> List[str]:
        """
        Conceptual method to validate the loaded configuration.
        This method would check for required parameters, valid ranges,
        and consistency across settings.

        Returns:
            List[str]: A list of warning or error messages found during validation.
                       Returns an empty list if validation passes.
        """
        validation_messages: List[str] = []
        logger.info("Performing conceptual configuration validation.")

        # Example validation rules (conceptual)
        if "data_type" in self.config and self.config["data_type"] not in ["tabular", "timeseries", "text"]:
            validation_messages.append("Warning: 'data_type' in config is not one of the expected values (tabular, timeseries, text).")
        
        if "num_samples" in self.config and not isinstance(self.config["num_samples"], int):
            validation_messages.append("Error: 'num_samples' must be an integer.")
        elif "num_samples" in self.config and self.config["num_samples"] <= 0:
            validation_messages.append("Error: 'num_samples' must be greater than 0.")

        # More complex validation based on specific module needs would go here.
        if not validation_messages:
            logger.info("Configuration validation passed (conceptually).")
        else:
            for msg in validation_messages:
                logger.warning(f"Config Validation: {msg}")
        
        return validation_messages

    def clear_config(self) -> None:
        """
        Clears all loaded configuration settings.
        """
        self.config = {}
        logger.info("Configuration cleared.")

# Example Usage (for testing and demonstration)
if __name__ == "__main__":
    print("--- Testing ConfigManager ---")
    config_manager = ConfigManager()

    # Load initial configuration
    initial_config = {
        "data_type": "tabular",
        "num_samples": 1000,
        "features": {
            "Age": {"type": "numerical", "min": 18, "max": 65},
            "Gender": {"type": "categorical", "values": ["Male", "Female", "Other"]}
        },
        "output_format": "csv"
    }
    config_manager.load_config(initial_config)
    print("\nLoaded Configuration:")
    print(config_manager.get_config())

    # Get a specific config item
    print(f"\nNumber of samples: {config_manager.get_config('num_samples')}")

    # Set a new config item
    config_manager.set_config("random_seed", 42)
    print(f"\nRandom seed set: {config_manager.get_config('random_seed')}")

    # Update an existing config item
    config_manager.set_config("output_format", "json")
    print(f"\nOutput format updated: {config_manager.get_config('output_format')}")

    # Validate configuration
    print("\nValidating Configuration:")
    validation_errors = config_manager.validate_config()
    if validation_errors:
        for error in validation_errors:
            print(f"- {error}")
    else:
        print("No issues found in current configuration.")

    # Test validation with bad data
    print("\nTesting validation with invalid 'num_samples':")
    config_manager.set_config("num_samples", -50)
    validation_errors_bad = config_manager.validate_config()
    for error in validation_errors_bad:
        print(f"- {error}")

    print("\nTesting validation with invalid 'num_samples' type:")
    config_manager.set_config("num_samples", "abc")
    validation_errors_bad_type = config_manager.validate_config()
    for error in validation_errors_bad_type:
        print(f"- {error}")

    # Clear configuration
    config_manager.clear_config()
    print(f"\nConfiguration after clearing: {config_manager.get_config()}")

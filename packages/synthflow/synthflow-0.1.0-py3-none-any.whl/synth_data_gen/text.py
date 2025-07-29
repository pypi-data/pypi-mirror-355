import logging
import random
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class TextSynthesizer:
    """
    A class for generating simple or structured synthetic text, focusing on
    template-based and rule-based approaches rather than complex Natural Language Generation (NLG).
    """
    def __init__(self):
        self.templates: List[str] = []
        self.placeholders: Dict[str, List[Any]] = {}
        self.rules: Dict[str, Any] = {} # For more complex rule-based generation (conceptual)
        self.trained = False
        logger.info("TextSynthesizer initialized.")

    def fit(self, 
            templates: List[str], 
            placeholders: Dict[str, List[Any]], 
            rules: Optional[Dict[str, Any]] = None) -> None:
        """
        Configures the text synthesizer with predefined templates, placeholder values,
        and optional rules.

        Args:
            templates (List[str]): A list of string templates. Placeholders should be
                                   enclosed in double curly braces, e.g., "Hello {{name}}!".
            placeholders (Dict[str, List[Any]]): A dictionary where keys are placeholder
                                                  names (without braces) and values are
                                                  lists of possible values for that placeholder.
                                                  Example: {"name": ["Alice", "Bob"], "product": ["A", "B"]}
            rules (Optional[Dict[str, Any]]): A dictionary defining rules for more complex
                                              generation logic. (Conceptual for future extension)
        """
        if not templates:
            raise ValueError("Templates list cannot be empty.")
        if not placeholders:
            raise ValueError("Placeholders dictionary cannot be empty.")

        self.templates = templates
        self.placeholders = placeholders
        self.rules = rules if rules is not None else {}
        self.trained = True
        logger.info(f"TextSynthesizer fitted with {len(templates)} templates and {len(placeholders)} placeholders.")

    def generate(self, num_samples: int) -> List[str]:
        """
        Generates a specified number of synthetic text samples based on the configured
        templates and placeholder values.

        Args:
            num_samples (int): The number of synthetic text samples to generate.

        Returns:
            List[str]: A list of generated synthetic text strings.
        """
        if not self.trained:
            raise RuntimeError("TextSynthesizer must be fitted before generation.")
        if num_samples <= 0:
            raise ValueError("Number of samples to generate must be positive.")

        generated_texts: List[str] = []
        for _ in range(num_samples):
            # Select a random template
            template = random.choice(self.templates)
            generated_text = template

            # Replace placeholders in the selected template
            for placeholder_name, possible_values in self.placeholders.items():
                if f"{{{{{placeholder_name}}}}}" in generated_text:
                    if not possible_values:
                        logger.warning(f"Placeholder '{placeholder_name}' has no values defined. Skipping replacement.")
                        continue
                    replacement_value = random.choice(possible_values)
                    generated_text = generated_text.replace(f"{{{{{placeholder_name}}}}}", str(replacement_value))
            
            # Apply conceptual rules if any (future extension)
            # For now, rules are not actively processed in generation

            generated_texts.append(generated_text)

        logger.info(f"Generated {len(generated_texts)} synthetic text samples.")
        return generated_texts

    def get_placeholder_definitions(self) -> Dict[str, List[Any]]:
        """
        Returns the dictionary of defined placeholders and their possible values.

        Returns:
            Dict[str, List[Any]]: The placeholders dictionary.
        """
        return self.placeholders

    def get_templates(self) -> List[str]:
        """
        Returns the list of configured templates.

        Returns:
            List[str]: The list of templates.
        """
        return self.templates

# Example Usage (for testing and demonstration)
if __name__ == "__main__":
    print("--- Testing TextSynthesizer ---")
    synthesizer = TextSynthesizer()

    # Define templates and placeholders
    templates_data = [
        "Customer {{customer_id}} placed an order for {{product_name}}.",
        "New user registration from {{country}} with email {{email}}.",
        "Logged event: {{event_type}} at {{timestamp}}."
    ]

    placeholders_data = {
        "customer_id": [f"CUST{i:04d}" for i in range(100, 105)],
        "product_name": ["Laptop", "Monitor", "Keyboard", "Mouse"],
        "country": ["USA", "Canada", "Germany", "Japan"],
        "email": [f"user{i}@example.com" for i in range(1, 6)],
        "event_type": ["login_success", "login_failed", "page_view", "checkout_complete"],
        "timestamp": [pd.Timestamp('2023-01-01') + pd.Timedelta(minutes=i) for i in range(10)]
    }

    # Fit the synthesizer
    synthesizer.fit(templates_data, placeholders_data)

    # Generate synthetic text samples
    print("\nGenerated 5 samples:")
    synthetic_texts = synthesizer.generate(5)
    for text in synthetic_texts:
        print(text)

    print("\nGenerated 10 samples:")
    synthetic_texts_2 = synthesizer.generate(10)
    for text in synthetic_texts_2:
        print(text)

    # Test edge cases
    print("\n--- Testing Edge Cases ---")
    try:
        empty_synthesizer = TextSynthesizer()
        empty_synthesizer.generate(1)
    except RuntimeError as e:
        print(f"Caught expected error (not fitted): {e}")

    try:
        synthesizer.generate(0)
    except ValueError as e:
        print(f"Caught expected error (num_samples = 0): {e}")

    try:
        empty_templates_synth = TextSynthesizer()
        empty_templates_synth.fit([], placeholders_data)
    except ValueError as e:
        print(f"Caught expected error (empty templates): {e}")

    try:
        empty_placeholders_synth = TextSynthesizer()
        empty_placeholders_synth.fit(templates_data, {})
    except ValueError as e:
        print(f"Caught expected error (empty placeholders): {e}")

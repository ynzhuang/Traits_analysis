"""
API Key Service for managing API keys from JSON files.
"""

import json
import logging
from typing import Dict, Any


class APIKeyService:
    """Service for loading and managing API keys."""
    
    @staticmethod
    def load_api_keys(api_keys_file: str) -> Dict[str, Any]:
        """
        Reads API keys from a JSON file.
        
        Args:
            api_keys_file: Path to the JSON file containing API keys
            
        Returns:
            Dictionary containing API keys and configuration
            
        Raises:
            FileNotFoundError: If the API keys file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        logging.info(f"Reading API keys from {api_keys_file}")
        try:
            with open(api_keys_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"API keys file not found: {api_keys_file}")
            raise
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in API keys file {api_keys_file}: {e}")
            raise
    
    @staticmethod
    def validate_api_keys(api_keys: Dict[str, Any], required_providers: list = None) -> bool:
        """
        Validate that required API keys are present.
        
        Args:
            api_keys: Dictionary of API keys
            required_providers: List of required provider names (e.g., ['openai', 'claude'])
            
        Returns:
            True if all required keys are present, False otherwise
        """
        if not required_providers:
            return True
            
        missing_keys = []
        for provider in required_providers:
            if provider not in api_keys or not api_keys[provider]:
                missing_keys.append(provider)
        
        if missing_keys:
            logging.error(f"Missing API keys for providers: {missing_keys}")
            return False
            
        return True
    
    @staticmethod
    def add_model_override(api_keys: Dict[str, Any], provider: str, model_name: str) -> Dict[str, Any]:
        """
        Add a model name override to the API keys dictionary.
        
        Args:
            api_keys: Dictionary of API keys
            provider: Provider name (e.g., 'openai', 'claude')
            model_name: Specific model name to use
            
        Returns:
            Updated API keys dictionary
        """
        api_keys = api_keys.copy()  # Don't modify original
        api_keys[f"{provider}_model"] = model_name
        logging.info(f"Added model override for {provider}: {model_name}")
        return api_keys
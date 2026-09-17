"""
LLM Service for initializing and managing language models.
"""

import logging
from typing import Dict, Any, Tuple, Type, Optional
from langchain.chat_models import init_chat_model
from pydantic import BaseModel
from .langsmith_service import LangSmithService


class LLMService:
    """Service for initializing and managing language models."""
    
    # Map user-friendly names to internal LangChain provider names
    PROVIDER_MAP = {
        'openai': 'openai',
        'gemini': 'google_genai',
        'claude': 'anthropic'
    }
    
    # Define default models for each provider
    DEFAULT_MODELS = {
        'openai': 'gpt-4o',
        'gemini': 'gemini-2.5-pro',
        'claude': 'claude-sonnet-4-20250514'
    }
    
    @classmethod
    def get_llm(
        cls,
        provider_name: str,
        api_keys: Dict[str, Any],
        structured_output_class: Type[BaseModel],
        temperature: float = 0
    ) -> Tuple[Any, str]:
        """
        Initialize and return the specified language model with structured output.
        
        Args:
            provider_name: Name of the provider ('openai', 'gemini', 'claude')
            api_keys: Dictionary containing API keys and configuration
            structured_output_class: Pydantic model class for structured output
            temperature: Temperature setting for the model
            
        Returns:
            Tuple of (llm_instance, explicit_model_name)
            
        Raises:
            ValueError: If the provider is not supported
        """
        # Configure LangSmith tracing if available
        LangSmithService.configure_tracing(api_keys)
        
        # Determine the model name to use
        explicit_model = api_keys.get(provider_name).get('model', cls.DEFAULT_MODELS.get(provider_name))
        

        if not explicit_model:
            logging.error(f"Unsupported model provider: {provider_name}")
            raise ValueError(f"Unsupported model provider: {provider_name}")

        logging.info(f"Initializing language model provider: {provider_name}, model: {explicit_model}")
        
        # Log LangSmith configuration
        if LangSmithService.is_tracing_enabled():
            logging.info(f"LangSmith tracing enabled for {provider_name} model: {explicit_model}")

        # Set up model arguments
        model_args = {
            "model": explicit_model,
            "model_provider": cls.PROVIDER_MAP.get(provider_name),
            "temperature": float(temperature)  # Ensure temperature is always a float
        }
        
        # Add provider-specific configurations
        cls._add_provider_specific_args(provider_name, api_keys, model_args, explicit_model)

        # Initialize the model using the universal function
        base_llm = init_chat_model(**model_args)
        
        # Initialize the model using the universal function
        # Use function calling method for better compatibility with complex schemas
        llm = base_llm.with_structured_output(structured_output_class, method="function_calling")
        
        return llm, explicit_model
    
    @classmethod
    def _add_provider_specific_args(cls, provider_name: str, api_keys: Dict[str, Any], model_args: Dict[str, Any], explicit_model: str) -> None:
        """
        Add provider-specific arguments to model configuration.
        
        Args:
            provider_name: Name of the provider
            api_keys: Dictionary containing API keys
            model_args: Model arguments dictionary to modify
            explicit_model: The explicit model name being used
        """

        model_args["api_key"] = api_keys.get(provider_name).get('api-key')
        if provider_name == 'openai':
            model_args["seed"] = str(42)

        # Set max_tokens with model-specific limits to prevent API errors
        # Define model-specific token limits based on actual API constraints
        MODEL_TOKEN_LIMITS = {
            'claude-sonnet-4-20250514': 16384,
            'claude-sonnet-4': 16384,
            'gpt-4o': 16384,
            'gpt-4': 8192,
            'gpt-4.1':32768,
            'gemini-2.5-pro': 32768,
            'gemini-pro': 32768
        }
        
        # Get the actual model name being used
        model_name = explicit_model
        model_limit = MODEL_TOKEN_LIMITS.get(model_name, 8192)  # Conservative default
        
        # Allow override from config but cap at model limit
        provider_config = api_keys.get(provider_name)
        if isinstance(provider_config, dict):
            requested_tokens = provider_config.get('max_tokens', model_limit)
        else:
            requested_tokens = model_limit
        
        # Cap at model's actual limit to prevent API errors
        max_tokens = min(requested_tokens, model_limit)
        
        model_args["max_tokens"] = max_tokens
        logging.info(f"TOKEN LIMIT DEBUG: Model {model_name} limit: {model_limit}, requested: {requested_tokens}, final: {max_tokens}")
        
        # Log warning if we had to cap the tokens
        if requested_tokens > model_limit:
            logging.warning(f"TOKEN LIMIT WARNING: Requested {requested_tokens} tokens but model {model_name} only supports {model_limit}. Capped to {max_tokens}.")
    
    @classmethod
    def get_supported_providers(cls) -> list:
        """
        Get list of supported provider names.
        
        Returns:
            List of supported provider names
        """
        return list(cls.PROVIDER_MAP.keys())
    
    @classmethod
    def get_default_model(cls, provider_name: str) -> Optional[str]:
        """
        Get the default model for a provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Default model name or None if provider not supported
        """
        return cls.DEFAULT_MODELS.get(provider_name)
    
    @classmethod
    def validate_provider(cls, provider_name: str) -> bool:
        """
        Validate if a provider is supported.
        
        Args:
            provider_name: Name of the provider to validate
            
        Returns:
            True if provider is supported, False otherwise
        """
        return provider_name in cls.PROVIDER_MAP
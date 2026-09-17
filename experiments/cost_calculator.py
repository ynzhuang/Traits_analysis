"""
Cost Calculator for AI model usage estimation and tracking.
"""

import logging
from typing import Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class ModelPricing:
    """Pricing information for a model."""
    input_cost_per_1k: float  # Cost per 1K input tokens
    output_cost_per_1k: float  # Cost per 1K output tokens
    name: str


class CostCalculator:
    """Service for calculating and tracking AI model costs."""
    
    # Pricing data (as of 2025) - costs per 1K tokens
    MODEL_PRICING = {
        # OpenAI models
        'gpt-4o': ModelPricing(0.0025, 0.01, 'GPT-4o'),
        'gpt-4': ModelPricing(0.03, 0.06, 'GPT-4'),
        'gpt-4-turbo': ModelPricing(0.01, 0.03, 'GPT-4 Turbo'),
        'gpt-3.5-turbo': ModelPricing(0.0005, 0.0015, 'GPT-3.5 Turbo'),
        
        # Anthropic Claude models
        'claude-sonnet-4': ModelPricing(0.003, 0.015, 'Claude Sonnet 4'),
        'claude-sonnet-4-20250514': ModelPricing(0.003, 0.015, 'Claude Sonnet 4'),
        'claude-3-opus': ModelPricing(0.015, 0.075, 'Claude 3 Opus'),
        'claude-3-sonnet': ModelPricing(0.003, 0.015, 'Claude 3 Sonnet'),
        'claude-3-haiku': ModelPricing(0.00025, 0.00125, 'Claude 3 Haiku'),
        
        # Google Gemini models
        'gemini-2.5-pro': ModelPricing(0.00125, 0.005, 'Gemini 2.5 Pro'),
        'gemini-pro': ModelPricing(0.0005, 0.0015, 'Gemini Pro'),
        'gemini-1.5-pro': ModelPricing(0.00125, 0.005, 'Gemini 1.5 Pro'),
    }
    
    def __init__(self):
        """Initialize the cost calculator."""
        self.total_cost = 0.0
        self.model_costs = {}
        self.token_usage = {}
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string.
        
        Args:
            text: Input text
            
        Returns:
            Estimated number of tokens
        """
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    def get_model_pricing(self, model_name: str) -> ModelPricing:
        """
        Get pricing information for a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            ModelPricing object
            
        Raises:
            ValueError: If model pricing is not available
        """
        pricing = self.MODEL_PRICING.get(model_name)
        if not pricing:
            # Try to find a partial match
            for key, value in self.MODEL_PRICING.items():
                if key in model_name or model_name in key:
                    logging.warning(f"Using approximate pricing for {model_name} based on {key}")
                    return value
            
            # Default to GPT-4o pricing if no match found
            logging.warning(f"No pricing data for {model_name}, using GPT-4o pricing as default")
            return self.MODEL_PRICING['gpt-4o']
        
        return pricing
    
    def estimate_cost(self, model_name: str, input_text: str, estimated_output_tokens: int = 1000) -> Tuple[float, Dict[str, Any]]:
        """
        Estimate the cost for a single API call.
        
        Args:
            model_name: Name of the model
            input_text: Input text
            estimated_output_tokens: Estimated number of output tokens
            
        Returns:
            Tuple of (estimated_cost, cost_breakdown)
        """
        pricing = self.get_model_pricing(model_name)
        input_tokens = self.estimate_tokens(input_text)
        
        input_cost = (input_tokens / 1000) * pricing.input_cost_per_1k
        output_cost = (estimated_output_tokens / 1000) * pricing.output_cost_per_1k
        total_cost = input_cost + output_cost
        
        cost_breakdown = {
            'model': pricing.name,
            'input_tokens': input_tokens,
            'estimated_output_tokens': estimated_output_tokens,
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': total_cost,
            'pricing': {
                'input_per_1k': pricing.input_cost_per_1k,
                'output_per_1k': pricing.output_cost_per_1k
            }
        }
        
        return total_cost, cost_breakdown
    
    def calculate_actual_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate actual cost based on token usage.
        
        Args:
            model_name: Name of the model
            input_tokens: Actual input tokens used
            output_tokens: Actual output tokens generated
            
        Returns:
            Actual cost
        """
        pricing = self.get_model_pricing(model_name)
        
        input_cost = (input_tokens / 1000) * pricing.input_cost_per_1k
        output_cost = (output_tokens / 1000) * pricing.output_cost_per_1k
        total_cost = input_cost + output_cost
        
        return total_cost
    
    def add_usage(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        Add usage and calculate cost for tracking.
        
        Args:
            model_name: Name of the model
            input_tokens: Input tokens used
            output_tokens: Output tokens generated
            
        Returns:
            Cost for this usage
        """
        cost = self.calculate_actual_cost(model_name, input_tokens, output_tokens)
        
        # Track total cost
        self.total_cost += cost
        
        # Track per-model costs
        if model_name not in self.model_costs:
            self.model_costs[model_name] = 0.0
        self.model_costs[model_name] += cost
        
        # Track token usage
        if model_name not in self.token_usage:
            self.token_usage[model_name] = {'input': 0, 'output': 0}
        self.token_usage[model_name]['input'] += input_tokens
        self.token_usage[model_name]['output'] += output_tokens
        
        return cost
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of costs and usage.
        
        Returns:
            Dictionary with cost and usage summary
        """
        return {
            'total_cost': self.total_cost,
            'model_costs': self.model_costs.copy(),
            'token_usage': self.token_usage.copy(),
            'models_used': list(self.model_costs.keys())
        }
    
    def format_cost_summary(self) -> str:
        """
        Format cost summary as a readable string.
        
        Returns:
            Formatted cost summary
        """
        summary = self.get_summary()
        
        lines = [
            f"💰 Total Cost: ${summary['total_cost']:.4f}",
            "",
            "📊 Cost Breakdown by Model:"
        ]
        
        for model, cost in summary['model_costs'].items():
            usage = summary['token_usage'].get(model, {'input': 0, 'output': 0})
            lines.append(f"  • {model}: ${cost:.4f}")
            lines.append(f"    - Input tokens: {usage['input']:,}")
            lines.append(f"    - Output tokens: {usage['output']:,}")
        
        return "\n".join(lines)
"""
Trait schema definition.

This module contains the Trait model which represents individual traits
extracted from clinical trial eligibility criteria.
"""

from pydantic import BaseModel, Field


class Trait(BaseModel):
    """
    Represents an individual trait extracted from a clinical trial criterion.
    
    This is the comprehensive trait model that consolidates the functionality
    previously split between Trait (decompose_criteria.py) and TraitInfo 
    (analyze_criteria_decomposition_agreement.py).
    """
    trait: str = Field(description="The name of the extracted trait")
    category: str = Field(description="The category of the trait")
    value: str = Field(description="The value, threshold, or description of the trait")
    source_text: str = Field(description="Exact text/phrase from original criterion")
    original_trait_phrase: str = Field(description="Original phrase for the trait name")
    original_value_phrase: str = Field(description="Original phrase for the value")

    class Config:
        """Pydantic configuration."""
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "trait": "age",
                "category": "demographic",
                "value": "≥18 years",
                "source_text": "Patients must be 18 years of age or older",
                "original_trait_phrase": "18 years of age or older",
                "original_value_phrase": "≥18 years"
            }
        }
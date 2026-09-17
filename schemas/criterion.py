"""
Criterion schema definition.

This module contains the Criterion model which represents individual
eligibility criteria from clinical trials.
"""

from pydantic import BaseModel, Field
from typing import List

from .trait import Trait


class Criterion(BaseModel):
    """
    Represents an individual eligibility criterion from a clinical trial.
    
    A criterion contains the original text, logical representation, and
    a list of extracted traits.
    """
    type: str = Field(description="The type of criterion (inclusion or exclusion)")
    original_text: str = Field(description="The original text of the criterion")
    logic: str = Field(description="The logical representation of the criterion")
    traits: List[Trait] = Field(description="A list of traits extracted from the criterion")

    class Config:
        """Pydantic configuration."""
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "type": "inclusion",
                "original_text": "Patients must be 18 years of age or older",
                "logic": "age >= 18",
                "traits": [
                    {
                        "trait": "age",
                        "category": "demographic",
                        "value": "≥18 years",
                        "source_text": "Patients must be 18 years of age or older",
                        "original_trait_phrase": "18 years of age or older",
                        "original_value_phrase": "≥18 years"
                    }
                ]
            }
        }
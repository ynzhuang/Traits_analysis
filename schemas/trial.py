"""
Trial schema definition.

This module contains the Trial and DecomposedCriteria models which represent
clinical trial metadata and decomposed eligibility criteria.
"""

from pydantic import BaseModel, Field
from typing import List, Optional

from .criterion import Criterion


class Trial(BaseModel):
    """
    Represents clinical trial metadata.
    
    This model encapsulates rich trial information beyond just the trial ID,
    providing a foundation for enhanced trial representation.
    """
    trial_id: str = Field(description="The NCT number or identifier of the trial")
    title: Optional[str] = Field(default=None, description="The official title of the trial")
    nct_number: Optional[str] = Field(default=None, description="The NCT registry number")
    phase: Optional[str] = Field(default=None, description="The phase of the trial (e.g., 'Phase I', 'Phase II')")
    status: Optional[str] = Field(default=None, description="The current status of the trial")
    sponsor: Optional[str] = Field(default=None, description="The primary sponsor of the trial")
    condition: Optional[str] = Field(default=None, description="The primary condition being studied")
    intervention_type: Optional[str] = Field(default=None, description="Type of intervention (e.g., 'Drug', 'Device')")
    study_type: Optional[str] = Field(default=None, description="Type of study (e.g., 'Interventional', 'Observational')")

    class Config:
        """Pydantic configuration."""
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "trial_id": "NCT12345678",
                "title": "A Phase II Study of Drug X in Patients with Cancer",
                "nct_number": "NCT12345678",
                "phase": "Phase II",
                "status": "Recruiting",
                "sponsor": "Example Pharmaceutical Company",
                "condition": "Cancer",
                "intervention_type": "Drug",
                "study_type": "Interventional"
            }
        }


class DecomposedCriteria(BaseModel):
    """
    Represents the complete decomposition of a clinical trial's eligibility criteria.
    
    This model combines trial metadata with the decomposed criteria, providing
    a comprehensive representation of the trial and its eligibility requirements.
    """
    trial: Trial = Field(description="The trial metadata")
    criteria: List[Criterion] = Field(description="A list of decomposed criteria")

    class Config:
        """Pydantic configuration."""
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "trial": {
                    "trial_id": "NCT12345678",
                    "title": "A Phase II Study of Drug X in Patients with Cancer",
                    "nct_number": "NCT12345678",
                    "phase": "Phase II",
                    "status": "Recruiting",
                    "sponsor": "Example Pharmaceutical Company",
                    "condition": "Cancer",
                    "intervention_type": "Drug",
                    "study_type": "Interventional"
                },
                "criteria": [
                    {
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
                ]
            }
        }
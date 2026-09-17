"""
Agreement analysis schema definitions for n-reviewer analysis.

This module contains the models for analyzing agreement across multiple reviewers (n ≥ 2).
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class MatchStatus(str, Enum):
    """Status of trait matching between reviewers."""
    EXACT_MATCH = "perfect"
    VALUE_MISMATCH = "value_mismatch"
    CATEGORY_MISMATCH = "category_mismatch"
    GRANULARITY_MISMATCH = "granularity_mismatch"
    SYNONYM_VARIATION = "synonym_variation"
    MISSING = "missing"


class NormalizationRule(str, Enum):
    """Types of normalization rules applied."""
    ABBREVIATION_STANDARDIZATION = "abbreviation_standardization"
    UNIT_CONVERSION = "unit_conversion"
    SYNONYM_MAPPING = "synonym_mapping"
    CASE_NORMALIZATION = "case_normalization"
    PUNCTUATION_REMOVAL = "punctuation_removal"


class AnalysisMetadata(BaseModel):
    """Metadata about the analysis."""
    total_trials: int = Field(description="Total number of trials analyzed")
    total_criteria: int = Field(description="Total number of criteria analyzed")
    total_reviewers: int = Field(description="Total number of reviewers")
    reviewer_identifiers: List[str] = Field(description="List of reviewer identifiers")
    analysis_timestamp: str = Field(description="ISO timestamp of analysis")
    
    class Config:
        extra = "forbid"


class AgreementDistribution(BaseModel):
    """Distribution of agreement levels."""
    perfect_agreement: int = Field(description="Number with perfect agreement")
    majority_agreement: int = Field(description="Number with majority agreement")
    no_agreement: int = Field(description="Number with no agreement")
    
    class Config:
        extra = "forbid"


class OverallSummary(BaseModel):
    """Overall summary statistics."""
    total_traits: int = Field(description="Total number of unique traits")
    total_criteria: int = Field(description="Total number of criteria")
    total_reviewers: int = Field(description="Total number of reviewers")
    agreement_distribution: AgreementDistribution = Field(description="Distribution of agreement levels")
    
    class Config:
        extra = "forbid"


class AgreementSummaryNew(BaseModel):
    """New agreement summary structure."""
    overall: OverallSummary = Field(description="Overall summary statistics")
    
    class Config:
        extra = "forbid"


class ReviewerExtraction(BaseModel):
    """Extraction by a specific reviewer."""
    trait: Optional[str] = Field(default=None, description="Trait name")
    category: Optional[str] = Field(default=None, description="Trait category")
    value: Optional[str] = Field(default=None, description="Trait value")
    source_text: Optional[str] = Field(default=None, description="Source text")
    original_trait_phrase: Optional[str] = Field(default=None, description="Original trait phrase")
    original_value_phrase: Optional[str] = Field(default=None, description="Original value phrase")
    match_status: MatchStatus = Field(description="Match status for this reviewer")
    discrepancies: Optional[str] = Field(default=None, description="Qualitative explanation of discrepancies")
    
    class Config:
        extra = "forbid"


class ConsensusTrait(BaseModel):
    """Consensus trait across reviewers."""
    consensus_trait_signature: str = Field(description="Consensus trait signature in format trait|category|value")
    normalized_trait_name: str = Field(description="Standardized trait name")
    normalized_category: str = Field(description="Standardized category")
    normalized_value: str = Field(description="Standardized value")
    reviewer_extractions: Dict[str, ReviewerExtraction] = Field(description="Extractions by each reviewer")
    
    class Config:
        extra = "forbid"


class CriterionAnalysis(BaseModel):
    """Analysis for a single criterion."""
    criterion_index: int = Field(description="Index of the criterion")
    type: str = Field(description="inclusion or exclusion")
    original_text: str = Field(description="Original criterion text")
    consensus_logic: str = Field(description="Consensus logical expression")
    total_unique_traits: int = Field(description="Total unique traits found")
    reviewer_trait_counts: Dict[str, int] = Field(description="Number of traits per reviewer")
    trait_overlap_percentage: float = Field(description="Percentage of trait overlap")
    traits: List[ConsensusTrait] = Field(description="List of consensus traits")
    
    class Config:
        extra = "forbid"


class TrialAnalysis(BaseModel):
    """Analysis for a single trial."""
    trial_id: str = Field(description="NCT number")
    total_criteria: int = Field(description="Total criteria in trial")
    total_unique_traits: int = Field(description="Total unique traits in trial")
    agreement_distribution: AgreementDistribution = Field(description="Agreement distribution for this trial")
    criteria: List[CriterionAnalysis] = Field(description="Analysis for each criterion")
    
    class Config:
        extra = "forbid"


class SemanticNormalizationLog(BaseModel):
    """Log entry for semantic normalization."""
    original_variations: List[str] = Field(description="Original variations found")
    normalized_form: str = Field(description="Normalized form used")
    normalization_rule: NormalizationRule = Field(description="Rule applied")
    affected_reviewers: List[str] = Field(description="Reviewers affected by this normalization")
    
    class Config:
        extra = "forbid"


class QualityMetrics(BaseModel):
    """Quality metrics for the analysis."""
    trait_extraction_consistency: float = Field(description="Consistency in trait extraction")
    category_assignment_consistency: float = Field(description="Consistency in category assignment")
    value_specification_consistency: float = Field(description="Consistency in value specification")
    granularity_consistency: float = Field(description="Consistency in granularity")
    
    class Config:
        extra = "forbid"


class AgreementAnalysisResult(BaseModel):
    """
    Agreement analysis result matching the updated prompt schema.
    """
    analysis_metadata: AnalysisMetadata = Field(description="Analysis metadata")
    agreement_summary: AgreementSummaryNew = Field(description="Agreement summary")
    trials: List[TrialAnalysis] = Field(description="Trial-by-trial analysis")
    semantic_normalization_log: List[SemanticNormalizationLog] = Field(description="Normalization log")
    quality_metrics: QualityMetrics = Field(description="Quality metrics")
    
    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "analysis_metadata": {
                    "total_trials": 5,
                    "total_criteria": 50,
                    "total_reviewers": 3,
                    "reviewer_identifiers": ["reviewer_1", "reviewer_2", "reviewer_3"],
                    "analysis_timestamp": "2024-01-15T10:30:00Z"
                },
                "agreement_summary": {
                    "overall": {
                        "total_traits": 150,
                        "total_criteria": 50,
                        "total_reviewers": 3,
                        "agreement_distribution": {
                            "perfect_agreement": 30,
                            "majority_agreement": 15,
                            "no_agreement": 5
                        }
                    }
                },
                "trials": [],
                "semantic_normalization_log": [],
                "quality_metrics": {
                    "trait_extraction_consistency": 0.85,
                    "category_assignment_consistency": 0.78,
                    "value_specification_consistency": 0.82,
                    "granularity_consistency": 0.75
                }
            }
        }
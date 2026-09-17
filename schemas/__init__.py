"""
Schemas package for the criteria analyzer.

This package contains all Pydantic models used throughout the application,
organized into logical modules for better maintainability.
"""

# Core models
from .trait import Trait
from .criterion import Criterion
from .trial import Trial, DecomposedCriteria

# Agreement analysis models
from .agreement_analysis import (
    # Schema models
    MatchStatus,
    NormalizationRule,
    AnalysisMetadata,
    AgreementDistribution,
    OverallSummary,
    AgreementSummaryNew,
    ReviewerExtraction,
    ConsensusTrait,
    CriterionAnalysis,
    TrialAnalysis,
    SemanticNormalizationLog,
    QualityMetrics,
    AgreementAnalysisResult,
)

__all__ = [
    # Core models
    "Trait",
    "Criterion",
    "Trial",
    "DecomposedCriteria",
    
    # Agreement analysis models
    "MatchStatus",
    "NormalizationRule",
    "AnalysisMetadata",
    "AgreementDistribution",
    "OverallSummary",
    "AgreementSummaryNew",
    "ReviewerExtraction",
    "ConsensusTrait",
    "CriterionAnalysis",
    "TrialAnalysis",
    "SemanticNormalizationLog",
    "QualityMetrics",
    "AgreementAnalysisResult",
]
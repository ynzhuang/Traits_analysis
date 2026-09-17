import argparse
import json
import os
import logging
import time
import itertools
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set
from collections import defaultdict
import difflib

from pydantic import BaseModel, Field, field_validator
import json as json_module

# Import services
from services.api_key_service import APIKeyService
from services.llm_service import LLMService
from services.prompt_service import PromptService
from services.cache_service import CacheService
from services.chain_service import ChainService

# Import schemas
from schemas import Trait
from schemas.agreement_analysis import (
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_decomposed_files(input_dir: str) -> Dict[str, Dict]:
    """Load all decomposed criteria JSON files from the input directory."""
    decomposed_files = {}
    input_path = Path(input_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory {input_dir} does not exist")
    
    json_files = list(input_path.glob("*.json"))
    if not json_files:
        raise ValueError(f"No JSON files found in {input_dir}")
    
    logging.info(f"Found {len(json_files)} JSON files in {input_dir}")
    
    for file_path in json_files:
        logging.info(f"Loading {file_path.name}")
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Extract reviewer/model name from filename
        # Expected format: ici_criteria_sample-{provider}-{model}-{timestamp}.json
        filename_parts = file_path.stem.split('-')
        if len(filename_parts) >= 3:
            provider = filename_parts[1]
            model = filename_parts[2]
            # DEBUG: Add type checking for reviewer name construction
            logging.info(f"DEBUG: Building reviewer name with types - provider: {type(provider)} = '{provider}'")
            logging.info(f"DEBUG: model: {type(model)} = '{model}'")
            
            # Ensure components are strings
            provider_str = str(provider)
            model_str = str(model)
            reviewer_name = f"{provider_str}-{model_str}"
            logging.info(f"DEBUG: Successfully constructed reviewer name: {reviewer_name}")
        else:
            reviewer_name = str(file_path.stem)
        
        decomposed_files[reviewer_name] = data
    
    return decomposed_files

def normalize_trait(trait: Dict[str, str]) -> Tuple[str, str, str]:
    """Normalize trait for comparison by standardizing case and removing extra whitespace."""
    return (
        trait['trait'].lower().strip(),
        trait['category'].lower().strip(),
        trait['value'].lower().strip()
    )

def calculate_semantic_similarity(trait1: Dict[str, str], trait2: Dict[str, str]) -> float:
    """Calculate semantic similarity between two traits using simple string matching."""
    # Normalize traits
    t1_name, t1_cat, t1_val = normalize_trait(trait1)
    t2_name, t2_cat, t2_val = normalize_trait(trait2)
    
    # Calculate similarity for each component
    name_sim = difflib.SequenceMatcher(None, t1_name, t2_name).ratio()
    cat_sim = difflib.SequenceMatcher(None, t1_cat, t2_cat).ratio()
    val_sim = difflib.SequenceMatcher(None, t1_val, t2_val).ratio()
    
    # Weighted average (trait name is most important)
    similarity = 0.5 * name_sim + 0.3 * cat_sim + 0.2 * val_sim
    return similarity

def match_traits(traits1: List[Dict], traits2: List[Dict], threshold: float = 0.8) -> Tuple[List[Tuple], List[Dict], List[Dict]]:
    """Match traits between two reviewers using semantic similarity."""
    matches = []
    unmatched_1 = traits1.copy()
    unmatched_2 = traits2.copy()
    
    # Find best matches
    for trait1 in traits1:
        best_match = None
        best_similarity = 0
        
        for trait2 in traits2:
            similarity = calculate_semantic_similarity(trait1, trait2)
            if similarity > best_similarity and similarity >= threshold:
                best_similarity = similarity
                best_match = trait2
        
        if best_match:
            matches.append((trait1, best_match))
            if trait1 in unmatched_1:
                unmatched_1.remove(trait1)
            if best_match in unmatched_2:
                unmatched_2.remove(best_match)
    
    return matches, unmatched_1, unmatched_2

def calculate_agreement_metrics(matches: List[Tuple], unmatched_1: List[Dict], unmatched_2: List[Dict]) -> Dict[str, float]:
    """Calculate precision, recall, F1, Jaccard, and Cohen's kappa."""
    true_positives = len(matches)
    false_positives = len(unmatched_2)
    false_negatives = len(unmatched_1)
    
    # Precision and Recall
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    
    # F1 Score
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # Jaccard Index
    jaccard = true_positives / (true_positives + false_positives + false_negatives) if (true_positives + false_positives + false_negatives) > 0 else 0
    
    # Cohen's Kappa (simplified calculation)
    total = true_positives + false_positives + false_negatives
    if total == 0:
        cohen_kappa = 1.0
    else:
        observed_agreement = true_positives / total
        expected_agreement = 0.5  # Simplified assumption
        cohen_kappa = (observed_agreement - expected_agreement) / (1 - expected_agreement) if expected_agreement != 1 else 1.0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'jaccard_index': jaccard,
        'cohen_kappa': cohen_kappa
    }

def calculate_fleiss_kappa(trait_matrix: List[List[int]]) -> float:
    """
    Calculate Fleiss' Kappa for multi-reviewer agreement.
    
    Args:
        trait_matrix: Matrix where rows are criteria and columns are reviewers.
                     Each cell contains 1 if trait is present, 0 if absent.
    
    Returns:
        Fleiss' kappa coefficient (-1 to 1, where 1 = perfect agreement)
    """
    logging.info(f"DEBUG: calculate_fleiss_kappa called with matrix size: {len(trait_matrix) if trait_matrix else 0}")
    
    if not trait_matrix or len(trait_matrix) == 0:
        logging.error("DEBUG: Empty or None trait matrix provided")
        return 0.0
    
    n_criteria = len(trait_matrix)
    n_reviewers = len(trait_matrix[0]) if trait_matrix else 0
    
    logging.info(f"DEBUG: Matrix dimensions: {n_criteria} criteria x {n_reviewers} reviewers")
    
    if n_reviewers < 3:
        logging.error(f"DEBUG: Insufficient reviewers for Fleiss' kappa: {n_reviewers} < 3")
        return 0.0  # Fleiss' kappa requires at least 3 reviewers
    
    # Calculate observed agreement for each criterion
    p_i = []  # Proportion of agreement for each criterion
    for idx, criterion_ratings in enumerate(trait_matrix):
        # Count agreements (both present or both absent)
        agreements = 0
        total_pairs = 0
        
        for i in range(n_reviewers):
            for j in range(i + 1, n_reviewers):
                total_pairs += 1
                if criterion_ratings[i] == criterion_ratings[j]:
                    agreements += 1
        
        if total_pairs > 0:
            agreement_ratio = agreements / total_pairs
            p_i.append(agreement_ratio)
            if idx < 5:  # Log first few for debugging
                logging.debug(f"DEBUG: Criterion {idx} ratings {criterion_ratings} -> agreement: {agreements}/{total_pairs} = {agreement_ratio:.3f}")
        else:
            p_i.append(0.0)
    
    # Overall observed agreement
    P_observed = sum(p_i) / n_criteria if n_criteria > 0 else 0.0
    logging.info(f"DEBUG: Overall observed agreement: {P_observed:.3f}")
    
    # Calculate expected agreement by chance
    # Count overall proportions of each category (present/absent)
    total_present = sum(sum(criterion) for criterion in trait_matrix)
    total_ratings = n_criteria * n_reviewers
    
    logging.info(f"DEBUG: Total present: {total_present}, Total ratings: {total_ratings}")
    
    if total_ratings == 0:
        logging.error("DEBUG: Total ratings is 0")
        return 0.0
    
    p_present = total_present / total_ratings
    p_absent = 1 - p_present
    
    logging.info(f"DEBUG: p_present: {p_present:.3f}, p_absent: {p_absent:.3f}")
    
    # Expected agreement by chance
    P_expected = p_present ** 2 + p_absent ** 2
    logging.info(f"DEBUG: Expected agreement by chance: {P_expected:.3f}")
    
    # Fleiss' Kappa
    if P_expected == 1.0:
        result = 1.0 if P_observed == 1.0 else 0.0
        logging.info(f"DEBUG: P_expected = 1.0, returning: {result}")
        return result
    
    fleiss_kappa = (P_observed - P_expected) / (1 - P_expected)
    logging.info(f"DEBUG: Final Fleiss' kappa: ({P_observed:.3f} - {P_expected:.3f}) / (1 - {P_expected:.3f}) = {fleiss_kappa:.3f}")
    return fleiss_kappa

def calculate_fleiss_kappa_for_traits(decomposed_data: Dict[str, Dict], reviewers: List[str], trial_ids: Set[str]) -> float:
    """
    Calculate Fleiss' Kappa for trait agreement across all reviewers and criteria.
    
    Args:
        decomposed_data: Dictionary of reviewer data
        reviewers: List of reviewer names
        trial_ids: Set of trial IDs to analyze
    
    Returns:
        Fleiss' kappa coefficient for overall trait agreement
    """
    logging.info(f"DEBUG: Starting Fleiss' kappa calculation with {len(reviewers)} reviewers: {reviewers}")
    logging.info(f"DEBUG: Trial IDs to analyze: {trial_ids}")
    
    if len(reviewers) < 3:
        logging.info(f"DEBUG: Insufficient reviewers for Fleiss' kappa: {len(reviewers)} < 3")
        return 0.0
    
    # DEBUG: Validate data structure
    for reviewer in reviewers:
        if reviewer not in decomposed_data:
            logging.error(f"DEBUG: Reviewer {reviewer} not found in decomposed_data")
            return 0.0
        logging.info(f"DEBUG: Reviewer {reviewer} has trials: {list(decomposed_data[reviewer].keys())}")
    
    # Build trait matrix: rows = unique traits across all criteria, columns = reviewers
    all_traits = set()
    trait_presence = {}  # (trial_id, criterion_text, trait_key) -> {reviewer: bool}
    
    # First pass: collect all unique traits
    total_traits_found = 0
    for reviewer in reviewers:
        reviewer_data = decomposed_data[reviewer]
        reviewer_traits = 0
        for trial_id in trial_ids:
            if trial_id not in reviewer_data:
                logging.warning(f"DEBUG: Trial {trial_id} not found in {reviewer} data")
                continue
            
            criteria = reviewer_data[trial_id]['criteria']
            logging.info(f"DEBUG: {reviewer} has {len(criteria)} criteria for trial {trial_id}")
            
            for criterion in criteria:
                criterion_key = (trial_id, criterion['original_text'])
                
                for trait in criterion['traits']:
                    trait_key = (trait['trait'].lower().strip(),
                               trait['category'].lower().strip(),
                               trait['value'].lower().strip())
                    all_traits.add(trait_key)
                    reviewer_traits += 1
                    total_traits_found += 1
                    
                    # Initialize presence tracking
                    presence_key = (criterion_key, trait_key)
                    if presence_key not in trait_presence:
                        trait_presence[presence_key] = {r: False for r in reviewers}
                    
                    trait_presence[presence_key][reviewer] = True
        
        logging.info(f"DEBUG: {reviewer} contributed {reviewer_traits} traits")
    
    logging.info(f"DEBUG: Total unique traits found: {len(all_traits)}")
    logging.info(f"DEBUG: Total trait instances: {total_traits_found}")
    logging.info(f"DEBUG: Trait presence combinations: {len(trait_presence)}")
    
    if len(trait_presence) == 0:
        logging.error("DEBUG: No trait presence data found - cannot calculate Fleiss' kappa")
        return 0.0
    
    # Build matrix for Fleiss' Kappa calculation
    trait_matrix = []
    for presence_key, reviewer_presence in trait_presence.items():
        row = [1 if reviewer_presence[reviewer] else 0 for reviewer in reviewers]
        trait_matrix.append(row)
        logging.debug(f"DEBUG: Matrix row for {presence_key[1][:50]}...: {row}")
    
    logging.info(f"DEBUG: Built trait matrix with {len(trait_matrix)} rows and {len(reviewers)} columns")
    
    if len(trait_matrix) == 0:
        logging.error("DEBUG: Empty trait matrix - cannot calculate Fleiss' kappa")
        return 0.0
    
    fleiss_result = calculate_fleiss_kappa(trait_matrix)
    logging.info(f"DEBUG: Fleiss' kappa calculation result: {fleiss_result}")
    return fleiss_result

def classify_discrepancy(trait1: Dict[str, str], trait2: Dict[str, str], is_missing: bool = False) -> Tuple[str, str]:
    """Classify the type of discrepancy and provide explanation."""
    if is_missing:
        return "missing_in_reviewer_2", "Trait identified by one reviewer but not the other"
    
    t1_name, t1_cat, t1_val = normalize_trait(trait1)
    t2_name, t2_cat, t2_val = normalize_trait(trait2)
    
    name_sim = difflib.SequenceMatcher(None, t1_name, t2_name).ratio()
    
    if name_sim > 0.8:  # Similar trait names
        if t1_cat != t2_cat:
            return "category_mismatch", "Same trait but categorized differently"
        elif t1_val != t2_val:
            return "value_mismatch", "Same trait and category but different values"
        else:
            return "granularity_mismatch", "Minor differences in trait specification"
    else:
        return "granularity_mismatch", "Different levels of granularity in trait extraction"


def analyze_agreement_with_llm(decomposed_data: Dict[str, Dict], llm, prompt_template: str) -> AgreementAnalysisResult:
    """Perform agreement analysis using LLM."""
    logging.info("Performing LLM-based agreement analysis")
    
    # DEBUG: Log Pydantic model schema for OpenAI validation
    try:
        schema = AgreementAnalysisResult.model_json_schema()
        logging.info(f"DEBUG: AgreementAnalysisResult schema keys: {list(schema.keys())}")
        if 'properties' in schema:
            logging.info(f"DEBUG: Schema properties: {list(schema['properties'].keys())}")
        if 'required' in schema:
            logging.info(f"DEBUG: Schema required fields: {schema['required']}")
        else:
            logging.error("DEBUG: Schema missing 'required' field - this may cause OpenAI API error")
        
        # Check nested schema structures
        if 'properties' in schema and 'agreement_summary' in schema['properties']:
            summary_schema = schema['properties']['agreement_summary']
            logging.info(f"DEBUG: agreement_summary schema type: {summary_schema.get('type')}")
            if 'properties' in summary_schema:
                logging.info(f"DEBUG: agreement_summary properties: {list(summary_schema['properties'].keys())}")
        
        # Check trials schema
        if 'properties' in schema and 'trials' in schema['properties']:
            trials_schema = schema['properties']['trials']
            logging.info(f"DEBUG: trials schema type: {trials_schema.get('type')}")
            if 'items' in trials_schema and 'properties' in trials_schema['items']:
                trial_props = trials_schema['items']['properties']
                logging.info(f"DEBUG: trial item properties: {list(trial_props.keys())}")
                    
    except Exception as e:
        logging.error(f"DEBUG: Error generating schema: {e}")
    
    # Log data size for debugging
    total_trials = 0
    total_criteria = 0
    for reviewer, data in decomposed_data.items():
        reviewer_trials = len(data)
        reviewer_criteria = sum(len(trial_data.get('criteria', [])) for trial_data in data.values())
        total_trials += reviewer_trials
        total_criteria += reviewer_criteria
        logging.info(f"TOKEN DEBUG: Reviewer {reviewer} has {reviewer_trials} trials, {reviewer_criteria} criteria")
    
    logging.info(f"TOKEN DEBUG: Total input data: {total_trials} trial instances, {total_criteria} criteria instances")
    
    # Prepare input data for LLM
    input_data = {
        "decomposed_files": decomposed_data,
        "reviewers": list(decomposed_data.keys())
    }
    
    # Log specific trials being processed
    all_trial_ids = set()
    for reviewer_data in decomposed_data.values():
        all_trial_ids.update(reviewer_data.keys())
    logging.info(f"TOKEN DEBUG: Processing trials: {sorted(all_trial_ids)}")
    
    # Create the prompt using service
    human_template = "Analyze the agreement between reviewers for the following decomposed criteria:\n\n{input_data}"
    prompt = PromptService.create_chat_prompt_template(
        prompt_template,
        human_template,
        escape_braces=True,
        template_variables=['input_data']
    )
    
    # Create and invoke the chain using service
    chain = ChainService.create_chain(prompt, llm)
    
    try:
        result, duration = ChainService.invoke_chain(chain, {"input_data": json.dumps(input_data, indent=2)})
        logging.info("DEBUG: LLM chain invocation successful")
    except Exception as e:
        # Log the raw LLM output for debugging if it's a validation error
        if "validation error" in str(e).lower():
            logging.error("VALIDATION ERROR DEBUG: LLM generated invalid output")
            logging.error(f"Full error details: {e}")
            
            error_str = str(e)
            if "input_value=" in error_str:
                # Extract the input_value part for debugging
                import re
                input_value_match = re.search(r"input_value=({.*?})", error_str, re.DOTALL)
                if input_value_match:
                    raw_output = input_value_match.group(1)
                    logging.error(f"RAW LLM OUTPUT SAMPLE: {raw_output[:500]}...")
            
            missing_fields = []
            if "reviewer_trait_counts" in error_str:
                missing_fields.append("reviewer_trait_counts")
                logging.error("MISSING FIELD: reviewer_trait_counts - LLM did not generate this required field")
            if "reviewer_extractions" in error_str:
                missing_fields.append("reviewer_extractions")
                logging.error("MISSING FIELD: reviewer_extractions - LLM did not generate this required field")
            if "analysis_metadata" in error_str:
                missing_fields.append("analysis_metadata")
                logging.error("MISSING FIELD: analysis_metadata - LLM did not generate this required field")
            if "semantic_normalization_log" in error_str:
                missing_fields.append("semantic_normalization_log")
                logging.error("MISSING FIELD: semantic_normalization_log - LLM did not generate this required field")
            
            if missing_fields:
                logging.error(f"DIAGNOSIS: These fields should be made optional or have defaults: {missing_fields}")
                logging.error("SOLUTION: Modify AgreementAnalysisResult schema to make these fields optional")
        # Enhanced error logging for token limit issues
        error_msg = str(e).lower()
        if "length limit" in error_msg or "token" in error_msg or "completion_tokens" in error_msg:
            logging.error(f"TOKEN LIMIT ERROR in agreement analysis for trials: {sorted(all_trial_ids)}")
            logging.error(f"ERROR DETAILS: {e}")
            
            # Log the specific trial mentioned in the original error
            if "NCT03191786" in str(input_data):
                logging.error("TOKEN DEBUG: NCT03191786 is present in the input data - this trial may have unusually large criteria")
            
            # Suggest specific solutions
            logging.error("SUGGESTED SOLUTIONS:")
            logging.error("1. Increase max_tokens in API configuration (current default: 8192)")
            logging.error("2. Process trials individually instead of in batch")
            logging.error("3. Reduce prompt verbosity or split complex analysis")
        
        # Re-raise the exception to maintain original behavior
        raise
    
    return result


def format_metric(value: float, precision: int = 3) -> str:
    """Format a metric value for display."""
    return f"{value:.{precision}f}"

def get_quality_assessment(f1_score: float, kappa: float) -> str:
    """Assess agreement quality based on metrics."""
    if f1_score > 0.9 and kappa > 0.8:
        return "🟢 Excellent"
    elif f1_score > 0.8 and kappa > 0.6:
        return "🟡 Good"
    elif f1_score > 0.6 and kappa > 0.4:
        return "🟠 Moderate"
    else:
        return "🔴 Poor"

def generate_markdown_report(result: AgreementAnalysisResult, output_path: str, analysis_type: str, reviewer_count: int, model_name: str = None):
    """Generate a comprehensive markdown report based on the analysis results using a template."""
    
    # Create markdown filename
    base_path = Path(output_path)
    if base_path.suffix == '.json':
        md_path = base_path.with_suffix('.md')
    else:
        md_path = base_path.parent / f"{base_path.stem}_report.md"
    

    template_filename = "agreement_analysis_n_reviewer_report.md"
    
    template_path = Path(__file__).parent / "report_templates" / template_filename
    
    # Calculate additional metrics for n-reviewer template
    pairwise_count = reviewer_count * (reviewer_count - 1) // 2  # n choose 2
    
    logging.info(f"Using template: {template_filename} for {reviewer_count} reviewers")
    
    try:
        with open(template_path, 'r') as f:
            template_content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Report template not found at {template_path}")
    
    # Prepare template variables
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    summary = result.agreement_summary
    
    # Calculate metrics from new schema structure
    total_criteria = summary.overall.total_criteria
    total_traits = summary.overall.total_traits
    
    # Count perfect agreement criteria (simplified calculation)
    perfect_agreement_criteria = summary.overall.agreement_distribution.perfect_agreement
    exact_match_ratio = perfect_agreement_criteria / total_criteria if total_criteria > 0 else 0
    
    # Calculate overall agreement ratio based on distribution
    total_items = (summary.overall.agreement_distribution.perfect_agreement +
                  summary.overall.agreement_distribution.majority_agreement +
                  summary.overall.agreement_distribution.no_agreement)
    overall_agreement_ratio = (summary.overall.agreement_distribution.perfect_agreement +
                             summary.overall.agreement_distribution.majority_agreement) / total_items if total_items > 0 else 0
    
    # Count discrepancies from trials
    total_discrepancies = 0
    for trial in result.trials:
        for criterion in trial.criteria:
            for trait in criterion.traits:
                # Count missing extractions as discrepancies
                if trait.reviewer_extractions:
                    missing_count = sum(1 for extraction in trait.reviewer_extractions.values()
                                      if extraction.match_status == MatchStatus.MISSING)
                    total_discrepancies += missing_count
    
    # Build template variables for new schema
    template_vars = {
        'timestamp': timestamp,
        'analysis_type': analysis_type,
        'total_criteria': total_criteria,
        'exact_match_criteria_count': perfect_agreement_criteria,
        'exact_match_ratio': format_metric(exact_match_ratio),
        'overall_agreement_ratio': format_metric(overall_agreement_ratio),
        'total_discrepancies': total_discrepancies,
        'total_traits_compared': total_traits,
        'total_traits_agreed': summary.overall.agreement_distribution.perfect_agreement,
        'reviewer_count': reviewer_count,
        'pairwise_count': pairwise_count,
        'fleiss_kappa': format_metric(result.quality_metrics.trait_extraction_consistency),  # Use consistency as proxy
    }
    
    # Model section
    if model_name:
        template_vars['model_section'] = f"**Model Used:** {model_name}\n"
        template_vars['model_technical_section'] = f"- **LLM Model:** {model_name}\n"
    else:
        template_vars['model_section'] = ""
        template_vars['model_technical_section'] = ""
    
    # Quality assessment section - use quality metrics from new schema
    avg_consistency = result.quality_metrics.trait_extraction_consistency
    # Estimate F1 based on agreement ratio for quality assessment
    estimated_f1 = overall_agreement_ratio
    quality = get_quality_assessment(estimated_f1, avg_consistency)
    
    template_vars['quality_assessment_section'] = f"""### Overall Quality Assessment
**{quality}** (Trait Extraction Consistency: {format_metric(avg_consistency)})

"""
    
    # Pairwise metrics table - for new schema, show trial-level agreement
    table_lines = ["| Trial ID | Total Criteria | Perfect Agreement | Majority Agreement | No Agreement | Agreement Rate |",
                  "|----------|-----------------|-------------------|-------------------|--------------|----------------|"]
    
    # Add trial-level metrics
    for trial in result.trials:
        perfect = trial.agreement_distribution.perfect_agreement
        majority = trial.agreement_distribution.majority_agreement
        no_agreement = trial.agreement_distribution.no_agreement
        total = perfect + majority + no_agreement
        agreement_rate = (perfect + majority) / total if total > 0 else 0
        
        table_lines.append(f"| {trial.trial_id} | {trial.total_criteria} | {perfect} | {majority} | {no_agreement} | {format_metric(agreement_rate)} |")
    
    template_vars['pairwise_metrics_table'] = "\n".join(table_lines) + "\n"
    
    # Discrepancy analysis section - build from new schema structure
    template_vars['discrepancy_analysis_section'] = _build_discrepancy_section_new(result.trials)
    
    # Recommendations section
    template_vars['recommendations_section'] = _build_recommendations_section(overall_agreement_ratio)
    
    # Additional sections for n-reviewer template
    is_n_reviewer = reviewer_count > 2  # More than 2 reviewers = n reviewers (n > 2)
    if is_n_reviewer:
        template_vars['reviewer_overview_section'] = _build_reviewer_overview_section_new(result.trials, reviewer_count)
        template_vars['agreement_distribution_section'] = _build_agreement_distribution_section_new(result.agreement_summary.overall.agreement_distribution)
        template_vars['multi_reviewer_recommendations_section'] = _build_multi_reviewer_recommendations_section_new(result.quality_metrics, reviewer_count)
    else:
        # Set empty values for 2-reviewer template compatibility
        template_vars['reviewer_overview_section'] = ""
        template_vars['agreement_distribution_section'] = ""
        template_vars['multi_reviewer_recommendations_section'] = ""
    
    # Replace template variables
    report_content = template_content.format(**template_vars)
    
    # Write the report
    with open(md_path, 'w') as f:
        f.write(report_content)
    
    logging.info(f"Markdown report saved to: {md_path}")
    return str(md_path)


def _build_recommendations_section(overall_agreement: float) -> str:
    """Build the recommendations section content based on agreement level."""
    if overall_agreement > 0.8:
        return """### ✅ High Agreement Detected

The decomposition process shows strong consistency across reviewers:

- Results are suitable for downstream applications like patient matching
- Consider this as a baseline for future analyses
- The current decomposition guidelines appear effective
"""
    elif overall_agreement > 0.6:
        return """### ⚠️ Moderate Agreement Detected

The decomposition process shows reasonable consistency but has room for improvement:

- Review discrepancies to identify improvement areas
- Consider refining decomposition guidelines
- May need expert review for complex criteria
- Focus on reducing the most common discrepancy types
"""
    else:
        return """### 🔴 Low Agreement Detected

Significant inconsistencies found in the decomposition process:

- **Immediate action required** to improve consistency
- Review and standardize the decomposition process
- Consider additional training or clearer guidelines
- Implement quality control measures
- May need expert oversight for complex cases
"""




    """Build the agreement distribution section for n-reviewer analysis."""
    if not pairwise_metrics:
        return "No agreement data available.\n"
    
    # Categorize traits by Fleiss' kappa quality levels
    excellent = sum(1 for t in pairwise_metrics if t.fleiss_kappa >= 0.8)
    good = sum(1 for t in pairwise_metrics if 0.6 <= t.fleiss_kappa < 0.8)
    moderate = sum(1 for t in pairwise_metrics if 0.4 <= t.fleiss_kappa < 0.6)
    poor = sum(1 for t in pairwise_metrics if t.fleiss_kappa < 0.4)
    
    total = len(pairwise_metrics)
    
    content = []
    content.append("| Quality Level | Count | Percentage |")
    content.append("|---------------|-------|------------|")
    content.append(f"| 🟢 Excellent | {excellent} | {(excellent/total)*100:.1f}% |")
    content.append(f"| � Good | {good} | {(good/total)*100:.1f}% |")
    content.append(f"| 🟠 Moderate | {moderate} | {(moderate/total)*100:.1f}% |")
    content.append(f"| 🔴 Poor | {poor} | {(poor/total)*100:.1f}% |")
    content.append("")
    
    # Add interpretation
    if excellent / total > 0.7:
        content.append("**Interpretation:** Most traits show excellent agreement, indicating strong consistency.")
    elif (excellent + good) / total > 0.7:
        content.append("**Interpretation:** Most traits show good to excellent agreement, indicating reasonable consistency.")
    elif poor / total > 0.5:
        content.append("**Interpretation:** Many traits show poor agreement, indicating significant inconsistencies.")
    else:
        content.append("**Interpretation:** Mixed agreement levels across traits, suggesting variable consistency.")
    
    content.append("")
    return "\n".join(content)


    


def _build_discrepancy_section_new(trials: List[TrialAnalysis]) -> str:
    """Build the discrepancy analysis section content from new schema."""
    total_discrepancies = 0
    discrepancy_counts = {}
    
    # Count discrepancies from trials
    for trial in trials:
        for criterion in trial.criteria:
            for trait in criterion.traits:
                if trait.reviewer_extractions:
                    for reviewer_id, extraction in trait.reviewer_extractions.items():
                        if extraction.match_status != MatchStatus.EXACT_MATCH:
                            total_discrepancies += 1
                        match_status = extraction.match_status.value
                        discrepancy_counts[match_status] = discrepancy_counts.get(match_status, 0) + 1
    
    if total_discrepancies == 0:
        return "✅ **No discrepancies found** - Perfect agreement between all reviewers!\n"
    
    content = []
    
    content.append("### Discrepancy Types\n")
    content.append("| Discrepancy Type | Count | Percentage |")
    content.append("|------------------|-------|------------|")
    
    for disc_type, count in sorted(discrepancy_counts.items()):
        percentage = (count / total_discrepancies) * 100
        content.append(f"| {disc_type.replace('_', ' ').title()} | {count} | {percentage:.1f}% |")
    content.append("")
    
    # Show examples
    content.append("### Example Discrepancies\n")
    
    shown = 0
    max_examples = 6
    
    for trial in trials:
        if shown >= max_examples:
            break
        for criterion in trial.criteria:
            if shown >= max_examples:
                break
            for trait in criterion.traits:
                if shown >= max_examples:
                    break
                
                # Find discrepancies in this trait
                discrepant_reviewers = []
                if trait.reviewer_extractions:
                    for reviewer_id, extraction in trait.reviewer_extractions.items():
                        if extraction.match_status != MatchStatus.EXACT_MATCH:
                            discrepant_reviewers.append((reviewer_id, extraction))
                
                if discrepant_reviewers and shown < max_examples:
                    content.append(f"**Trial:** {trial.trial_id}\n")
                    content.append(f"**Criterion:** {criterion.original_text[:150]}...\n")
                    content.append(f"**Consensus Trait:** {trait.consensus_trait_signature}\n")
                    
                    # Show reviewer extractions
                    content.append("**Reviewer Extractions:**\n")
                    if trait.reviewer_extractions:
                        for reviewer_id, extraction in trait.reviewer_extractions.items():
                            if extraction.match_status == MatchStatus.MISSING:
                                content.append(f"  - {reviewer_id}: Missing\n")
                            else:
                                content.append(f"  - {reviewer_id}: {extraction.trait}|{extraction.category}|{extraction.value} ({extraction.match_status.value})\n")
                    
                    if discrepant_reviewers[0][1].discrepancies:
                        content.append(f"**Explanation:** {discrepant_reviewers[0][1].discrepancies}\n")
                    content.append("---\n")
                    
                    shown += 1
    
    return "\n".join(content)


def _build_reviewer_overview_section_new(trials: List[TrialAnalysis], reviewer_count: int) -> str:
    """Build the reviewer overview section for n-reviewer analysis from new schema."""
    if not trials:
        return "No reviewer data available.\n"
    
    # Extract reviewer performance from trials
    reviewer_stats = {}
    
    # Initialize stats for all reviewers
    all_reviewers = set()
    for trial in trials:
        for criterion in trial.criteria:
            for trait in criterion.traits:
                if trait.reviewer_extractions:
                    all_reviewers.update(trait.reviewer_extractions.keys())
    
    for reviewer in all_reviewers:
        reviewer_stats[reviewer] = {'agreements': 0, 'total': 0, 'exact_matches': 0}
    
    # Count agreements per reviewer
    for trial in trials:
        for criterion in trial.criteria:
            for trait in criterion.traits:
                if trait.reviewer_extractions:
                    for reviewer_id, extraction in trait.reviewer_extractions.items():
                        reviewer_stats[reviewer_id]['total'] += 1
                        if extraction.match_status == MatchStatus.EXACT_MATCH:
                            reviewer_stats[reviewer_id]['exact_matches'] += 1
                            reviewer_stats[reviewer_id]['agreements'] += 1
                        elif extraction.match_status in [MatchStatus.SYNONYM_VARIATION, MatchStatus.VALUE_MISMATCH]:
                            reviewer_stats[reviewer_id]['agreements'] += 0.7  # Partial credit
    
    content = []
    content.append("| Reviewer | Agreement Rate | Exact Match Rate | Total Traits | Quality |")
    content.append("|----------|----------------|------------------|--------------|---------|")
    
    for reviewer_id, stats in sorted(reviewer_stats.items()):
        if stats['total'] > 0:
            agreement_rate = stats['agreements'] / stats['total']
            exact_match_rate = stats['exact_matches'] / stats['total']
            quality = get_quality_assessment(agreement_rate, exact_match_rate)
            
            content.append(f"| {reviewer_id} | {format_metric(agreement_rate)} | {format_metric(exact_match_rate)} | {stats['total']} | {quality} |")
    
    content.append("")
    return "\n".join(content)


def _build_agreement_distribution_section_new(agreement_dist: AgreementDistribution) -> str:
    """Build the agreement distribution section for n-reviewer analysis from new schema."""
    total = agreement_dist.perfect_agreement + agreement_dist.majority_agreement + agreement_dist.no_agreement
    
    if total == 0:
        return "No agreement data available.\n"
    
    content = []
    content.append("| Quality Level | Count | Percentage |")
    content.append("|---------------|-------|------------|")
    content.append(f"| 🟢 Perfect Agreement | {agreement_dist.perfect_agreement} | {(agreement_dist.perfect_agreement/total)*100:.1f}% |")
    content.append(f"| 🟡 Majority Agreement | {agreement_dist.majority_agreement} | {(agreement_dist.majority_agreement/total)*100:.1f}% |")
    content.append(f"| 🔴 No Agreement | {agreement_dist.no_agreement} | {(agreement_dist.no_agreement/total)*100:.1f}% |")
    content.append("")
    
    # Add interpretation
    perfect_ratio = agreement_dist.perfect_agreement / total
    majority_ratio = agreement_dist.majority_agreement / total
    no_agreement_ratio = agreement_dist.no_agreement / total
    
    if perfect_ratio > 0.7:
        content.append("**Interpretation:** Most items show perfect agreement, indicating strong consistency.")
    elif (perfect_ratio + majority_ratio) > 0.7:
        content.append("**Interpretation:** Most items show good to perfect agreement, indicating reasonable consistency.")
    elif no_agreement_ratio > 0.5:
        content.append("**Interpretation:** Many items show no agreement, indicating significant inconsistencies.")
    else:
        content.append("**Interpretation:** Mixed agreement levels, suggesting variable consistency.")
    
    content.append("")
    return "\n".join(content)


def _build_multi_reviewer_recommendations_section_new(quality_metrics: QualityMetrics, reviewer_count: int) -> str:
    """Build multi-reviewer specific recommendations from new schema."""
    content = []
    
    avg_consistency = (quality_metrics.trait_extraction_consistency +
                      quality_metrics.category_assignment_consistency +
                      quality_metrics.value_specification_consistency +
                      quality_metrics.granularity_consistency) / 4
    
    if reviewer_count > 3:
        content.append("#### Large Reviewer Group (>3 reviewers)")
        content.append("- **Consensus Mechanism:** Consider implementing majority voting for trait extraction")
        content.append("- **Quality Control:** Use inter-reviewer agreement as a quality filter")
        content.append("- **Outlier Detection:** Identify and investigate reviewers with consistently low agreement")
        content.append("")
    
    if avg_consistency < 0.6:
        content.append("#### Low Consistency Detected")
        content.append("- **Training:** Provide additional training on decomposition guidelines")
        content.append("- **Calibration:** Conduct calibration sessions with example cases")
        content.append("- **Guidelines:** Refine and clarify decomposition criteria")
        content.append("")
    
    if quality_metrics.trait_extraction_consistency < 0.7:
        content.append("#### Trait Extraction Issues")
        content.append("- **Standardization:** Develop clearer trait identification guidelines")
        content.append("- **Examples:** Provide more examples of proper trait extraction")
        content.append("")
    
    if quality_metrics.category_assignment_consistency < 0.7:
        content.append("#### Category Assignment Issues")
        content.append("- **Taxonomy:** Refine the category taxonomy")
        content.append("- **Training:** Focus on category assignment training")
        content.append("")
    
    if avg_consistency > 0.8:
        content.append("#### Strong Consistency Foundation")
        content.append("- **Scale Up:** Current process is suitable for larger datasets")
        content.append("- **Automation:** Consider semi-automated approaches with human oversight")
        content.append("- **Benchmarking:** Use current results as quality benchmarks")
        content.append("")
    
    content.append("#### General Multi-Reviewer Best Practices")
    content.append("- **Blind Review:** Ensure reviewers work independently")
    content.append("- **Regular Calibration:** Conduct periodic agreement checks")
    content.append("- **Feedback Loop:** Share agreement results with reviewers for improvement")
    content.append("- **Documentation:** Maintain detailed logs of disagreement patterns")
    
    return "\n".join(content)


def main():
    """Main function to analyze agreement between decomposed criteria."""
    parser = argparse.ArgumentParser(description="Analyze agreement between decomposed clinical trial criteria.")
    parser.add_argument('--input-dir', required=True, help="Directory containing decomposed criteria JSON files.")
    parser.add_argument('--output', required=True, help="Output file path for agreement analysis results.")
    parser.add_argument('--prompt', required=True, help="Path to the agreement analysis prompt markdown file.")
    parser.add_argument('--api-keys', required=True, help="Path to the JSON file with API keys.")
    parser.add_argument('--model', choices=['openai', 'gemini', 'claude'], required=True, help="Language model provider to use.")
    parser.add_argument('--model-name', help="Specific model name to use.")
    parser.add_argument('--no-cache', dest='cache', action='store_false', help="Disable prompt caching.")
    parser.set_defaults(cache=True)
    args = parser.parse_args()

    try:
        logging.info("Starting criteria agreement analysis process.")
        
        # Load decomposed files
        decomposed_data = load_decomposed_files(args.input_dir)
        logging.info(f"Loaded data from {len(decomposed_data)} reviewers: {list(decomposed_data.keys())}")
        
        # Load prompt template using service
        prompt_template = PromptService.load_prompt_template(args.prompt)
        
        # Load API keys using service
        api_keys = APIKeyService.load_api_keys(args.api_keys)
        
        # Add model override if specified
        if args.model_name:
            api_keys = APIKeyService.add_model_override(api_keys, args.model, args.model_name)
        
        # Set up caching using service
        CacheService.setup_cache(args.cache)
        
        # Get the language model using service
        llm, explicit_model_name = LLMService.get_llm(args.model, api_keys, AgreementAnalysisResult)
        
        # Perform analysis
        result = analyze_agreement_with_llm(decomposed_data, llm, prompt_template)
        analysis_type = f"LLM Analysis ({args.model})"
        model_name = explicit_model_name if 'explicit_model_name' in locals() else args.model
        reviewer_count = len(decomposed_data)
        
        # Generate output filename if directory provided
        if os.path.isdir(args.output):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # DEBUG: Add type checking for filename construction
            logging.info(f"DEBUG: Building agreement filename with types - args.model: {type(args.model)} = '{args.model}'")
            logging.info(f"DEBUG: timestamp: {type(timestamp)} = '{timestamp}'")
            
            # Ensure all components are strings
            model_str = str(args.model)
            timestamp_str = str(timestamp)
            
            filename = f"agreement_analysis_{model_str}_{timestamp_str}.json"
            output_path = os.path.join(args.output, filename)
            logging.info(f"DEBUG: Successfully constructed agreement filename: {filename}")
        else:
            output_path = args.output
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write the output
        logging.info(f"Writing agreement analysis results to {output_path}")
        with open(output_path, 'w') as f:
            json.dump(result.model_dump(), f, indent=2)
        
        # Generate markdown report
        markdown_path = generate_markdown_report(result, output_path, analysis_type, reviewer_count, model_name)
        
        # Log summary statistics
        summary = result.agreement_summary
        logging.info(f"Agreement Analysis Complete:")
        logging.info(f"  - Total criteria analyzed: {summary.overall.total_criteria}")
        logging.info(f"  - Total traits analyzed: {summary.overall.total_traits}")
        logging.info(f"  - Total reviewers: {summary.overall.total_reviewers}")
        logging.info(f"  - Perfect agreement items: {summary.overall.agreement_distribution.perfect_agreement}")
        logging.info(f"  - Majority agreement items: {summary.overall.agreement_distribution.majority_agreement}")
        logging.info(f"  - No agreement items: {summary.overall.agreement_distribution.no_agreement}")
        logging.info(f"  - Trait extraction consistency: {result.quality_metrics.trait_extraction_consistency:.3f}")
        logging.info(f"  - Category assignment consistency: {result.quality_metrics.category_assignment_consistency:.3f}")
        logging.info(f"  - Value specification consistency: {result.quality_metrics.value_specification_consistency:.3f}")
        logging.info(f"  - Granularity consistency: {result.quality_metrics.granularity_consistency:.3f}")
        
        # Count total discrepancies
        total_discrepancies = 0
        for trial in result.trials:
            for criterion in trial.criteria:
                for trait in criterion.traits:
                    if trait.reviewer_extractions:
                        missing_count = sum(1 for extraction in trait.reviewer_extractions.values()
                                          if extraction.match_status == MatchStatus.MISSING)
                        total_discrepancies += missing_count
        logging.info(f"  - Total discrepancies: {total_discrepancies}")
        
        logging.info(f"Successfully completed agreement analysis and saved to {output_path}")
        logging.info(f"Markdown report generated: {markdown_path}")

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)

if __name__ == '__main__':
    main()
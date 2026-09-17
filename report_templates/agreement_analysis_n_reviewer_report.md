# Clinical Trial Criteria Agreement Analysis Report (N-Reviewer)

**Generated:** {timestamp}
**Analysis Type:** {analysis_type}
**Number of Reviewers:** {reviewer_count}
{model_section}

---

## 🎯 Executive Summary

### Key Metrics
- **Total Criteria Analyzed:** {total_criteria}
- **Perfect Agreement Items:** {exact_match_criteria_count}
- **Perfect Agreement Ratio:** {exact_match_ratio}
- **Overall Agreement Ratio:** {overall_agreement_ratio}
- **Total Discrepancies:** {total_discrepancies}
- **Reviewer Combinations:** {pairwise_count}
- **Trait Extraction Consistency:** {fleiss_kappa}

{quality_assessment_section}

### Reviewer Overview
{reviewer_overview_section}

## 📊 Trial-Level Agreement Metrics

The following table shows agreement metrics for each trial:

{pairwise_metrics_table}

### Agreement Distribution
{agreement_distribution_section}

## 🔍 Discrepancy Analysis

{discrepancy_analysis_section}

## 📈 Interpretation Guide

### Agreement Metrics Explained

- **Perfect Agreement:** All reviewers extracted identical traits
- **Majority Agreement:** Most reviewers agreed on trait extraction
- **No Agreement:** Reviewers had significant disagreements
- **Trait Extraction Consistency:** Overall consistency in identifying traits (0.0-1.0, higher is better)
- **Category Assignment Consistency:** Consistency in categorizing traits (0.0-1.0, higher is better)
- **Value Specification Consistency:** Consistency in specifying trait values (0.0-1.0, higher is better)
- **Granularity Consistency:** Consistency in level of detail (0.0-1.0, higher is better)

### Quality Thresholds

- 🟢 **Excellent Agreement:** Agreement ratio > 0.9, Consistency > 0.8
- 🟡 **Good Agreement:** Agreement ratio > 0.8, Consistency > 0.6
- 🟠 **Moderate Agreement:** Agreement ratio > 0.6, Consistency > 0.4
- 🔴 **Poor Agreement:** Agreement ratio < 0.6, Consistency < 0.4

### Discrepancy Types

- **missing:** Trait identified by some reviewers but not others
- **category_mismatch:** Same trait but categorized differently
- **value_mismatch:** Same trait and category but different values
- **granularity_mismatch:** Different levels of detail in trait extraction
- **synonym_variation:** Different terms for the same concept

### Multi-Reviewer Considerations

When analyzing agreement across multiple reviewers:
- **Consensus Building:** Look for patterns across all reviewers
- **Semantic Normalization:** Account for synonym variations and abbreviations
- **Outlier Detection:** Identify reviewers with consistently different results
- **Quality Control:** Use majority agreement as a quality indicator

## 💡 Recommendations

{recommendations_section}

### Multi-Reviewer Specific Recommendations

{multi_reviewer_recommendations_section}

## 🚀 Next Steps

1. **Review Detailed Results:** Examine the discrepancy analysis to understand patterns
2. **Identify Reviewer Patterns:** Look for systematic differences between specific reviewers
3. **Consensus Analysis:** Consider implementing majority voting or consensus mechanisms
4. **Semantic Standardization:** Improve normalization of medical terminology
5. **Refine Guidelines:** Update decomposition guidelines based on common discrepancy patterns
6. **Validate Improvements:** Re-run analysis after implementing changes
7. **Scale Analysis:** Apply to additional datasets to confirm improvements

## 🔧 Technical Details

- **Analysis Method:** {analysis_type}
{model_technical_section}
- **Total Reviewers:** {reviewer_count}
- **Reviewer Combinations:** {pairwise_count}
- **Total Traits Compared:** {total_traits_compared}
- **Perfect Agreement Items:** {total_traits_agreed}
- **Analysis Timestamp:** {timestamp}

---

*This report was generated automatically by the Clinical Trial Criteria Agreement Analysis tool for N-reviewer semantic analysis.*
# 🧪 Revised Study Trait Agreement Analysis Prompt (Clinical Trial Criteria Decomposition)

---

## 📝 Task Description

You are provided with outputs from multiple reviewers (n ≥ 2)—human or AI—who have independently decomposed the same set of clinical trial eligibility criteria into structured traits. Your tasks are:

1. **Trait Matching Across Reviewers**: For each criterion in each trial, match traits semantically across reviewers by aligning on trait name, category, and value using semantic normalization, not strict string matching. Each criterion can be decomposed into multiple traits (e.g., "Age 18-65 years, BMI >25, no diabetes" contains three distinct traits), so trait matching must account for all possible trait combinations that reviewers may extract from a single criterion.

2. **Agreement Analysis**: Assess inter-reviewer agreement of each trait across all reviewers. This requires first establishing consensus trait signatures through systematic analysis of all reviewer extractions. If a reviewer did not extract a trait, the "match_status" will be set to "missing". "match_status" refers to the matching status of the current reviewer for this particular trait, comparing to the consensus_trait_signature on a semantic level, NOT exact matching.

**IMPORTANT: 
- Return ONLY the JSON output as specified in the Output JSON Schema. Do not include any additional text, explanations, or markdown formatting in your response.
- Generate ALL fields specified in the schema. Do not skip, omit, or leave any fields empty unless explicitly marked as optional.
- Every field must be populated with appropriate values based on the analysis, even if some fields contain empty arrays or zero values.
- CRITICAL: Ensure reviewer_extractions and reviewer_trait_counts are always generated for every criterion and trait. These fields are essential for the analysis and must include data for all reviewers, even if a reviewer has "missing" match_status.**
---

## 📥 Input Format

Each reviewer provides a nested JSON structure organized by trial:

```json
{
  "NCT12345678": {
    "trial_id": "NCT12345678",
    "criteria": [
      {
        "type": "inclusion" | "exclusion",
        "original_text": "<original criterion text>",
        "logic": "<logical expression>",
        "traits": [
          {
            "trait": "<trait name>",
            "category": "<category>",
            "value": "<value>",
            "source_text": "<extracted portion of original text>",
            "original_trait_phrase": "<phrase describing the trait>",
            "original_value_phrase": "<phrase describing the value>"
          }
        ]
      }
    ]
  }
}
```

### **Key Data Fields**
- **trial_id**: NCT number identifying the clinical trial
- **type**: "inclusion" or "exclusion" criterion
- **original_text**: Full text of the eligibility criterion as written
- **logic**: Logical expression representation (for reference)
- **traits**: Array of extracted traits from this criterion
- **trait**: Name/identifier of the clinical trait
- **category**: Categorical classification of the trait type
- **value**: Specific value, range, or condition for the trait
- **source_text**: Portion of original text that supported this trait extraction
- **original_trait_phrase**: Specific phrase describing the trait
- **original_value_phrase**: Specific phrase describing the value

---

## 📤 Output JSON Schema

```json
{
  "analysis_metadata": {
    "total_trials": <int>,
    "total_criteria": <int>,
    "total_reviewers": <int>,
    "reviewer_identifiers": ["reviewer_1", "reviewer_2", "reviewer_n"],
    "analysis_timestamp": "<ISO timestamp>"
  },
  "agreement_summary": {
    "overall": {
      "total_traits": <int>,
      "total_criteria": <int>,
      "total_reviewers": <int>,
      "agreement_distribution": {
        "perfect_agreement": <int>,
        "majority_agreement": <int>,
        "no_agreement": <int>
      }
    }
  },
  "trials": [
    {
      "trial_id": "<NCT number>",
      "total_criteria": <int>,
      "total_unique_traits": <int>,
      "agreement_distribution": {
        "perfect_agreement": <int>,
        "majority_agreement": <int>,
        "no_agreement": <int>
      },
      "criteria": [
        {
          "criterion_index": <int>,
          "type": "inclusion" | "exclusion",
          "original_text": "<text>",
          "consensus_logic": "<logical expression>",
          "total_unique_traits": <int>,
          "reviewer_trait_counts": {
            "reviewer_1": <int>,
            "reviewer_2": <int>,
            "reviewer_n": <int>
          },
          "trait_overlap_percentage": <float>,
          "traits": [
            {
              "consensus_trait_signature": "<trait>|<category>|<value>",
              "normalized_trait_name": "<standardized name>",
              "normalized_category": "<standardized category>",
              "normalized_value": "<standardized value>",
              "reviewer_extractions": {
                "reviewer_1": {
                  "trait": "<trait name>",
                  "category": "<category>",
                  "value": "<value>",
                  "source_text": "<text>",
                  "original_trait_phrase": "<phrase>",
                  "original_value_phrase": "<phrase>",
                  "match_status": "value_mismatch" | "category_mismatch" | "granularity_mismatch" | "synonym_variation",
                  "discrepancies": "<qualitative explanation>"
                },
                "reviewer_2": {
                  "trait": "<trait name>",
                  "category": "<category>",
                  "value": "<value>",
                  "source_text": "<text>",
                  "original_trait_phrase": "<phrase>",
                  "original_value_phrase": "<phrase>",
                  "match_status": "value_mismatch" | "category_mismatch" | "granularity_mismatch" | "synonym_variation",
                  "discrepancies": "<qualitative explanation>"
                },
                "reviewer_n": {
                  "match_status": "missing"
                }
              }
            }
          ]
        }
      ]
    }
  ],
  "semantic_normalization_log": [
    {
      "original_variations": ["BMI", "Body Mass Index", "body mass index"],
      "normalized_form": "BMI",
      "normalization_rule": "abbreviation_standardization",
      "affected_reviewers": ["reviewer_1", "reviewer_2"]
    }
  ],
  "quality_metrics": {
    "trait_extraction_consistency": <float>,
    "category_assignment_consistency": <float>,
    "value_specification_consistency": <float>,
    "granularity_consistency": <float>
  }
}
```

---

## 🔍 Analysis Guidelines

### **Normalization and Standardization**

#### **Semantic Normalization Steps**
1. **Text Preprocessing**: Lowercase, trim whitespace, remove punctuation
2. **Medical Terminology**: Standardize using clinical vocabularies (e.g., SNOMED CT, MeSH)
3. **Unit Standardization**: Convert to consistent measurement units
4. **Abbreviation Expansion**: Expand common medical abbreviations consistently
5. **Synonym Recognition**: Use domain-specific synonym dictionaries

#### **Trait Signature Construction**
- **Format**: `trait name | category | value`
- **Consensus Trait Signature**: The normalized, standardized trait signature derived from majority consensus or clinical standard
- **Semantic Equivalence Mapping**: 
  - "ECOG PS" ↔ "ECOG Performance Status" ↔ "Performance Status"
  - "HIV" ↔ "Human Immunodeficiency Virus"
  - "BMI" ↔ "Body Mass Index"

#### **Category Standardization**
Standardize categories to:
- **Demographics** (age, sex, race, ethnicity)
- **Diagnosis/Disease** (primary diagnosis, stage, metastases)
- **Biomarkers/Molecular** (genetic markers, molecular tests)
- **Laboratory** (lab values, test results)
- **Performance Status/Functional Status** (ECOG, Karnofsky, functional assessments)
- **Prior/Concurrent Treatments** (previous therapies, concurrent medications)
- **Comorbidities** (other medical conditions)
- **Medications** (current medications, contraindications)
- **Procedures** (surgical procedures, diagnostic tests)
- **Infection/Immunization** (infectious diseases, vaccines)
- **Reproductive/Pregnancy Status** (pregnancy, contraception)
- **Organ Function** (organ-specific function assessments)
- **Other** (miscellaneous criteria)

#### **Value Standardization**
- **Numerical Ranges**: Standardize format (e.g., "18-65", "≥18", ">65")
- **Boolean Values**: "Yes/No", "Present/Absent", "Positive/Negative"
- **Categorical Values**: Standardize terms (e.g., "Active" vs "Ongoing")

### **Discrepancy Analysis**
Report discrepancy types and provide qualitative explanations:
- **Missing**: Trait not extracted by reviewer
- **Category Mismatch**: Different categorical classification
- **Value Mismatch**: Different value specifications
- **Granularity Mismatch**: Different levels of detail
- **Synonym Variation**: Different terms for same concept

Short qualitative explanations should include:
- Differences in granularity
- Synonym use or abbreviation
- Category interpretation discrepancies
- Omission due to judgment or parsing limitations

### **Complex Logical Relationships**
- Some criteria contain AND/OR logic that may lead to different trait granularities
- Document how reviewers handle conditional relationships
- Consider separate analysis for simple vs. complex criteria

---

## ✅ Quality Assurance

1. **Input Validation**
   - Verify all trials are present across reviewers
   - Check for consistent criterion ordering
   - Validate JSON structure integrity

2. **Normalization Quality**
   - Log all normalization decisions
   - Maintain audit trail of semantic mappings
   - Document edge cases and resolution methods

3. **Discrepancy Analysis**
   - Categorize discrepancy types systematically
   - Assess clinical impact of disagreements
   - Identify systematic reviewer biases

4. **Output Verification**
   - Validate JSON schema compliance
   - Check mathematical consistency
   - Verify reference integrity

---

## 📌 Enhanced Example: Complex Multi-Trait Criterion

For criterion: "Participants >= 70 years of age who have an ECOG PS of 0 or 1 may be included due to: a) substantial comorbidities; b) contraindication(s) for any platinum-doublet chemotherapy"

**Reviewer 1 Extraction:**
```json
{
  "traits": [
    {
      "trait": "Age",
      "category": "Demographics", 
      "value": "≥70",
      "source_text": ">= 70 years of age"
    },
    {
      "trait": "ECOG PS",
      "category": "Performance Status/Functional Status",
      "value": "0-1",
      "source_text": "ECOG PS of 0 or 1"
    },
    {
      "trait": "Comorbidities",
      "category": "Comorbidities",
      "value": "Substantial",
      "source_text": "substantial comorbidities"
    }
  ]
}
```

**Reviewer 2 Extraction:**
```json
{
  "traits": [
    {
      "trait": "Age",
      "category": "Demographics",
      "value": "≥70 years",
      "source_text": ">= 70 years of age"
    },
    {
      "trait": "ECOG Performance Status",
      "category": "Functional Status",
      "value": "0 or 1",
      "source_text": "ECOG PS of 0 or 1"
    },
    {
      "trait": "Platinum therapy contraindication",
      "category": "Prior/Concurrent Treatments",
      "value": "Yes",
      "source_text": "contraindication(s) for any platinum-doublet chemotherapy"
    }
  ]
}
```

**Expected Discrepancy Analysis:**
- **Age**: Value mismatch ("≥70" vs "≥70 years") - Low severity
- **ECOG PS**: Synonym variation + category mismatch - Medium severity  
- **Comorbidities vs Platinum contraindication**: Granularity mismatch - High severity (missed trait)
# Clinical Trial Eligibility Criteria Analysis Prompt  
**(Immune Checkpoint Inhibitor [ICI] Trials)**

## Logic-Trait Consistency Guidelines

### Logical Query Construction
- **Variable Naming**: Use trait names (lowercase, underscore-separated) as logical variables (e.g., "diagnosis", "stage", "age")
- **Value Matching**: Ensure logical operators and values directly correspond to trait values
- **Operator Consistency**: Use standard logical operators (==, !=, >=, <=, >, <, AND, OR, NOT)
- **Value Format**: Maintain consistent value formats between logic and traits (e.g., if trait value is "IIIB or IV", logic should reference the same format)

### Consistency Requirements
- Every trait referenced in logic must appear in the traits array
- Every trait in the traits array should be referenced in the logic statement
- Trait names in logic should match trait names in the traits array (accounting for case and formatting differences)
- Values in logic should semantically match the values in corresponding traits

### Logic-Trait Mapping Examples
```
Logic: (diagnosis == 'NSCLC') AND (stage == 'IIIB or IV')
Traits: [
  {"trait": "Diagnosis", "value": "NSCLC"},
  {"trait": "Stage", "value": "IIIB or IV"}
]

Logic: (age >= 18) AND (ecog_ps <= 1)
Traits: [
  {"trait": "Age", "value": "≥18"},
  {"trait": "ECOG PS", "value": "0-1"}
]
```

## Original Phrase Extraction Guidelines

### Purpose
Extract the exact original phrases for both trait names and values as they appear in the source eligibility criteria text to maintain complete traceability and enable validation.

### Extraction Rules for Original Trait Phrases
- **Identify the exact word or phrase** in the original text that corresponds to the concept captured by the normalized trait name
- **Include contextual modifiers** that are part of the trait concept (e.g., "ECOG performance status" not just "performance")
- **Preserve original capitalization, spacing, and punctuation** exactly as written
- **Extract the minimal phrase** that captures the trait concept without unnecessary surrounding text

### Extraction Rules for Original Value Phrases
- **Capture the complete value expression** including operators, units, ranges, and qualifiers
- **Include comparison operators** (≥, ≤, >, <, =) and units (years, mg/dL, etc.) exactly as written
- **Preserve compound values** with their connecting words (e.g., "Stage IIIB not amenable for multimodality treatment or metastatic Stage IV")
- **Include negation and qualification phrases** that modify the value (e.g., "not amenable for multimodality treatment")

### Examples of Original Phrase Extraction
```
Original Text: "Age ≥ 18 years"
- original_trait_phrase: "Age"
- original_value_phrase: "≥ 18 years"

Original Text: "ECOG performance status 0-1"
- original_trait_phrase: "ECOG performance status"
- original_value_phrase: "0-1"

Original Text: "No active autoimmune disease"
- original_trait_phrase: "autoimmune disease"
- original_value_phrase: "No active"
```

### When Original Phrases Differ from Normalized
- **Always provide both fields** even if they appear redundant
- **Use original_trait_phrase** when the source uses different terminology than your normalized trait name
- **Use original_value_phrase** when the source expression is more complex than your normalized value
- **If identical to normalized form**, still include the original phrase fields for consistency

---

## Task Description

You are provided with the eligibility criteria text for a clinical trial utilizing immune checkpoint inhibitors (ICIs). Your objectives are:

1. **Trait Extraction:** Identify and extract all distinct study traits (i.e., self-contained elements that correspond to phenotypes such as demographics, laboratory tests, diagnoses, procedures, comorbidities, medications, prior treatments, and performance status) mentioned in the criteria.
2. **Logic Decomposition:** Decompose each eligibility criterion into a structured logical query based on the extracted traits, specifying inclusion/exclusion logic.
3. **Trait Categorization:** Classify each extracted trait into one of the following categories (expand list as needed based on content):  
    - Demographics  
    - Diagnosis/Disease  
    - Laboratory  
    - Procedures  
    - Prior/Concurrent Treatments  
    - Medications  
    - Comorbidities  
    - Performance Status/Functional Status  
    - Biomarkers/Molecular  
    - Organ Function  
    - Reproductive/Pregnancy Status  
    - Infection/Immunization  
    - Other (specify)
4. **Trait Normalization:** Normalize trait names and values to standardized, concise terminology while preserving the original text for transparency.
5. **Source Text Mapping:** Map each normalized trait back to its exact source text/phrases from the original criterion.
6. **Original Phrase Extraction:** Extract the exact original phrases for trait names and values as they appear in the source text.
7. **Logic-Trait Consistency:** Ensure logical queries use trait names as variables and that all traits referenced in logic appear in the traits array.
8. **Output:** Present the results in the JSON format specified below.

---

## Input Example

> **Inclusion Criteria:**  
> • Age ≥ 18 years  
> • Histologically confirmed stage IV NSCLC  
> • ECOG performance status 0–1  
> • Adequate hepatic function: ALT/AST ≤ 2.5 × ULN, bilirubin ≤ 1.5 × ULN  
>  
> **Exclusion Criteria:**  
> • Active autoimmune disease  
> • Prior treatment with anti-PD-1/PD-L1 therapy  
> • HIV infection  
> • Pregnant or breastfeeding women

---

## Trait Normalization Guidelines

### Trait Names
- Use standardized, concise terminology (e.g., "Age" not "Patient age")
- Use consistent naming conventions across similar traits
- Avoid redundant words and articles
- Focus on core clinical concepts (e.g., "Diagnosis", "Stage", "ECOG PS")
- Extract only the most essential traits that capture the clinical requirements

### Trait Values
- Normalize numeric thresholds to standard format (e.g., "≥18" instead of "greater than or equal to 18")
- Use consistent units and terminology
- Simplify complex expressions while preserving meaning
- Use standardized medical terminology (e.g., "Stage IV" not "stage 4")

### Examples of Normalization
- Original: "Histologically or cytologically confirmed diagnosis of advanced or recurrent (Stage IIIB not amenable for multimodality treatment) or metastatic (Stage IV) NSCLC as per the American Joint Committee on Cancer (AJCC) 7th edition"
  - Normalized trait: "Diagnosis"
  - Normalized value: "NSCLC"
  - Normalized trait: "Stage"  
  - Normalized value: "IIIB or IV"
- Original: "Eastern Cooperative Oncology Group performance status of 0 to 1"
  - Normalized trait: "ECOG PS"
  - Normalized value: "0-1"

---

## Output JSON Schema

```json
{
  "trial_id": "<NCT number or identifier>",
  "criteria": [
    {
      "type": "inclusion" | "exclusion",
      "original_text": "<original criterion text>",
      "logic": "<logical representation, e.g., (age >= 18)>",
      "traits": [
        {
          "trait": "<normalized trait name>",
          "category": "<trait category>",
          "value": "<normalized value/threshold/description>",
          "source_text": "<exact text/phrase from original criterion that corresponds to this trait>",
          "original_trait_phrase": "<original phrase for the trait name if different from normalized>",
          "original_value_phrase": "<original phrase for the value if different from normalized>"
        }
      ]
    },
  ]
}
```

---

## Trait Category Reference

Based on typical ICI trial eligibility criteria, common categories include (but are not limited to):

- **Demographics:** age, sex, pregnancy status
- **Diagnosis/Disease:** specific cancer type, stage, recurrence, progression
- **Laboratory:** hemoglobin, WBC, neutrophils, platelets, liver/renal function, biomarkers
- **Procedures:** surgery, radiotherapy, biopsy
- **Prior/Concurrent Treatments:** previous chemo, immunotherapy, lines of therapy
- **Medications:** current medication use, contraindicated drugs
- **Comorbidities:** cardiovascular disease, autoimmune disease, infection history
- **Performance Status:** ECOG, Karnofsky, Lansky
- **Biomarkers/Molecular:** PD-L1 expression, EGFR/ALK status, KRAS mutation
- **Organ Function:** cardiac, pulmonary, hepatic, renal
- **Reproductive/Pregnancy Status:** pregnancy test, contraception requirement, breastfeeding
- **Infection/Immunization:** HIV, hepatitis, tuberculosis, vaccine status
- **Other:** protocol-specified, investigator's judgment, compliance

---

## Quality Assurance Process

1. **Annotation Consistency:** Double annotation by two independent reviewers for a subset of trials; calculate inter-annotator agreement (e.g., Cohen's kappa).
2. **Validation:** Random sampling of output JSON to ensure logical queries match the original criteria, and trait categorization is accurate.
3. **Normalization Validation:** Verify that normalized traits and values maintain semantic equivalence with original text while achieving standardization.
4. **Original Phrase Extraction Validation:** Verify that original_trait_phrase and original_value_phrase fields accurately capture the exact phrases from the source text and follow extraction guidelines.
5. **Source Text Mapping Validation:** Ensure all source_text fields accurately reflect the original criterion text and completely cover all relevant phrases.
5. **Spot Checks for Ambiguity:** Flag criteria where trait boundaries or logic are ambiguous for expert adjudication.
6. **Edge Case Logging:** Maintain a log of edge cases and unusual trait expressions to iteratively refine extraction logic and improve consistency.
7. **Automated Checks:**  
    - Ensure every criterion has at least one mapped trait.  
    - Ensure no trait is uncategorized.  
    - Check logical expressions for completeness (e.g., no "…").
    - Verify all traits have corresponding source_text mappings.
8. **Version Control:** Maintain and version the prompt and mapping rules; document all changes and rationale.

---

## Example Output

```json
{
  "trial_id": "NCTXXXXXXX",
  "criteria": [
    {
      "type": "inclusion",
      "original_text": "Age ≥ 18 years",
      "logic": "(age >= 18)",
      "traits": [
        {
          "trait": "Age",
          "category": "Demographics",
          "value": "≥18",
          "source_text": "Age ≥ 18 years",
          "original_trait_phrase": "Age",
          "original_value_phrase": "≥ 18 years"
        }
      ]
    },
    {
      "type": "inclusion",
      "original_text": "Histologically confirmed diagnosis of advanced or recurrent (Stage IIIB) or metastatic (Stage IV) NSCLC",
      "logic": "(diagnosis == NSCLC) AND (stage == IIIB or IV)",
      "traits": [
        {
          "trait": "Diagnosis",
          "category": "Diagnosis/Disease",
          "value": "NSCLC",
          "source_text": "NSCLC",
          "original_trait_phrase": "NSCLC",
          "original_value_phrase": "NSCLC"
        },
        {
          "trait": "Stage",
          "category": "Diagnosis/Disease",
          "value": "IIIB or IV",
          "source_text": "Stage IIIB",
          "original_trait_phrase": "Stage",
          "original_value_phrase": "advanced or recurrent (Stage IIIB) or metastatic (Stage IV)"
        }
      ]
    },
    {
      "type": "exclusion",
      "original_text": "Active autoimmune disease",
      "logic": "(autoimmune_disease == 'active')",
      "traits": [
        {
          "trait": "Autoimmune disease",
          "category": "Comorbidities",
          "value": "Active",
          "source_text": "Active autoimmune disease",
          "original_trait_phrase": "autoimmune disease",
          "original_value_phrase": "Active"
        }
      ]
    }
  ]
}
```

---

## Instructions for Model Use

- **Decompose each eligibility criterion as a standalone logical statement referencing study traits.**
- **Ensure logic-trait consistency by using trait names as logical variables and maintaining semantic alignment between logic expressions and trait values.**
- **Normalize trait names to concise, standardized terminology while preserving medical accuracy.**
- **Normalize trait values to consistent formats (e.g., standardized units, abbreviated forms).**
- **Map every normalized trait back to its exact source text from the original criterion.**
- **Extract exact original phrases for both trait names and values as they appear in the source text using the detailed extraction guidelines.**
- **Ensure source_text field captures the complete relevant phrase, not just keywords.**
- **For compound criteria, create separate trait objects for each distinct concept.**
- **Categorize each trait using the most specific category possible.**
- **Where multiple traits are present in a single criterion, create separate trait objects within the same criterion.**
- **For ambiguous cases, annotate as "Other" and flag for review.**
- **Maintain semantic equivalence between original and normalized forms.**
- **Use original_trait_phrase and original_value_phrase fields when normalization significantly changes the original wording.**
- **Strictly adhere to the JSON schema for downstream compatibility.**
- **Document any assumptions or uncertainties in the output as comments.**

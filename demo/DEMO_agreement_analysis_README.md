# Demo Agreement Analysis Script

This document provides comprehensive instructions for using the `demo_agreement_analysis.py` script, which demonstrates the functionality of the clinical trial criteria agreement analysis tool.

## Overview

The demo script showcases the agreement analysis capabilities by:

1. **Running analysis on sample data** with both local and LLM-based methods
2. **Displaying key results** in a user-friendly format with visual indicators
3. **Showing examples of discrepancies** found between different reviewers/models
4. **Generating a comprehensive summary report** in Markdown format
5. **Providing interpretation guidance** to help understand the results

## Quick Start

### Basic Demo (Local Analysis Only)

Run the demo with local analysis (no API keys required):

```bash
python demo_agreement_analysis.py --local-only
```

This will:
- ✅ Check that sample data is available
- 🔄 Run local agreement analysis on the sample data
- 📊 Display detailed results with quality assessments
- 📄 Generate a summary report in `outputs/`

### Full Demo (Local + LLM Analysis)

To run both local and LLM-based analysis:

1. **Create API keys file** (copy from template):
   ```bash
   cp api_keys_template.json api_keys.json
   # Edit api_keys.json with your actual API keys
   ```

2. **Run demo with LLM analysis**:
   ```bash
   python demo_agreement_analysis.py --api-keys api_keys.json --model claude
   ```

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--local-only` | Run only local analysis (no API required) | `--local-only` |
| `--api-keys FILE` | Path to API keys JSON file | `--api-keys api_keys.json` |
| `--model MODEL` | LLM model to use (`claude`, `openai`, `gemini`) | `--model claude` |

## Sample Output

The demo provides rich, formatted output including:

### 📊 Agreement Metrics Display
```
📊 OVERALL AGREEMENT METRICS
   Total criteria analyzed: 107
   Exact criterion matches: 18
   Criterion match ratio: 0.168
   Overall trait agreement: 0.177
   Total discrepancies: 269

🔍 PAIRWISE REVIEWER METRICS

   Pair 1: claude-claude vs openai-gpt
   Quality Assessment: 🔴 Poor
   ├─ Precision: 0.328
   ├─ Recall: 0.273
   ├─ F1-Score: 0.298
   ├─ Jaccard Index: 0.175
   └─ Cohen's Kappa: -0.650
```

### 🔍 Discrepancy Examples
```
🔸 Missing In Reviewer 2
   Trial: NCT03191786
   Criterion: Histologically or cytologically confirmed diagnosis...
   claude-claude: NSCLC diagnosis | Diagnosis/Disease | histologically confirmed
   openai-gpt:  |  | 
   Explanation: Trait 'NSCLC diagnosis' identified by claude-claude but not openai-gpt
```

### 📈 Quality Assessment Indicators

The demo uses visual indicators to quickly assess agreement quality:

- 🟢 **Excellent**: F1-score > 0.9, Cohen's kappa > 0.8
- 🟡 **Good**: F1-score > 0.8, Cohen's kappa > 0.6  
- 🟠 **Moderate**: F1-score > 0.6, Cohen's kappa > 0.4
- 🔴 **Poor**: F1-score < 0.6, Cohen's kappa < 0.4

## Generated Outputs

The demo creates several output files in the `outputs/` directory:

### 1. Analysis Results (JSON)
- `agreement_analysis_local_TIMESTAMP.json` - Local analysis results
- `agreement_analysis_MODEL_TIMESTAMP.json` - LLM analysis results (if run)

### 2. Summary Report (Markdown)
- `demo_summary_report_TIMESTAMP.md` - Comprehensive analysis report

Example report structure:
```markdown
# Clinical Trial Criteria Agreement Analysis Demo Report

## Executive Summary
- Overall Agreement: 0.177
- Criterion Match Ratio: 0.168
- Total Discrepancies: 269

## Detailed Results
[Pairwise metrics table]
[Discrepancy summary table]

## Recommendations
🔴 Low Agreement Detected
- Significant inconsistencies found
- Recommend reviewing decomposition process

## Next Steps
1. Review detailed discrepancy analysis
2. Identify patterns in disagreements
...
```

## Understanding the Results

### What the Sample Data Shows

The demo analyzes decomposed criteria from three different AI models:
- **Claude Sonnet 4** (`claude-claude`)
- **GPT-4o** (`openai-gpt`) 
- **Gemini 2.5 Pro** (`gemini-gemini`)

### Typical Results

When run on the sample data, you can expect:

- **Low overall agreement** (~0.17) - This is normal for complex clinical criteria
- **Many discrepancies** (~269) - Shows different models extract traits differently
- **Poor quality ratings** - Indicates need for standardization

### Key Insights

The sample results demonstrate:

1. **Model Variability**: Different AI models extract traits with varying granularity
2. **Categorization Differences**: Same traits may be categorized differently
3. **Missing Traits**: Models may miss traits that others identify
4. **Value Formatting**: Different ways of expressing the same concept

## Troubleshooting

### Common Issues

#### 1. "Sample data directory not found"
**Solution**: Ensure you're running from the project root directory where `sample_data/decomposed/` exists.

#### 2. "Need at least 2 JSON files for comparison"
**Solution**: Verify that `sample_data/decomposed/` contains the sample JSON files.

#### 3. "API keys file not found"
**Solution**: Create `api_keys.json` from the template and add your actual API keys.

#### 4. "LLM analysis failed"
**Possible causes**:
- Invalid API keys
- Network connectivity issues
- API rate limits
- Insufficient API credits

### Performance Notes

- **Local analysis**: Fast (~30 seconds), no API calls required
- **LLM analysis**: Slower (~2-5 minutes), requires API access
- **Memory usage**: Moderate, suitable for typical development machines

## Customization

### Using Your Own Data

To run the demo on your own decomposed criteria:

1. **Prepare your data**: Ensure JSON files follow the expected format
2. **Update the script**: Modify the `sample_dir` path in `check_sample_data()`
3. **Run analysis**: Use the same commands with your data directory

### Modifying Output Format

The demo script is designed to be easily customizable:

- **Metrics display**: Modify `display_agreement_summary()`
- **Discrepancy examples**: Adjust `display_discrepancy_examples()`
- **Report generation**: Customize `generate_summary_report()`

## Integration with Workflow

### As a Validation Tool

Use the demo to validate your decomposition process:

```bash
# After running decomposition on new data
python demo_agreement_analysis.py --local-only
# Review results and adjust process if needed
```

### For Model Comparison

Compare different AI models' performance:

```bash
# Run with different models
python demo_agreement_analysis.py --api-keys api_keys.json --model claude
python demo_agreement_analysis.py --api-keys api_keys.json --model openai
python demo_agreement_analysis.py --api-keys api_keys.json --model gemini
```

### Batch Processing

For multiple datasets:

```bash
#!/bin/bash
for dataset in dataset1 dataset2 dataset3; do
    # Update sample data path for each dataset
    python demo_agreement_analysis.py --local-only
    mv outputs/demo_summary_report_*.md outputs/${dataset}_report.md
done
```

## Next Steps

After running the demo:

1. **Review the generated report** to understand agreement patterns
2. **Examine discrepancy examples** to identify improvement opportunities
3. **Consider running on your own data** to validate your decomposition process
4. **Use insights** to refine decomposition guidelines or model selection

## Related Files

- [`demo_agreement_analysis.py`](demo_agreement_analysis.py) - Main demo script
- [`analyze_criteria_agreement.py`](analyze_criteria_agreement.py) - Core analysis tool
- [`api_keys_template.json`](api_keys_template.json) - API keys template
- [`sample_data/decomposed/`](sample_data/decomposed/) - Sample data for demo
- [`AGREEMENT_ANALYSIS_README.md`](AGREEMENT_ANALYSIS_README.md) - Detailed analysis documentation

For questions or issues with the demo, refer to the main analysis documentation or examine the sample outputs for format examples.
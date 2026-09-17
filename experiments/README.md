# Experiments - Batch Processing for Criteria Decomposition

This folder contains scripts for mass testing and batch processing of clinical trial eligibility criteria decomposition.

## Files

- **[`batch_run_decompose_criteria.py`](batch_run_decompose_criteria.py)** - Main batch processing script
- **[`cost_calculator.py`](cost_calculator.py)** - Cost estimation and tracking utilities
- **[`config.json`](config.json)** - Configuration file for batch processing parameters
- **[`requirements.txt`](requirements.txt)** - Additional Python dependencies

## Features

### 🚀 Batch Processing
- Process multiple input files simultaneously
- Support for multiple AI models (OpenAI, Claude, Gemini)
- Configurable retry logic and error handling
- Automatic output organization with timestamps

### 📊 Progress Tracking
- Colored progress bars using `tqdm`
- Real-time cost tracking during processing
- Success/failure statistics per model
- Detailed logging with timestamps

### 💰 Cost Management
- **Pre-processing cost estimation** - Get cost estimates before running
- **Real-time cost tracking** - Monitor accumulated costs during processing
- **Detailed cost breakdown** - Per-model and per-trial cost analysis
- **Multiple model pricing** - Support for OpenAI, Claude, and Gemini pricing

### 🎯 Configuration-Driven
- All parameters stored in `config.json`
- No command-line arguments needed (except config path)
- Easy to modify and version control settings

## Setup

1. **Install additional dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your settings in `config.json`:**
   ```json
   {
     "input_files": ["../sample_data/ici_criteria_sample_5.json"],
     "models": [
       {"provider": "openai", "model_name": "gpt-4o"},
       {"provider": "claude", "model_name": "claude-sonnet-4"}
     ],
     "estimate_costs": true,
     "show_progress": true
   }
   ```

3. **Ensure your API keys file is configured** (referenced in config.json)

## Usage

### Basic Usage
```bash
cd experiments
python batch_run_decompose_criteria.py
```

### Custom Configuration
```bash
python batch_run_decompose_criteria.py --config my_custom_config.json
```

### Verbose Logging
```bash
python batch_run_decompose_criteria.py --verbose
```

## Configuration Options

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `input_files` | list | Paths to JSON files containing trial criteria | Required |
| `prompt_template` | string | Path to prompt markdown file | Required |
| `api_keys_file` | string | Path to API keys JSON file | Required |
| `models` | list | List of model configurations to use | Required |
| `output_directory` | string | Where to save results | `../outputs/batch_experiments` |
| `cache_enabled` | boolean | Enable/disable prompt caching | `true` |
| `retry_count` | integer | Number of retries on failure | `2` |
| `retry_delay` | float | Initial delay between retries (seconds) | `1.0` |
| `show_progress` | boolean | Show colored progress bars | `true` |
| `estimate_costs` | boolean | Show cost estimates before processing | `true` |

## Model Configuration

Each model in the `models` array should have:

```json
{
  "provider": "openai|claude|gemini",
  "model_name": "specific-model-name"
}
```

### Supported Models

#### OpenAI
- `gpt-4o` (recommended)
- `gpt-4`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

#### Anthropic Claude
- `claude-sonnet-4` (recommended)
- `claude-3-opus`
- `claude-3-sonnet`
- `claude-3-haiku`

#### Google Gemini
- `gemini-2.5-pro` (recommended)
- `gemini-pro`
- `gemini-1.5-pro`

## Output Structure

The script generates several output files:

```
outputs/batch_experiments/
├── batch_results_YYYYMMDD_HHMMSS.json    # Main results with metadata
├── openai_gpt-4o_YYYYMMDD_HHMMSS.json    # Individual model results
├── claude_claude-sonnet-4_YYYYMMDD_HHMMSS.json
├── gemini_gemini-2.5-pro_YYYYMMDD_HHMMSS.json
└── cost_summary_YYYYMMDD_HHMMSS.txt      # Detailed cost breakdown
```

### Main Results File Structure

```json
{
  "metadata": {
    "timestamp": "20250705_135500",
    "config": { /* original config */ },
    "cost_summary": { /* total costs and usage */ }
  },
  "results": {
    "openai_gpt-4o": {
      "model_key": "openai_gpt-4o",
      "provider": "openai",
      "model_name": "gpt-4o",
      "results": { /* decomposed criteria for each trial */ },
      "successful_count": 5,
      "total_count": 5
    }
  },
  "failed_trials": { /* any trials that failed processing */ }
}
```

## Cost Estimation

The script provides detailed cost estimation before processing:

```
💰 COST ESTIMATION
============================================================
📊 Total trials to process: 5
🤖 Models to use: 3

🔹 GPT-4o:
   Cost per trial: $0.0234
   Total cost: $0.1170

🔹 Claude Sonnet 4:
   Cost per trial: $0.0187
   Total cost: $0.0935

🔹 Gemini 2.5 Pro:
   Cost per trial: $0.0098
   Total cost: $0.0490

💸 ESTIMATED GRAND TOTAL: $0.2595
============================================================
```

## Progress Tracking

During processing, you'll see colored progress bars:

```
🔄 Processing 5 trials with 3 models...

📋 Model 1/3: openai - gpt-4o
🤖 OPENAI: 100%|████████████| 5/5 [00:45<00:00, 9.12s/trial] cost=$0.117 last=$0.023

📋 Model 2/3: claude - claude-sonnet-4  
🤖 CLAUDE: 100%|████████████| 5/5 [00:38<00:00, 7.65s/trial] cost=$0.211 last=$0.019

💰 Running total cost: $0.2595
```

## Error Handling

- **Retry Logic**: Configurable retry count with exponential backoff
- **Graceful Failures**: Individual trial failures don't stop the entire batch
- **Detailed Logging**: All errors are logged with context
- **Failed Trials Tracking**: Failed trials are saved separately for analysis

## Example Workflow

1. **Prepare your data**: Ensure your input JSON files are in the correct format
2. **Configure**: Update `config.json` with your desired settings
3. **Estimate**: Run the script to see cost estimates
4. **Confirm**: Approve the estimated costs to proceed
5. **Monitor**: Watch progress bars and cost accumulation
6. **Analyze**: Review results in the generated output files

## Tips

- **Start Small**: Test with a subset of trials first
- **Monitor Costs**: The script warns for costs over $10
- **Use Caching**: Enable caching to avoid re-processing identical inputs
- **Check Logs**: Use `--verbose` flag for detailed debugging information
- **Backup Results**: Output files include timestamps to prevent overwrites

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Install with `pip install -r requirements.txt`
2. **API Key Errors**: Ensure your API keys file is properly configured
3. **File Not Found**: Check that input file paths in config.json are correct
4. **Permission Errors**: Ensure write permissions for the output directory

### Getting Help

- Check the logs for detailed error messages
- Use `--verbose` flag for more debugging information
- Verify your configuration against the examples in this README
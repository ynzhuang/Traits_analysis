#!/usr/bin/env python3
"""
Batch processing script for decomposing clinical trial eligibility criteria.
This script processes multiple input files using various AI models with progress tracking and cost estimation.
"""

import argparse
import json
import os
import sys
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple
from pathlib import Path

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import services
from services.api_key_service import APIKeyService
from services.llm_service import LLMService
from services.prompt_service import PromptService
from services.cache_service import CacheService
from services.chain_service import ChainService

# Import schemas
from schemas import DecomposedCriteria

# Import local modules
from cost_calculator import CostCalculator

# Third-party imports for progress bar
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("⚠️  tqdm not available. Install with: pip install tqdm")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class BatchProcessor:
    """Batch processor for criteria decomposition with progress tracking and cost estimation."""
    
    def __init__(self, config_path: str):
        """
        Initialize the batch processor.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.cost_calculator = CostCalculator()
        self.results = {}
        self.failed_trials = {}
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logging.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logging.error(f"Failed to load configuration from {config_path}: {e}")
            raise
    
    def _load_input_files(self) -> Dict[str, Dict[str, str]]:
        """
        Load all input files specified in the configuration.
        
        Returns:
            Dictionary mapping file paths to their trial data
        """
        all_trials = {}
        
        for input_file in self.config['input_files']:
            try:
                logging.info(f"Loading input file: {input_file}")
                with open(input_file, 'r') as f:
                    trials = json.load(f)
                
                # Add file prefix to trial IDs to avoid conflicts
                file_prefix = Path(input_file).stem
                prefixed_trials = {
                    f"{file_prefix}_{trial_id}": criteria 
                    for trial_id, criteria in trials.items()
                }
                
                all_trials.update(prefixed_trials)
                logging.info(f"Loaded {len(trials)} trials from {input_file}")
                
            except Exception as e:
                logging.error(f"Failed to load {input_file}: {e}")
                continue
        
        logging.info(f"Total trials loaded: {len(all_trials)}")
        return all_trials
    
    def _estimate_batch_cost(self, trials: Dict[str, str]) -> Dict[str, Any]:
        """
        Estimate the total cost for processing all trials with all models.
        
        Args:
            trials: Dictionary of trial data
            
        Returns:
            Cost estimation breakdown
        """
        logging.info("🧮 Estimating batch processing costs...")
        
        # Load prompt template to estimate input size
        prompt_template = PromptService.load_prompt_template(self.config['prompt_template'])
        
        # Estimate average input size
        sample_criteria = list(trials.values())[0] if trials else ""
        sample_input = f"Decompose the following criteria for trial sample:\n\n{sample_criteria}"
        
        total_estimates = {}
        grand_total = 0.0
        
        for model_config in self.config['models']:
            model_name = model_config['model_name']
            provider = model_config['provider']
            
            # Estimate cost per trial
            cost_per_trial, breakdown = self.cost_calculator.estimate_cost(
                model_name, 
                sample_input, 
                estimated_output_tokens=1500  # Estimated output size
            )
            
            # Calculate total for all trials
            total_cost = cost_per_trial * len(trials)
            grand_total += total_cost
            
            total_estimates[f"{provider}_{model_name}"] = {
                'cost_per_trial': cost_per_trial,
                'total_cost': total_cost,
                'trial_count': len(trials),
                'breakdown': breakdown
            }
        
        return {
            'grand_total': grand_total,
            'model_estimates': total_estimates,
            'trial_count': len(trials)
        }
    
    def _print_cost_estimate(self, cost_estimate: Dict[str, Any]) -> None:
        """Print formatted cost estimate."""
        print("\n" + "="*60)
        print("💰 COST ESTIMATION")
        print("="*60)
        print(f"📊 Total trials to process: {cost_estimate['trial_count']:,}")
        print(f"🤖 Models to use: {len(self.config['models'])}")
        print()
        
        for model_key, estimate in cost_estimate['model_estimates'].items():
            print(f"🔹 {estimate['breakdown']['model']}:")
            print(f"   Cost per trial: ${estimate['cost_per_trial']:.4f}")
            print(f"   Total cost: ${estimate['total_cost']:.4f}")
            print()
        
        print(f"💸 ESTIMATED GRAND TOTAL: ${cost_estimate['grand_total']:.4f}")
        print("="*60)
    
    def _confirm_proceed(self, cost_estimate: Dict[str, Any]) -> bool:
        """Ask user to confirm proceeding with the estimated cost."""
        if cost_estimate['grand_total'] > 10.0:  # Warn for costs over $10
            print(f"\n⚠️  WARNING: Estimated cost is ${cost_estimate['grand_total']:.2f}")
            print("This is a significant amount. Please confirm you want to proceed.")
        
        while True:
            response = input("\n🤔 Do you want to proceed? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'")
    
    def _process_with_model(self, model_config: Dict[str, str], trials: Dict[str, str]) -> Dict[str, Any]:
        """
        Process all trials with a specific model.
        
        Args:
            model_config: Model configuration
            trials: Dictionary of trial data
            
        Returns:
            Processing results for this model
        """
        provider = model_config['provider']
        model_name = model_config.get('model_name')
        
        logging.info(f"🚀 Starting processing with {provider} ({model_name})")
        
        try:
            # Load API keys
            api_keys = APIKeyService.load_api_keys(self.config['api_keys_file'])
            
            # Add model override if specified
            if model_name:
                api_keys = APIKeyService.add_model_override(api_keys, provider, model_name)
            
            # Set up caching
            CacheService.setup_cache(self.config.get('cache_enabled', True))
            
            # Get the language model
            llm, explicit_model_name = LLMService.get_llm(provider, api_keys, DecomposedCriteria)
            
            # Load and prepare prompt
            prompt_template = PromptService.load_prompt_template(self.config['prompt_template'])
            human_template = "Decompose the following criteria for trial {trial_id}:\n\n{criteria}"
            prompt = PromptService.prepare_prompt_for_provider(
                prompt_template,
                provider,
                human_template,
                template_variables=['trial_id', 'criteria']
            )
            
            # Create the chain
            chain = ChainService.create_chain(prompt, llm)
            
            # Process trials with progress bar
            model_results = {}
            model_key = f"{provider}_{explicit_model_name}"
            
            # Create progress bar
            if TQDM_AVAILABLE and self.config.get('show_progress', True):
                progress_bar = tqdm(
                    trials.items(), 
                    desc=f"🤖 {provider.upper()}", 
                    unit="trial",
                    colour="green"
                )
            else:
                progress_bar = trials.items()
            
            for trial_id, criteria_text in progress_bar:
                try:
                    # Ensure trial_id is a string
                    trial_id_str = str(trial_id)
                    
                    # Estimate input tokens for cost tracking
                    input_text = f"Decompose the following criteria for trial {trial_id_str}:\n\n{criteria_text}"
                    estimated_input_tokens = self.cost_calculator.estimate_tokens(input_text)
                    
                    # Process the trial
                    result, duration = ChainService.invoke_chain(
                        chain,
                        {"trial_id": trial_id_str, "criteria": criteria_text},
                        retry_count=self.config.get('retry_count', 2),
                        retry_delay=self.config.get('retry_delay', 1.0),
                        operation_name=f"Processing trial: {trial_id_str}"
                    )
                    
                    # Convert result to dict
                    result_dict = result.model_dump()
                    model_results[trial_id_str] = result_dict
                    
                    # Estimate output tokens and add to cost tracking
                    estimated_output_tokens = self.cost_calculator.estimate_tokens(str(result_dict))
                    cost = self.cost_calculator.add_usage(
                        explicit_model_name, 
                        estimated_input_tokens, 
                        estimated_output_tokens
                    )
                    
                    # Update progress bar with cost info if available
                    if TQDM_AVAILABLE and hasattr(progress_bar, 'set_postfix'):
                        progress_bar.set_postfix({
                            'cost': f"${self.cost_calculator.total_cost:.3f}",
                            'last': f"${cost:.4f}"
                        })
                    
                    logging.debug(f"✅ Processed {trial_id_str} - Cost: ${cost:.4f}")
                    
                except Exception as e:
                    logging.error(f"❌ Failed to process trial {trial_id}: {e}")
                    if trial_id not in self.failed_trials:
                        self.failed_trials[trial_id] = {}
                    self.failed_trials[trial_id][model_key] = str(e)
                    continue
            
            logging.info(f"✅ Completed {provider} processing: {len(model_results)}/{len(trials)} successful")
            return {
                'model_key': model_key,
                'provider': provider,
                'model_name': explicit_model_name,
                'results': model_results,
                'successful_count': len(model_results),
                'total_count': len(trials)
            }
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize {provider} model: {e}")
            return {
                'model_key': f"{provider}_{model_name or 'unknown'}",
                'provider': provider,
                'model_name': model_name,
                'results': {},
                'successful_count': 0,
                'total_count': len(trials),
                'error': str(e)
            }
    
    def _save_results(self, all_results: Dict[str, Any]) -> str:
        """
        Save processing results to output files.
        
        Args:
            all_results: Dictionary containing all processing results
            
        Returns:
            Path to the main output file
        """
        # Create output directory
        output_dir = self.config.get('output_directory', 'outputs/batch_experiments')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save main results file
        main_output_file = os.path.join(output_dir, f"batch_results_{timestamp}.json")
        
        output_data = {
            'metadata': {
                'timestamp': timestamp,
                'config': self.config,
                'cost_summary': self.cost_calculator.get_summary()
            },
            'results': all_results,
            'failed_trials': self.failed_trials
        }
        
        with open(main_output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        # Save individual model results
        for model_key, model_data in all_results.items():
            if 'results' in model_data and model_data['results']:
                model_file = os.path.join(output_dir, f"{model_key}_{timestamp}.json")
                with open(model_file, 'w') as f:
                    json.dump(model_data['results'], f, indent=2)
                logging.info(f"💾 Saved {model_key} results to {model_file}")
        
        # Save cost summary
        cost_file = os.path.join(output_dir, f"cost_summary_{timestamp}.txt")
        with open(cost_file, 'w') as f:
            f.write(self.cost_calculator.format_cost_summary())
        
        logging.info(f"💾 Saved main results to {main_output_file}")
        logging.info(f"💾 Saved cost summary to {cost_file}")
        
        return main_output_file
    
    def run(self) -> str:
        """
        Run the batch processing.
        
        Returns:
            Path to the main output file
        """
        try:
            logging.info("🚀 Starting batch criteria decomposition process")
            
            # Load input data
            trials = self._load_input_files()
            if not trials:
                raise ValueError("No trials loaded from input files")
            
            # Estimate costs
            if self.config.get('estimate_costs', True):
                cost_estimate = self._estimate_batch_cost(trials)
                self._print_cost_estimate(cost_estimate)
                
                if not self._confirm_proceed(cost_estimate):
                    logging.info("❌ Processing cancelled by user")
                    return None
            
            # Process with each model
            all_results = {}
            
            print(f"\n🔄 Processing {len(trials)} trials with {len(self.config['models'])} models...")
            
            for i, model_config in enumerate(self.config['models'], 1):
                print(f"\n📋 Model {i}/{len(self.config['models'])}: {model_config['provider']} - {model_config.get('model_name', 'default')}")
                
                model_results = self._process_with_model(model_config, trials)
                all_results[model_results['model_key']] = model_results
                
                # Print intermediate cost update
                print(f"💰 Running total cost: ${self.cost_calculator.total_cost:.4f}")
            
            # Save results
            output_file = self._save_results(all_results)
            
            # Print final summary
            self._print_final_summary(all_results)
            
            return output_file
            
        except Exception as e:
            logging.error(f"❌ Batch processing failed: {e}")
            raise
    
    def _print_final_summary(self, all_results: Dict[str, Any]) -> None:
        """Print final processing summary."""
        print("\n" + "="*60)
        print("📊 BATCH PROCESSING SUMMARY")
        print("="*60)
        
        total_successful = 0
        total_trials = 0
        
        for model_key, model_data in all_results.items():
            successful = model_data.get('successful_count', 0)
            total = model_data.get('total_count', 0)
            total_successful += successful
            total_trials = total  # Should be same for all models
            
            status = "✅" if successful == total else "⚠️"
            print(f"{status} {model_key}: {successful}/{total} trials")
        
        print(f"\n🎯 Overall Success Rate: {total_successful}/{total_trials * len(all_results)} ({(total_successful/(total_trials * len(all_results))*100):.1f}%)")
        
        if self.failed_trials:
            print(f"❌ Failed Trials: {len(self.failed_trials)}")
        
        print("\n💰 Final Cost Summary:")
        print(self.cost_calculator.format_cost_summary())
        print("="*60)


def main():
    """Main function for batch processing."""
    parser = argparse.ArgumentParser(description="Batch process clinical trial eligibility criteria decomposition.")
    parser.add_argument('--config', default='config.json', help="Path to the configuration file (default: config.json)")
    parser.add_argument('--verbose', '-v', action='store_true', help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize and run batch processor
        processor = BatchProcessor(args.config)
        output_file = processor.run()
        
        if output_file:
            print(f"\n🎉 Batch processing completed successfully!")
            print(f"📁 Results saved to: {output_file}")
        else:
            print("\n❌ Batch processing was cancelled or failed")
            
    except Exception as e:
        logging.error(f"❌ Batch processing failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
import argparse
import json
import os
import logging
import time
from datetime import datetime

# Import services
from services.api_key_service import APIKeyService
from services.llm_service import LLMService
from services.prompt_service import PromptService
from services.cache_service import CacheService
from services.chain_service import ChainService

# Import schemas
from schemas import DecomposedCriteria

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



def main():
    """Main function to decompose clinical trial eligibility criteria."""
    parser = argparse.ArgumentParser(description="Decompose clinical trial eligibility criteria using a language model.")
    parser.add_argument('--prompt', required=True, help="Path to the prompt markdown file.")
    parser.add_argument('--criteria', required=True, help="Path to the JSON file with eligibility criteria.")
    parser.add_argument('--api-keys', required=True, help="Path to the JSON file with API keys.")
    parser.add_argument('--model', required=True, choices=['openai', 'gemini', 'claude'], help="Language model provider to use.")
    parser.add_argument('--model-name', help="Specific model name to use (e.g., gpt-4o, gpt-4-turbo).")
    parser.add_argument('--no-cache', dest='cache', action='store_false', help="Disable prompt caching.")
    parser.set_defaults(cache=True)
    args = parser.parse_args()

    try:
        logging.info("Starting criteria decomposition process.")
        
        # Load prompt template using service
        prompt_template = PromptService.load_prompt_template(args.prompt)

        # Read the eligibility criteria
        logging.info(f"Reading eligibility criteria from {args.criteria}")
        with open(args.criteria, 'r') as f:
            eligibility_criteria = json.load(f)

        # Load API keys using service
        api_keys = APIKeyService.load_api_keys(args.api_keys)

        # Add model override if specified
        if args.model_name:
            api_keys = APIKeyService.add_model_override(api_keys, args.model, args.model_name)

        # Set up caching using service
        CacheService.setup_cache(args.cache)

        # Get the language model using service
        llm, explicit_model_name = LLMService.get_llm(args.model, api_keys, DecomposedCriteria)

        # Create the prompt using service
        human_template = "Decompose the following criteria for trial {trial_id}:\n\n{criteria}"
        prompt = PromptService.prepare_prompt_for_provider(
            prompt_template,
            args.model,
            human_template,
            template_variables=['trial_id', 'criteria']
        )

        # Create the chain using service
        chain = ChainService.create_chain(prompt, llm)

        # Process each trial
        results = {}
        for trial_id, criteria_text in eligibility_criteria.items():
            try:
                # Ensure trial_id is a string to prevent concatenation errors
                trial_id_str = str(trial_id)
                
                result, duration = ChainService.invoke_chain(
                    chain,
                    {"trial_id": trial_id_str, "criteria": criteria_text},
                    operation_name=f"Processing trial: {trial_id_str}"
                )
                # The output is now a Pydantic model, so we can convert it to a dict
                results[trial_id_str] = result.model_dump()
                logging.info(f"Successfully processed trial {trial_id_str}")
            except Exception as e:
                logging.error(f"An unexpected error occurred while processing trial {trial_id}: {e}")

        # Generate the output path and filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        criteria_filename = os.path.splitext(os.path.basename(args.criteria))[0]
        
        # Create the output directory structure
        output_dir = os.path.join('outputs', criteria_filename)
        os.makedirs(output_dir, exist_ok=True)

        # Construct the filename
        output_filename_only = f"{criteria_filename}-{args.model}-{explicit_model_name}-{timestamp}.json"
        full_output_path = os.path.join(output_dir, output_filename_only)

        # Write the output
        logging.info(f"Writing results to {full_output_path}")
        with open(full_output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logging.info(f"Successfully decomposed criteria and saved to {full_output_path}")

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)

if __name__ == '__main__':
    main()
import ijson
import json
import logging
import argparse
import os

def extract_eligibility_criteria(input_filename):
    """
    Extracts eligibility criteria from a JSON file of clinical trial studies.

    Args:
        input_filename (str): The name of the input JSON file.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Generate output filename from input filename
    base_filename = os.path.splitext(input_filename)[0]
    output_filename = f"{base_filename}_eligibility_criteria.json"

    eligibility_criteria = {}
    
    try:
        with open(input_filename, 'rb') as f:
            # We are looking for each study object in the list of studies.
            # The path to each study is 'item' since the root is an array.
            studies = ijson.items(f, 'item')
            
            for study in studies:
                try:
                    protocol_section = study.get('protocolSection', {})
                    
                    identification_module = protocol_section.get('identificationModule', {})
                    nct_id = identification_module.get('nctId')
                    
                    eligibility_module = protocol_section.get('eligibilityModule', {})
                    criteria = eligibility_module.get('eligibilityCriteria')
                    
                    if nct_id and criteria:
                        eligibility_criteria[nct_id] = criteria
                        logging.info(f"Extracted criteria for {nct_id}")
                        
                except Exception as e:
                    logging.error(f"Error processing a study: {e}")
                    continue

        with open(output_filename, "w") as f:
            json.dump(eligibility_criteria, f, indent=2)
        
        logging.info(f"Successfully extracted eligibility criteria for {len(eligibility_criteria)} studies.")
        logging.info(f"Results saved to {output_filename}")

    except FileNotFoundError:
        logging.error(f"Input file not found: {input_filename}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract eligibility criteria from a JSON file of clinical trial studies.")
    parser.add_argument("--input_filename", required=True, help="The name of the input JSON file.")
    args = parser.parse_args()
    
    extract_eligibility_criteria(args.input_filename)
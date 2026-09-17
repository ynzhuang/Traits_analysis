import requests
import json
import argparse
import logging
import os
from enum import Enum


class StudyPhase(Enum):
    NA = "NA"
    EARLY_PHASE1 = "EARLY_PHASE1"
    PHASE1 = "PHASE1"
    PHASE2 = "PHASE2"
    PHASE3 = "PHASE3"
    PHASE4 = "PHASE4"


class StudyStatus(Enum):
    ACTIVE_NOT_RECRUITING = "ACTIVE_NOT_RECRUITING"
    COMPLETED = "COMPLETED"
    ENROLLING_BY_INVITATION = "ENROLLING_BY_INVITATION"
    NOT_YET_RECRUITING = "NOT_YET_RECRUITING"
    RECRUITING = "RECRUITING"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"
    WITHDRAWN = "WITHDRAWN"
    AVAILABLE = "AVAILABLE"
    NO_LONGER_AVAILABLE = "NO_LONGER_AVAILABLE"
    TEMPORARILY_NOT_AVAILABLE = "TEMPORARILY_NOT_AVAILABLE"
    APPROVED_FOR_MARKETING = "APPROVED_FOR_MARKETING"
    WITHHELD = "WITHHELD"
    UNKNOWN = "UNKNOWN"


def search_clinical_trials(intervention, phases=None, statuses=None):
    """
    Searches for clinical trials on ClinicalTrials.gov based on the intervention and handles pagination.

    Args:
        intervention (str): The intervention/treatment to search for.
        phases (list, optional): A list of StudyPhase enums to filter by.
        statuses (list, optional): A list of StudyStatus enums to filter by.

    Returns:
        list: A list of all studies found, or None if the request fails.
    """
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {"query.intr": intervention, "format": "json", "pageSize": 1000}

    if statuses:
        params["filter.overallStatus"] = ",".join([s.value for s in statuses])

    if phases:
        phase_query = " OR ".join([p.value for p in phases])
        params["filter.advanced"] = f"AREA[Phase]({phase_query})"

    all_studies = []
    page_token = None

    while True:
        if page_token:
            params["pageToken"] = page_token

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            studies = data.get("studies", [])
            all_studies.extend(studies)
            logging.info(f"Fetched {len(studies)} studies. Total fetched: {len(all_studies)}.")
            
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        except requests.exceptions.RequestException as e:
            logging.error(f"An error occurred: {e}")
            return None
            
    return all_studies


def main():
    """
    Main function to execute the script.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    parser = argparse.ArgumentParser(
        description="Search for clinical trials on ClinicalTrials.gov."
    )
    parser.add_argument(
        "--intervention", required=True, help="The intervention/treatment to search for."
    )
    parser.add_argument(
        "--phases",
        nargs="+",
        choices=[p.value for p in StudyPhase],
        help="One or more study phases to filter by.",
    )
    parser.add_argument(
        "--statuses",
        nargs="+",
        choices=[s.value for s in StudyStatus],
        help="One or more study statuses to filter by.",
    )
    args = parser.parse_args()

    selected_phases = [StudyPhase(p) for p in args.phases] if args.phases else None
    selected_statuses = (
        [StudyStatus(s) for s in args.statuses] if args.statuses else None
    )

    studies = search_clinical_trials(
        args.intervention, phases=selected_phases, statuses=selected_statuses
    )

    if studies is not None:
        logging.info(f"Found {len(studies)} studies matching all criteria.")

        output_dir = "data"
        os.makedirs(output_dir, exist_ok=True)
        output_filename = f"{args.intervention.replace(' ', '_')}_trials.json"
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, "w") as f:
            json.dump(studies, f, indent=2)
        logging.info(f"Search results saved to {output_path}")

if __name__ == "__main__":
    main()
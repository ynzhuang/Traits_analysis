import os
import json
import glob
from flask import Flask, jsonify
from flask_cors import CORS
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent  # Go up to criteria-analyzer root
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"
DECOMPOSED_DIR = SAMPLE_DATA_DIR / "decomposed"
OUTPUTS_DIR = BASE_DIR / "outputs"

def load_json_file(file_path):
    """Load and return JSON data from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def get_available_reviewers():
    """Get list of available reviewers from decomposed directory"""
    reviewers = []
    pattern = str(DECOMPOSED_DIR / "*.json")
    for file_path in glob.glob(pattern):
        filename = os.path.basename(file_path)
        # Extract reviewer name from filename (remove .json extension)
        reviewer_name = filename.replace('.json', '')
        reviewers.append(reviewer_name)
    return sorted(reviewers)

def get_trial_metadata():
    """Load trial metadata from sample data"""
    trial_file = SAMPLE_DATA_DIR / "ici_trials_sample.json"
    return load_json_file(trial_file)

def get_agreement_analysis():
    """Load the most recent agreement analysis file"""
    pattern = str(SAMPLE_DATA_DIR / "agreement_analysis_*.json")
    files = glob.glob(pattern)
    if not files:
        return None
    
    # Get the most recent file
    latest_file = max(files, key=os.path.getctime)
    return load_json_file(latest_file)

@app.route('/api/reviewers', methods=['GET'])
def get_reviewers():
    """Get list of available reviewers"""
    reviewers = get_available_reviewers()
    return jsonify(reviewers)

@app.route('/api/trials', methods=['GET'])
def get_trials():
    """Get list of available trials"""
    trial_data = get_trial_metadata()
    if not trial_data:
        return jsonify([])
    
    # Extract trial IDs from the metadata
    trial_ids = []
    if isinstance(trial_data, dict):
        # Handle the case where trials are nested under NCT IDs
        trial_ids = list(trial_data.keys())
    elif isinstance(trial_data, list):
        trial_ids = [trial.get('nct_id') for trial in trial_data if trial.get('nct_id')]
    
    return jsonify(trial_ids)

@app.route('/api/trials/<nct_id>', methods=['GET'])
def get_trial(nct_id):
    """Get trial metadata by NCT ID"""
    trial_data = get_trial_metadata()
    if not trial_data:
        return jsonify({'error': 'Trial metadata not found'}), 404
    
    # Find the specific trial
    trial = None
    if isinstance(trial_data, dict):
        # Handle the case where trials are nested under NCT IDs
        trial = trial_data.get(nct_id)
    elif isinstance(trial_data, list):
        trial = next((t for t in trial_data if t.get('nct_id') == nct_id), None)
    
    if not trial:
        return jsonify({'error': f'Trial {nct_id} not found'}), 404
    
    return jsonify(trial)

@app.route('/api/trials/<nct_id>/decompositions/<reviewer>', methods=['GET'])
def get_reviewer_decomposition(nct_id, reviewer):
    """Get reviewer decomposition for a specific trial"""
    file_path = DECOMPOSED_DIR / f"{reviewer}.json"
    decomposition = load_json_file(file_path)
    
    if not decomposition:
        return jsonify({'error': f'Decomposition not found for reviewer {reviewer}'}), 404
    
    # Return the specific trial data
    if nct_id in decomposition:
        return jsonify(decomposition[nct_id])
    else:
        return jsonify({'error': f'Trial {nct_id} not found in {reviewer} decomposition'}), 404

@app.route('/api/trials/<nct_id>/agreement', methods=['GET'])
def get_agreement_analysis_for_trial(nct_id):
    """Get agreement analysis for a specific trial"""
    agreement_data = get_agreement_analysis()
    if not agreement_data:
        return jsonify({'error': 'Agreement analysis not found'}), 404
    
    return jsonify(agreement_data)

@app.route('/api/trials/<nct_id>/comparison', methods=['GET'])
def get_criteria_comparison(nct_id):
    """Get complete comparison data for a trial"""
    # Load trial metadata
    trial_data = get_trial_metadata()
    if not trial_data:
        return jsonify({'error': 'Trial metadata not found'}), 404
    
    # Find the specific trial
    trial = None
    if isinstance(trial_data, dict):
        # Handle the case where trials are nested under NCT IDs
        trial = trial_data.get(nct_id)
    elif isinstance(trial_data, list):
        trial = next((t for t in trial_data if t.get('nct_id') == nct_id), None)
    
    if not trial:
        return jsonify({'error': f'Trial {nct_id} not found'}), 404
    
    # Get available reviewers
    reviewers = get_available_reviewers()
    
    # Load decompositions for all reviewers
    decompositions = {}
    for reviewer in reviewers:
        file_path = DECOMPOSED_DIR / f"{reviewer}.json"
        decomposition = load_json_file(file_path)
        if decomposition:
            decompositions[reviewer] = decomposition
    
    # Load agreement analysis
    agreement = get_agreement_analysis()
    if not agreement:
        return jsonify({'error': 'Agreement analysis not found'}), 404
    
    return jsonify({
        'trial': trial,
        'reviewers': reviewers,
        'decompositions': decompositions,
        'agreement': agreement
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Clinical Trial Criteria Decomposition API is running'
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print(f"Base directory: {BASE_DIR}")
    print(f"Sample data directory: {SAMPLE_DATA_DIR}")
    print(f"Decomposed directory: {DECOMPOSED_DIR}")
    print(f"Outputs directory: {OUTPUTS_DIR}")
    
    # Check if directories exist
    if not SAMPLE_DATA_DIR.exists():
        print(f"Warning: Sample data directory not found: {SAMPLE_DATA_DIR}")
    if not DECOMPOSED_DIR.exists():
        print(f"Warning: Decomposed directory not found: {DECOMPOSED_DIR}")
    if not OUTPUTS_DIR.exists():
        print(f"Warning: Outputs directory not found: {OUTPUTS_DIR}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
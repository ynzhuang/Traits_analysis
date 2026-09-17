"""
Test script for analyze_criteria_decomposition_agreement.py

This test script validates the functionality of the analyze_criteria_decomposition_agreement.py script
using the refactored service layer architecture.
"""

import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze_criteria_decomposition_agreement import (
    main, load_decomposed_files, normalize_trait, calculate_semantic_similarity,
    match_traits, calculate_agreement_metrics, classify_discrepancy,
    calculate_fleiss_kappa, analyze_agreement_with_llm, generate_markdown_report,
)
from services.api_key_service import APIKeyService
from services.llm_service import LLMService
from services.prompt_service import PromptService
from services.cache_service import CacheService
from services.chain_service import ChainService


class TestAnalyzeCriteriaDecompositionAgreement(unittest.TestCase):
    """Test cases for analyze_criteria_decomposition_agreement.py functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create test data
        self.test_prompt = "Test agreement analysis prompt with {input_data}"
        self.test_api_keys = {
            "gemini": "test_api_key",
            "gemini_model": "gemini-2.5-pro"
        }
        
        # Sample decomposed data for testing
        self.test_decomposed_data = {
            "gemini-gemini-2.5-pro": {
                "NCT12345": {
                    "trial_id": "NCT12345",
                    "criteria": [
                        {
                            "type": "inclusion",
                            "original_text": "Age >= 18 years",
                            "logic": "age >= 18",
                            "traits": [
                                {
                                    "trait": "Age",
                                    "category": "Demographics",
                                    "value": ">= 18 years"
                                }
                            ]
                        },
                        {
                            "type": "inclusion",
                            "original_text": "ECOG performance status 0-1",
                            "logic": "ECOG IN [0, 1]",
                            "traits": [
                                {
                                    "trait": "ECOG Performance Status",
                                    "category": "Performance Status/Functional Status",
                                    "value": "0-1"
                                }
                            ]
                        }
                    ]
                }
            },
            "openai-gpt-4o": {
                "NCT12345": {
                    "trial_id": "NCT12345",
                    "criteria": [
                        {
                            "type": "inclusion",
                            "original_text": "Age >= 18 years",
                            "logic": "age >= 18",
                            "traits": [
                                {
                                    "trait": "Age",
                                    "category": "Demographics",
                                    "value": ">= 18"
                                }
                            ]
                        },
                        {
                            "type": "inclusion",
                            "original_text": "ECOG performance status 0-1",
                            "logic": "ECOG IN [0, 1]",
                            "traits": [
                                {
                                    "trait": "Performance Status",
                                    "category": "Performance Status",
                                    "value": "ECOG 0-1"
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        # Create test files
        self.prompt_file = os.path.join(self.test_dir, "test_prompt.md")
        self.api_keys_file = os.path.join(self.test_dir, "test_api_keys.json")
        self.input_dir = os.path.join(self.test_dir, "decomposed")
        self.output_dir = os.path.join(self.test_dir, "outputs")
        
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        with open(self.prompt_file, 'w') as f:
            f.write(self.test_prompt)
        
        with open(self.api_keys_file, 'w') as f:
            json.dump(self.test_api_keys, f)
        
        # Create test decomposed files
        for reviewer, data in self.test_decomposed_data.items():
            file_path = os.path.join(self.input_dir, f"ici_criteria_sample-{reviewer}-20250704_173147.json")
            with open(file_path, 'w') as f:
                json.dump(data, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    
    def test_load_decomposed_files(self):
        """Test loading decomposed files from directory."""
        decomposed_data = load_decomposed_files(self.input_dir)
        
        self.assertEqual(len(decomposed_data), 2)
        # The actual keys depend on the filename parsing logic
        # Check that we have the expected number of reviewers
        reviewer_names = list(decomposed_data.keys())
        self.assertEqual(len(reviewer_names), 2)
        
        # Check that each reviewer has the expected data structure
        for reviewer_name, data in decomposed_data.items():
            self.assertIn("NCT12345", data)
            self.assertIn("criteria", data["NCT12345"])
        
        # Test file not found error
        with self.assertRaises(FileNotFoundError):
            load_decomposed_files("nonexistent_dir")
        
        # Test no JSON files error
        empty_dir = os.path.join(self.test_dir, "empty")
        os.makedirs(empty_dir, exist_ok=True)
        with self.assertRaises(ValueError):
            load_decomposed_files(empty_dir)
    
    def test_normalize_trait(self):
        """Test trait normalization function."""
        trait = {
            "trait": "  Age  ",
            "category": "DEMOGRAPHICS",
            "value": ">= 18 Years"
        }
        
        normalized = normalize_trait(trait)
        expected = ("age", "demographics", ">= 18 years")
        self.assertEqual(normalized, expected)
    
    def test_calculate_semantic_similarity(self):
        """Test semantic similarity calculation."""
        trait1 = {
            "trait": "Age",
            "category": "Demographics",
            "value": ">= 18 years"
        }
        trait2 = {
            "trait": "Age",
            "category": "Demographics",
            "value": ">= 18"
        }
        
        similarity = calculate_semantic_similarity(trait1, trait2)
        self.assertGreater(similarity, 0.8)  # Should be high similarity
        
        # Test different traits
        trait3 = {
            "trait": "Performance Status",
            "category": "Performance",
            "value": "ECOG 0-1"
        }
        
        similarity_low = calculate_semantic_similarity(trait1, trait3)
        self.assertLess(similarity_low, 0.5)  # Should be low similarity
    
    def test_match_traits(self):
        """Test trait matching function."""
        traits1 = [
            {"trait": "Age", "category": "Demographics", "value": ">= 18 years"},
            {"trait": "ECOG Performance Status", "category": "Performance Status", "value": "0-1"}
        ]
        traits2 = [
            {"trait": "Age", "category": "Demographics", "value": ">= 18"},
            {"trait": "Performance Status", "category": "Performance", "value": "ECOG 0-1"}
        ]
        
        matches, unmatched_1, unmatched_2 = match_traits(traits1, traits2, threshold=0.7)
        
        self.assertEqual(len(matches), 2)  # Both should match with lower threshold
        self.assertEqual(len(unmatched_1), 0)
        self.assertEqual(len(unmatched_2), 0)
    
    def test_calculate_agreement_metrics(self):
        """Test agreement metrics calculation."""
        matches = [("trait1", "trait1"), ("trait2", "trait2")]
        unmatched_1 = [{"trait": "trait3"}]
        unmatched_2 = [{"trait": "trait4"}]
        
        metrics = calculate_agreement_metrics(matches, unmatched_1, unmatched_2)
        
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)
        self.assertIn('f1_score', metrics)
        self.assertIn('jaccard_index', metrics)
        self.assertIn('cohen_kappa', metrics)
        
        # Check calculations
        expected_precision = 2 / (2 + 1)  # TP / (TP + FP)
        expected_recall = 2 / (2 + 1)     # TP / (TP + FN)
        
        self.assertAlmostEqual(metrics['precision'], expected_precision, places=3)
        self.assertAlmostEqual(metrics['recall'], expected_recall, places=3)
    
    def test_classify_discrepancy(self):
        """Test discrepancy classification."""
        trait1 = {"trait": "Age", "category": "Demographics", "value": ">= 18"}
        trait2 = {"trait": "Age", "category": "Patient Info", "value": ">= 18"}
        
        match_status, explanation = classify_discrepancy(trait1, trait2)
        self.assertEqual(match_status, "category_mismatch")
        
        # Test missing trait
        match_status, explanation = classify_discrepancy(trait1, {}, is_missing=True)
        self.assertEqual(match_status, "missing_in_reviewer_2")
    
    
    
    
    
    


class TestIntegrationWithRealFiles(unittest.TestCase):
    """Integration tests using actual project files."""
    
    def setUp(self):
        """Set up for integration tests."""
        self.project_root = Path(__file__).parent.parent
        self.prompt_file = self.project_root / "prompts" / "study_trait_n_reviewer_agreement_prompt.md"
        self.input_dir = self.project_root / "sample_data" / "decomposed"
        self.output_dir = self.project_root / "outputs"
    
    def test_file_existence(self):
        """Test that required test files exist."""
        self.assertTrue(self.prompt_file.exists(), f"Prompt file not found: {self.prompt_file}")
        self.assertTrue(self.input_dir.exists(), f"Input directory not found: {self.input_dir}")
        
        # Check for decomposed files
        json_files = list(self.input_dir.glob("*.json"))
        self.assertGreater(len(json_files), 0, f"No JSON files found in {self.input_dir}")
    
    def test_file_content_validity(self):
        """Test that test files contain valid content."""
        # Test prompt file
        with open(self.prompt_file, 'r') as f:
            prompt_content = f.read()
        self.assertGreater(len(prompt_content), 0, "Prompt file is empty")
        self.assertIn("agreement", prompt_content.lower(), "Prompt should mention agreement")
        
        # Test decomposed files
        json_files = list(self.input_dir.glob("*.json"))
        for json_file in json_files[:2]:  # Test first 2 files
            with open(json_file, 'r') as f:
                data = json.load(f)
            self.assertIsInstance(data, dict, f"File {json_file} should contain a dictionary")
            
            # Check structure
            for trial_id, trial_data in data.items():
                self.assertIn("criteria", trial_data, f"Trial {trial_id} should have criteria")
                self.assertIsInstance(trial_data["criteria"], list, "Criteria should be a list")
                
                for criterion in trial_data["criteria"]:
                    self.assertIn("traits", criterion, "Criterion should have traits")
                    self.assertIsInstance(criterion["traits"], list, "Traits should be a list")


def run_integration_test():
    """
    Run an integration test that simulates the actual command:
    python analyze_criteria_decomposition_agreement.py --input-dir sample_data/decomposed/ 
    --output outputs/ --prompt prompts/study_trait_n_reviewer_agreement_prompt.md 
    --api-keys api_keys.json --model gemini
    """
    print("=" * 60)
    print("INTEGRATION TEST: analyze_criteria_decomposition_agreement.py")
    print("=" * 60)
    
    # Check if required files exist
    project_root = Path(__file__).parent.parent
    prompt_file = project_root / "prompts" / "study_trait_n_reviewer_agreement_prompt.md"
    input_dir = project_root / "sample_data" / "decomposed"
    output_dir = project_root / "outputs"
    api_keys_file = project_root / "api_keys.json"
    
    print(f"Checking required files:")
    print(f"  ✓ Prompt file: {prompt_file.exists()} - {prompt_file}")
    print(f"  ✓ Input directory: {input_dir.exists()} - {input_dir}")
    print(f"  ✓ Output directory: {output_dir.exists()} - {output_dir}")
    print(f"  ✓ API keys file: {api_keys_file.exists()} - {api_keys_file}")
    
    if not all([prompt_file.exists(), input_dir.exists()]):
        print("\n❌ Required test files are missing. Cannot run integration test.")
        return False
    
    # Check for decomposed files
    json_files = list(input_dir.glob("*.json"))
    if len(json_files) < 2:
        print(f"\n❌ Need at least 2 decomposed files for agreement analysis. Found {len(json_files)}")
        return False
    
    print(f"  ✓ Found {len(json_files)} decomposed files")
    
    if not api_keys_file.exists():
        print(f"\n⚠️  API keys file not found: {api_keys_file}")
        print("   Create this file with your API keys to run the full integration test.")
        print("   For now, running local-only integration test...")
        
        # Run local-only test
        return run_local_integration_test()
    
    print(f"\n🚀 Running integration test with actual files...")
    
    # Import and run the actual script
    try:
        import subprocess
        import sys
        
        cmd = [
            sys.executable, 
            str(project_root / "analyze_criteria_decomposition_agreement.py"),
            "--input-dir", str(input_dir),
            "--output", str(output_dir),
            "--prompt", str(prompt_file),
            "--api-keys", str(api_keys_file),
            "--model", "gemini",
            "--no-cache"  # Disable cache for testing
        ]
        
        print(f"Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Integration test PASSED")
            print(f"Output: {result.stdout}")
            return True
        else:
            print("❌ Integration test FAILED")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Integration test TIMED OUT (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Integration test ERROR: {e}")
        return False


def run_local_integration_test():
    """Run integration test with local-only analysis."""
    print("\n🔧 Running local-only integration test...")
    
    try:
        import subprocess
        import sys
        
        project_root = Path(__file__).parent.parent
        
        cmd = [
            sys.executable,
            str(project_root / "analyze_criteria_decomposition_agreement.py"),
            "--input-dir", str(project_root / "sample_data" / "decomposed"),
            "--output", str(project_root / "outputs"),
            "--local-only"
        ]
        
        print(f"Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Local integration test PASSED")
            print(f"Output: {result.stdout}")
            return True
        else:
            print("❌ Local integration test FAILED")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Local integration test TIMED OUT (2 minutes)")
        return False
    except Exception as e:
        print(f"❌ Local integration test ERROR: {e}")
        return False


def run_mock_integration_test():
    """Run integration test with mocked LLM calls."""
    print("\n🔧 Running mock integration test...")
    
    try:
        # This would use the unit test framework with mocks
        suite = unittest.TestLoader().loadTestsFromTestCase(TestAnalyzeCriteriaDecompositionAgreement)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        if result.wasSuccessful():
            print("✅ Mock integration test PASSED")
            return True
        else:
            print("❌ Mock integration test FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Mock integration test ERROR: {e}")
        return False


if __name__ == '__main__':
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run integration test
    print("\n" + "=" * 60)
    run_integration_test()
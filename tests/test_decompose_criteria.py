"""
Test script for decompose_criteria.py

This test script validates the functionality of the decompose_criteria.py script
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

from decompose_criteria import main
from schemas import Trait, Criterion, Trial, DecomposedCriteria
from services.api_key_service import APIKeyService
from services.llm_service import LLMService
from services.prompt_service import PromptService
from services.cache_service import CacheService
from services.chain_service import ChainService


class TestDecomposeCriteria(unittest.TestCase):
    """Test cases for decompose_criteria.py functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create test data
        self.test_prompt = "Test prompt template with {variable}"
        self.test_criteria = {
            "NCT12345": "Age >= 18 years; ECOG performance status 0-1",
            "NCT67890": "Histologically confirmed cancer; No prior therapy"
        }
        self.test_api_keys = {
            "gemini": "test_api_key",
            "gemini_model": "gemini-2.5-pro"
        }
        
        # Create test files
        self.prompt_file = os.path.join(self.test_dir, "test_prompt.md")
        self.criteria_file = os.path.join(self.test_dir, "test_criteria.json")
        self.api_keys_file = os.path.join(self.test_dir, "test_api_keys.json")
        
        with open(self.prompt_file, 'w') as f:
            f.write(self.test_prompt)
        
        with open(self.criteria_file, 'w') as f:
            json.dump(self.test_criteria, f)
        
        with open(self.api_keys_file, 'w') as f:
            json.dump(self.test_api_keys, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def test_pydantic_models(self):
        """Test that Pydantic models are properly defined."""
        # Test Trait model
        trait = Trait(
            trait="age",
            category="demographic",
            value=">=18",
            source_text="Patients must be 18 years of age or older",
            original_trait_phrase="18 years of age or older",
            original_value_phrase=">=18"
        )
        self.assertEqual(trait.trait, "age")
        self.assertEqual(trait.category, "demographic")
        self.assertEqual(trait.value, ">=18")
        self.assertEqual(trait.source_text, "Patients must be 18 years of age or older")
        self.assertEqual(trait.original_trait_phrase, "18 years of age or older")
        self.assertEqual(trait.original_value_phrase, ">=18")
        
        # Test Criterion model
        criterion = Criterion(
            type="inclusion",
            original_text="Age >= 18 years",
            logic="age >= 18",
            traits=[trait]
        )
        self.assertEqual(criterion.type, "inclusion")
        self.assertEqual(len(criterion.traits), 1)
        
        # Test DecomposedCriteria model
        decomposed = DecomposedCriteria(
            trial=Trial(trial_id="NCT12345"),
            criteria=[criterion]
        )
        self.assertEqual(decomposed.trial.trial_id, "NCT12345")
        self.assertEqual(len(decomposed.criteria), 1)
    
    @patch('decompose_criteria.ChainService')
    @patch('decompose_criteria.LLMService')
    @patch('decompose_criteria.PromptService')
    @patch('decompose_criteria.CacheService')
    @patch('decompose_criteria.APIKeyService')
    @patch('json.load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    @patch('json.dump')
    def test_service_integration(self, mock_json_dump, mock_makedirs, mock_file_open,
                                mock_json_load, mock_api_service, mock_cache_service,
                                mock_prompt_service, mock_llm_service, mock_chain_service):
        """Test that services are properly integrated."""
        
        # Mock file loading
        mock_json_load.return_value = self.test_criteria
        
        # Mock service responses
        mock_api_service.load_api_keys.return_value = self.test_api_keys
        mock_api_service.add_model_override.return_value = self.test_api_keys
        mock_prompt_service.load_prompt_template.return_value = self.test_prompt
        mock_prompt_service.prepare_prompt_for_provider.return_value = MagicMock()
        
        mock_llm = MagicMock()
        mock_llm_service.get_llm.return_value = (mock_llm, "gemini-2.5-pro")
        
        mock_chain = MagicMock()
        mock_chain_service.create_chain.return_value = mock_chain
        
        # Mock chain result
        mock_result = DecomposedCriteria(
            trial=Trial(trial_id="NCT12345"),
            criteria=[
                Criterion(
                    type="inclusion",
                    original_text="Age >= 18 years",
                    logic="age >= 18",
                    traits=[
                        Trait(trait="age", category="demographic", value=">=18",
                              source_text="Patients must be 18 years of age or older",
                              original_trait_phrase="18 years of age or older",
                              original_value_phrase=">=18")
                    ]
                )
            ]
        )
        mock_chain_service.invoke_chain.return_value = (mock_result, 1.5)
        
        # Test arguments
        test_args = [
            'decompose_criteria.py',
            '--prompt', self.prompt_file,
            '--criteria', self.criteria_file,
            '--api-keys', self.api_keys_file,
            '--model', 'gemini'
        ]
        
        with patch('sys.argv', test_args):
            main()
        
        # Verify service calls
        mock_api_service.load_api_keys.assert_called_once_with(self.api_keys_file)
        mock_prompt_service.load_prompt_template.assert_called_once_with(self.prompt_file)
        mock_cache_service.setup_cache.assert_called_once_with(True)
        mock_llm_service.get_llm.assert_called_once_with('gemini', self.test_api_keys, DecomposedCriteria)
        mock_chain_service.create_chain.assert_called_once()
        
        # Verify chain was invoked for each trial
        self.assertEqual(mock_chain_service.invoke_chain.call_count, 2)
    
    @patch('sys.argv')
    @patch('decompose_criteria.ChainService')
    @patch('decompose_criteria.LLMService')
    @patch('decompose_criteria.PromptService')
    @patch('decompose_criteria.CacheService')
    @patch('decompose_criteria.APIKeyService')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('os.makedirs')
    def test_main_function_integration(self, mock_makedirs, mock_json_dump, mock_file_open,
                                     mock_api_service, mock_cache_service, mock_prompt_service,
                                     mock_llm_service, mock_chain_service, mock_argv):
        """Test the main function with realistic test case."""
        
        # Set up command line arguments
        mock_argv.__getitem__.side_effect = lambda x: [
            'decompose_criteria.py',
            '--prompt', './prompts/ici_trial_eligibility_criteria_decompose_prompt.md',
            '--criteria', './sample_data/ici_criteria_sample.json',
            '--api-keys', 'api_keys.json',
            '--model', 'gemini'
        ][x]
        mock_argv.__len__.return_value = 5
        
        # Mock file reading for criteria
        criteria_data = json.dumps(self.test_criteria)
        mock_file_open.return_value.read.return_value = criteria_data
        
        # Mock services
        mock_api_service.load_api_keys.return_value = self.test_api_keys
        mock_prompt_service.load_prompt_template.return_value = self.test_prompt
        mock_prompt_service.prepare_prompt_for_provider.return_value = MagicMock()
        
        mock_llm = MagicMock()
        mock_llm_service.get_llm.return_value = (mock_llm, "gemini-2.5-pro")
        
        mock_chain = MagicMock()
        mock_chain_service.create_chain.return_value = mock_chain
        
        # Mock successful decomposition result
        mock_result = DecomposedCriteria(
            trial=Trial(trial_id="NCT12345"),
            criteria=[
                Criterion(
                    type="inclusion",
                    original_text="Age >= 18 years",
                    logic="age >= 18",
                    traits=[
                        Trait(trait="age", category="demographic", value=">=18",
                              source_text="Patients must be 18 years of age or older",
                              original_trait_phrase="18 years of age or older",
                              original_value_phrase=">=18")
                    ]
                )
            ]
        )
        mock_chain_service.invoke_chain.return_value = (mock_result, 2.1)
        
        # Mock json.load for criteria file
        with patch('json.load', return_value=self.test_criteria):
            main()
        
        # Verify all services were called
        mock_api_service.load_api_keys.assert_called()
        mock_prompt_service.load_prompt_template.assert_called()
        mock_cache_service.setup_cache.assert_called()
        mock_llm_service.get_llm.assert_called()
        mock_chain_service.create_chain.assert_called()
        
        # Verify output directory creation and file writing
        mock_makedirs.assert_called()
        mock_json_dump.assert_called()
    
    def test_error_handling(self):
        """Test error handling for various failure scenarios."""
        
        # Test missing prompt file
        with patch('sys.argv', [
            'decompose_criteria.py',
            '--prompt', 'nonexistent.md',
            '--criteria', self.criteria_file,
            '--api-keys', self.api_keys_file,
            '--model', 'gemini'
        ]):
            with patch('decompose_criteria.PromptService.load_prompt_template', 
                      side_effect=FileNotFoundError("Prompt file not found")):
                with self.assertLogs(level='ERROR') as log:
                    main()
                self.assertTrue(any('An error occurred' in message for message in log.output))
        
        # Test missing criteria file
        with patch('sys.argv', [
            'decompose_criteria.py',
            '--prompt', self.prompt_file,
            '--criteria', 'nonexistent.json',
            '--api-keys', self.api_keys_file,
            '--model', 'gemini'
        ]):
            with patch('decompose_criteria.PromptService.load_prompt_template', 
                      return_value=self.test_prompt):
                with self.assertLogs(level='ERROR') as log:
                    main()
                self.assertTrue(any('An error occurred' in message for message in log.output))
        
        # Test missing API keys file
        with patch('sys.argv', [
            'decompose_criteria.py',
            '--prompt', self.prompt_file,
            '--criteria', self.criteria_file,
            '--api-keys', 'nonexistent.json',
            '--model', 'gemini'
        ]):
            with patch('decompose_criteria.PromptService.load_prompt_template', 
                      return_value=self.test_prompt):
                with patch('json.load', return_value=self.test_criteria):
                    with patch('decompose_criteria.APIKeyService.load_api_keys',
                              side_effect=FileNotFoundError("API keys file not found")):
                        with self.assertLogs(level='ERROR') as log:
                            main()
                        self.assertTrue(any('An error occurred' in message for message in log.output))


class TestIntegrationWithRealFiles(unittest.TestCase):
    """Integration tests using actual project files."""
    
    def setUp(self):
        """Set up for integration tests."""
        self.project_root = Path(__file__).parent.parent
        self.prompt_file = self.project_root / "prompts" / "ici_trial_eligibility_criteria_decompose_prompt.md"
        self.criteria_file = self.project_root / "sample_data" / "ici_criteria_sample.json"
    
    def test_file_existence(self):
        """Test that required test files exist."""
        self.assertTrue(self.prompt_file.exists(), f"Prompt file not found: {self.prompt_file}")
        self.assertTrue(self.criteria_file.exists(), f"Criteria file not found: {self.criteria_file}")
    
    def test_file_content_validity(self):
        """Test that test files contain valid content."""
        # Test prompt file
        with open(self.prompt_file, 'r') as f:
            prompt_content = f.read()
        self.assertGreater(len(prompt_content), 0, "Prompt file is empty")
        
        # Test criteria file
        with open(self.criteria_file, 'r') as f:
            criteria_data = json.load(f)
        self.assertIsInstance(criteria_data, dict, "Criteria file should contain a dictionary")
        self.assertGreater(len(criteria_data), 0, "Criteria file should not be empty")
        
        # Verify criteria structure
        for trial_id, criteria_text in criteria_data.items():
            self.assertIsInstance(trial_id, str, "Trial ID should be a string")
            self.assertIsInstance(criteria_text, str, "Criteria text should be a string")
            self.assertGreater(len(criteria_text), 0, "Criteria text should not be empty")


def run_integration_test():
    """
    Run an integration test that simulates the actual command:
    python decompose_criteria.py --prompt ./prompts/ici_trial_eligibility_criteria_decompose_prompt.md 
    --criteria ./sample_data/ici_criteria_sample.json --api-keys api_keys.json --model gemini
    """
    print("=" * 60)
    print("INTEGRATION TEST: decompose_criteria.py")
    print("=" * 60)
    
    # Check if required files exist
    project_root = Path(__file__).parent.parent
    prompt_file = project_root / "prompts" / "ici_trial_eligibility_criteria_decompose_prompt.md"
    criteria_file = project_root / "sample_data" / "ici_criteria_sample.json"
    api_keys_file = project_root / "api_keys.json"
    
    print(f"Checking required files:")
    print(f"  ✓ Prompt file: {prompt_file.exists()} - {prompt_file}")
    print(f"  ✓ Criteria file: {criteria_file.exists()} - {criteria_file}")
    print(f"  ✓ API keys file: {api_keys_file.exists()} - {api_keys_file}")
    
    if not all([prompt_file.exists(), criteria_file.exists()]):
        print("\n❌ Required test files are missing. Cannot run integration test.")
        return False
    
    if not api_keys_file.exists():
        print(f"\n⚠️  API keys file not found: {api_keys_file}")
        print("   Create this file with your API keys to run the full integration test.")
        print("   For now, running mock integration test...")
        
        # Run mock test
        return run_mock_integration_test()
    
    print(f"\n🚀 Running integration test with actual files...")
    
    # Import and run the actual script
    try:
        import subprocess
        import sys
        
        cmd = [
            sys.executable, 
            str(project_root / "decompose_criteria.py"),
            "--prompt", str(prompt_file),
            "--criteria", str(criteria_file),
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


def run_mock_integration_test():
    """Run integration test with mocked LLM calls."""
    print("\n🔧 Running mock integration test...")
    
    try:
        # This would use the unit test framework with mocks
        suite = unittest.TestLoader().loadTestsFromTestCase(TestDecomposeCriteria)
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
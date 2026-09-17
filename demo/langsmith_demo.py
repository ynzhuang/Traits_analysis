"""
Demo script showing LangSmith integration with the criteria analyzer.
"""

import sys
import os
import logging

# Add the parent directory to the path so we can import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.api_key_service import APIKeyService
from services.langsmith_service import LangSmithService
from services.llm_service import LLMService
from services.chain_service import ChainService
from services.prompt_service import PromptService
from pydantic import BaseModel
from typing import List


class CriteriaAnalysis(BaseModel):
    """Example structured output for criteria analysis."""
    criteria_count: int
    complexity_score: int
    key_requirements: List[str]
    analysis_summary: str


def main():
    """Demonstrate LangSmith integration."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load API keys
        api_keys = APIKeyService.load_api_keys()
        
        # Configure LangSmith tracing
        langsmith_configured = LangSmithService.configure_tracing(api_keys)
        
        if langsmith_configured:
            print("✅ LangSmith tracing configured successfully!")
            LangSmithService.log_debug_info()
        else:
            print("⚠️  LangSmith not configured - continuing without tracing")
        
        # Initialize LLM (this will automatically enable LangSmith tracing if configured)
        provider = "claude"  # You can change this to test different providers
        llm, model_name = LLMService.get_llm(
            provider_name=provider,
            api_keys=api_keys,
            structured_output_class=CriteriaAnalysis,
            temperature=0.1
        )
        
        print(f"✅ Initialized {provider} model: {model_name}")
        
        # Create a simple prompt for testing
        prompt_template = """
        Analyze the following clinical trial eligibility criteria:
        
        Criteria: {criteria_text}
        
        Provide a structured analysis including:
        - Count of individual criteria
        - Complexity score (1-10)
        - Key requirements
        - Summary of the analysis
        """
        
        prompt = PromptService.create_chat_prompt(prompt_template)
        
        # Create chain
        chain = ChainService.create_chain(prompt, llm)
        
        # Test data
        test_criteria = """
        Inclusion Criteria:
        1. Age 18-65 years
        2. Confirmed diagnosis of Type 2 diabetes
        3. HbA1c between 7.0% and 10.0%
        4. Stable medication regimen for at least 3 months
        
        Exclusion Criteria:
        1. Pregnancy or nursing
        2. Severe kidney disease (eGFR < 30)
        3. History of diabetic ketoacidosis
        """
        
        # Invoke chain with LangSmith tracing
        print("\n🔄 Running criteria analysis with LangSmith tracing...")
        
        result, duration = ChainService.invoke_chain(
            chain=chain,
            input_data={"criteria_text": test_criteria},
            retry_count=2,
            operation_name="Criteria Analysis Demo"
        )
        
        print(f"\n✅ Analysis completed in {duration:.2f} seconds")
        print(f"📊 Results:")
        print(f"   - Criteria Count: {result.criteria_count}")
        print(f"   - Complexity Score: {result.complexity_score}/10")
        print(f"   - Key Requirements: {', '.join(result.key_requirements)}")
        print(f"   - Summary: {result.analysis_summary}")
        
        if LangSmithService.is_tracing_enabled():
            project_name = LangSmithService.get_project_name()
            print(f"\n🔍 Check your LangSmith dashboard for detailed traces:")
            print(f"   Project: {project_name}")
            print(f"   URL: https://smith.langchain.com/")
        
    except Exception as e:
        logging.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
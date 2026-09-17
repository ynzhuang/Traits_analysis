"""
Prompt Service for managing prompt templates and processing.
"""

import logging
from typing import Dict, Any, Union, List
from langchain_core.prompts import ChatPromptTemplate


class PromptService:
    """Service for managing prompt templates and processing."""
    
    @staticmethod
    def load_prompt_template(prompt_file: str) -> str:
        """
        Load a prompt template from a file.
        
        Args:
            prompt_file: Path to the prompt template file
            
        Returns:
            Content of the prompt template
            
        Raises:
            FileNotFoundError: If the prompt file doesn't exist
        """
        logging.info(f"Reading prompt template from {prompt_file}")
        try:
            with open(prompt_file, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logging.error(f"Prompt template file not found: {prompt_file}")
            raise
    
    @staticmethod
    def escape_template_braces(template: str) -> str:
        """
        Escape curly braces in template to prevent LangChain from treating them as variables.
        
        Args:
            template: Template string to escape
            
        Returns:
            Escaped template string
        """
        return template.replace("{", "{{").replace("}", "}}")
    
    @staticmethod
    def restore_template_variables(template: str, variables: List[str]) -> str:
        """
        Restore specific template variables after escaping.
        
        Args:
            template: Escaped template string
            variables: List of variable names to restore (e.g., ['input_data', 'criteria'])
            
        Returns:
            Template with specified variables restored
        """
        for var in variables:
            escaped_var = "{{" + var + "}}"
            restored_var = "{" + var + "}"
            template = template.replace(escaped_var, restored_var)
        return template
    
    @staticmethod
    def create_claude_cache_control_prompt(template: str) -> List[Dict[str, Any]]:
        """
        Create a Claude-specific prompt with cache control.
        
        Args:
            template: Prompt template string
            
        Returns:
            List containing prompt with cache control metadata
        """
        return [
            {
                "type": "text",
                "text": template,
                "cache_control": {"type": "ephemeral"}
            }
        ]
    
    @staticmethod
    def create_chat_prompt_template(
        system_prompt: Union[str, List[Dict[str, Any]]], 
        human_template: str,
        escape_braces: bool = True,
        template_variables: List[str] = None
    ) -> ChatPromptTemplate:
        """
        Create a ChatPromptTemplate with proper escaping and variable handling.
        
        Args:
            system_prompt: System prompt (string or Claude cache control format)
            human_template: Human message template
            escape_braces: Whether to escape curly braces
            template_variables: List of variables to preserve after escaping
            
        Returns:
            Configured ChatPromptTemplate
        """
        if escape_braces and isinstance(system_prompt, str):
            escaped_system = PromptService.escape_template_braces(system_prompt)
            if template_variables:
                escaped_system = PromptService.restore_template_variables(escaped_system, template_variables)
            system_prompt = escaped_system
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_template)
        ])
    
    @staticmethod
    def prepare_prompt_for_provider(
        template: str, 
        provider: str, 
        human_template: str,
        template_variables: List[str] = None
    ) -> ChatPromptTemplate:
        """
        Prepare a prompt template for a specific provider with appropriate formatting.
        
        Args:
            template: Raw prompt template
            provider: Provider name ('claude', 'openai', 'gemini')
            human_template: Human message template
            template_variables: Variables to preserve in template
            
        Returns:
            Configured ChatPromptTemplate
        """

        return PromptService.create_chat_prompt_template(
            template, 
            human_template, 
            escape_braces=True,
            template_variables=template_variables
        )
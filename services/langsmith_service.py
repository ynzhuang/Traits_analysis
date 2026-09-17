"""
LangSmith Service for debugging and tracing LLM operations.
"""

import os
import logging
from typing import Dict, Any, Optional
from contextlib import contextmanager


class LangSmithService:
    """Service for configuring and managing LangSmith tracing."""
    
    @classmethod
    def configure_tracing(
        cls, 
        api_keys: Dict[str, Any], 
        project_name: Optional[str] = None,
        enable_tracing: bool = True
    ) -> bool:
        """
        Configure LangSmith tracing environment variables.
        
        Args:
            api_keys: Dictionary containing API keys and configuration
            project_name: Optional project name for LangSmith (defaults to "criteria-analyzer")
            enable_tracing: Whether to enable tracing
            
        Returns:
            True if LangSmith is configured, False otherwise
        """
        try:
            # Check if LangSmith API key is available
            langsmith_config = api_keys.get('langsmith', {})
            if not langsmith_config or not langsmith_config.get('api-key'):
                logging.warning("LangSmith API key not found in api_keys. Tracing will be disabled.")
                return False
            
            # Set LangSmith environment variables
            os.environ["LANGSMITH_TRACING"] = str(enable_tracing).lower()
            os.environ["LANGSMITH_ENDPOINT"] = langsmith_config.get('endpoint', 'https://api.smith.langchain.com')
            os.environ["LANGSMITH_API_KEY"] = langsmith_config.get('api-key')
            
            # Set project name
            project = project_name or langsmith_config.get('project', 'criteria-analyzer')
            os.environ["LANGSMITH_PROJECT"] = project
            
            if enable_tracing:
                logging.info(f"LangSmith tracing enabled for project: {project}")
                logging.info(f"LangSmith endpoint: {os.environ['LANGSMITH_ENDPOINT']}")
            else:
                logging.info("LangSmith tracing disabled")
                
            return True
            
        except Exception as e:
            logging.error(f"Failed to configure LangSmith: {e}")
            return False
    
    @classmethod
    def is_tracing_enabled(cls) -> bool:
        """
        Check if LangSmith tracing is currently enabled.
        
        Returns:
            True if tracing is enabled, False otherwise
        """
        return os.environ.get("LANGSMITH_TRACING", "false").lower() == "true"
    
    @classmethod
    def get_project_name(cls) -> Optional[str]:
        """
        Get the current LangSmith project name.
        
        Returns:
            Project name if set, None otherwise
        """
        return os.environ.get("LANGSMITH_PROJECT")
    
    @classmethod
    @contextmanager
    def trace_context(cls, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for manual tracing of operations.
        
        Args:
            operation_name: Name of the operation being traced
            metadata: Optional metadata to include in the trace
        """
        if not cls.is_tracing_enabled():
            yield
            return
            
        try:
            # Import here to avoid dependency issues if langsmith not installed
            from langsmith.run_trees import RunTree
            
            # Create a run tree for manual tracing
            run = RunTree(
                name=operation_name,
                run_type="chain",
                inputs=metadata or {},
            )
            run.post()
            
            try:
                yield run
                run.end(outputs={"status": "completed"})
            except Exception as e:
                run.end(error=str(e))
                raise
            finally:
                run.patch()
                
        except ImportError:
            logging.warning("LangSmith SDK not installed. Manual tracing unavailable.")
            yield
        except Exception as e:
            logging.error(f"Error in trace context: {e}")
            yield
    
    @classmethod
    def log_debug_info(cls) -> None:
        """Log current LangSmith configuration for debugging."""
        logging.info("=== LangSmith Configuration ===")
        logging.info(f"Tracing Enabled: {cls.is_tracing_enabled()}")
        logging.info(f"Project Name: {cls.get_project_name()}")
        logging.info(f"Endpoint: {os.environ.get('LANGSMITH_ENDPOINT', 'Not set')}")
        logging.info(f"API Key Set: {'Yes' if os.environ.get('LANGSMITH_API_KEY') else 'No'}")
        logging.info("==============================")
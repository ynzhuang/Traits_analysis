"""
Chain Service for creating and managing LangChain chains.
"""

import logging
import time
from typing import Any, Dict, Optional, Callable
from langchain_core.prompts import ChatPromptTemplate
from .langsmith_service import LangSmithService


class ChainService:
    """Service for creating and managing LangChain chains."""
    
    @staticmethod
    def create_chain(prompt: ChatPromptTemplate, llm: Any) -> Any:
        """
        Create a chain from a prompt and LLM.
        
        Args:
            prompt: ChatPromptTemplate instance
            llm: Language model instance
            
        Returns:
            Chain instance (prompt | llm)
        """
        return prompt | llm
    
    @staticmethod
    def _log_raw_response(response_or_error: Any, context: str) -> None:
        """
        Debug function to log raw response content for troubleshooting.
        
        Args:
            response_or_error: The response object or exception
            context: Context string (e.g., "SUCCESS", "TOKEN_LIMIT_ERROR")
        """
        try:
            logging.info(f"RAW RESPONSE DEBUG [{context}]:")
            
            if context == "TOKEN_LIMIT_ERROR":
                # For token limit errors, try to extract any available response data
                error_str = str(response_or_error)
                logging.error(f"RAW ERROR: {error_str}")
                
                # Check if the error contains any response content
                if hasattr(response_or_error, 'response'):
                    logging.error(f"RAW ERROR RESPONSE: {response_or_error.response}")
                if hasattr(response_or_error, 'content'):
                    content = str(response_or_error.content)[:1000]  # Truncate for logging
                    logging.error(f"RAW ERROR CONTENT (first 1000 chars): {content}")
                if hasattr(response_or_error, 'args') and response_or_error.args:
                    logging.error(f"RAW ERROR ARGS: {response_or_error.args}")
                    
            else:
                # For successful responses, log the structure and content
                response_type = type(response_or_error).__name__
                logging.info(f"RAW RESPONSE TYPE: {response_type}")
                
                # Log response attributes
                if hasattr(response_or_error, '__dict__'):
                    attrs = list(response_or_error.__dict__.keys())
                    logging.info(f"RAW RESPONSE ATTRIBUTES: {attrs}")
                
                # Log content if it's a string or has string representation
                content_str = str(response_or_error)
                if len(content_str) > 2000:
                    # Show first and last parts for very long responses
                    logging.info(f"RAW RESPONSE CONTENT (first 1000 chars): {content_str[:1000]}")
                    logging.info(f"RAW RESPONSE CONTENT (last 1000 chars): {content_str[-1000:]}")
                    logging.info(f"RAW RESPONSE TOTAL LENGTH: {len(content_str)} characters")
                else:
                    logging.info(f"RAW RESPONSE CONTENT: {content_str}")
                    
                # Check for specific LangChain response attributes
                if hasattr(response_or_error, 'content'):
                    logging.info(f"RAW RESPONSE .content: {str(response_or_error.content)[:500]}...")
                if hasattr(response_or_error, 'response_metadata'):
                    logging.info(f"RAW RESPONSE .response_metadata: {response_or_error.response_metadata}")
                if hasattr(response_or_error, 'usage_metadata'):
                    logging.info(f"RAW RESPONSE .usage_metadata: {response_or_error.usage_metadata}")
                    
        except Exception as debug_error:
            logging.error(f"Error in _log_raw_response debug function: {debug_error}")
    
    @staticmethod
    def invoke_chain(
        chain: Any,
        input_data: Dict[str, Any],
        retry_count: int = 0,
        retry_delay: float = 1.0,
        error_handler: Optional[Callable[[Exception], None]] = None,
        operation_name: str = "Chain operation"
    ) -> tuple[Any, float]:
        """
        Invoke a chain with retry logic, error handling, and timing tracking.
        
        Args:
            chain: Chain instance to invoke
            input_data: Input data for the chain
            retry_count: Number of retries on failure
            retry_delay: Delay between retries in seconds
            error_handler: Optional custom error handler function
            operation_name: Name of the operation for logging
            
        Returns:
            Tuple of (result, duration_in_seconds)
            
        Raises:
            Exception: If all retries fail
        """
        logging.info(f"Starting {operation_name}")
        last_exception = None
        overall_start_time = time.time()
        
        # Use LangSmith tracing context if available
        with LangSmithService.trace_context(
            operation_name,
            {
                "retry_count": retry_count,
                "input_size_chars": len(str(input_data)),
                "estimated_tokens": len(str(input_data)) // 4
            }
        ) as trace_run:
            
            for attempt in range(retry_count + 1):
                try:
                    start_time = time.time()
                    
                    # Log input size for debugging token issues
                    input_str = str(input_data)
                    input_size = len(input_str)
                    logging.info(f"TOKEN DEBUG: Chain input size: {input_size} characters (~{input_size//4} tokens estimated)")
                    
                    # Add attempt info to trace if available
                    if trace_run and hasattr(trace_run, 'patch'):
                        try:
                            trace_run.inputs.update({"attempt": attempt + 1})
                        except:
                            pass  # Ignore trace update errors
                    
                    result = chain.invoke(input_data)
                    duration = time.time() - start_time
                    overall_duration = time.time() - overall_start_time
                    
                    # Log successful response details with raw response debugging
                    result_str = str(result)
                    output_size = len(result_str)
                    logging.info(f"TOKEN DEBUG: Chain output size: {output_size} characters (~{output_size//4} tokens estimated)")
                    
                    # DEBUG: Show raw response content (truncated for logging)
                    # ChainService._log_raw_response(result, "SUCCESS")
                    
                    # Update trace with success info
                    if trace_run and hasattr(trace_run, 'patch'):
                        try:
                            trace_run.outputs.update({
                                "success": True,
                                "attempts": attempt + 1,
                                "duration_seconds": overall_duration,
                                "output_size_chars": output_size,
                                "estimated_output_tokens": output_size // 4
                            })
                        except:
                            pass  # Ignore trace update errors
                    
                    if attempt > 0:
                        logging.info(f"Completed {operation_name} on attempt {attempt + 1} [{overall_duration:.2f} secs total]")
                    else:
                        logging.info(f"Completed {operation_name} [{overall_duration:.2f} secs]")
                    
                    return result, overall_duration
                    
                except Exception as e:
                    last_exception = e
                    overall_duration = time.time() - overall_start_time
                    
                    # Enhanced token limit error detection and logging
                    error_str = str(e)
                    error_msg = error_str.lower()
                    is_token_error = any(keyword in error_msg for keyword in
                                       ["length limit", "token", "completion_tokens", "max_tokens"])
                    
                    if is_token_error:
                        logging.error(f"TOKEN LIMIT ERROR DETECTED: {e}")
                        logging.error(f"TOKEN DEBUG: Input size was ~{input_size//4} tokens")
                        logging.error("TOKEN DEBUG: Response was likely truncated due to max_tokens limit")
                        
                        # DEBUG: Try to extract and show any partial response content
                        ChainService._log_raw_response(e, "TOKEN_LIMIT_ERROR")
                        
                        logging.error("TOKEN DEBUG: Solutions:")
                        logging.error("  1. Model-specific limits are now enforced in LLMService")
                        logging.error("  2. Reduce input prompt size if still failing")
                        logging.error("  3. Split large requests into smaller chunks")
                        logging.error("  4. Use streaming responses if supported")
                    
                    # Update trace with error info
                    if trace_run and hasattr(trace_run, 'patch'):
                        try:
                            trace_run.outputs.update({
                                "success": False,
                                "error_type": type(e).__name__,
                                "error_message": str(e),
                                "is_token_error": is_token_error,
                                "attempts": attempt + 1,
                                "duration_seconds": overall_duration
                            })
                        except:
                            pass  # Ignore trace update errors
                    
                    if error_handler:
                        error_handler(e)
                    
                    if attempt < retry_count:
                        logging.warning(f"{operation_name} failed on attempt {attempt + 1}, retrying in {retry_delay}s: {e}")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logging.error(f"{operation_name} failed after {retry_count + 1} attempts [{overall_duration:.2f} secs total]: {e}")
            
            raise last_exception
    
    @staticmethod
    def batch_invoke_chain(
        chain: Any, 
        input_list: list[Dict[str, Any]], 
        operation_name: str = "Batch operation",
        continue_on_error: bool = True
    ) -> list[tuple[Any, Optional[Exception]]]:
        """
        Invoke a chain multiple times with different inputs.
        
        Args:
            chain: Chain instance to invoke
            input_list: List of input dictionaries
            operation_name: Name of the operation for logging
            continue_on_error: Whether to continue processing if one item fails
            
        Returns:
            List of tuples (result_or_None, exception_or_None)
        """
        logging.info(f"Starting {operation_name} with {len(input_list)} items")
        results = []
        
        for i, input_data in enumerate(input_list):
            try:
                result = chain.invoke(input_data)
                results.append((result, None))
                logging.debug(f"Completed item {i + 1}/{len(input_list)}")
                
            except Exception as e:
                logging.error(f"Failed item {i + 1}/{len(input_list)}: {e}")
                results.append((None, e))
                
                if not continue_on_error:
                    logging.error(f"Stopping {operation_name} due to error")
                    break
        
        successful = sum(1 for result, error in results if error is None)
        logging.info(f"Completed {operation_name}: {successful}/{len(input_list)} successful")
        
        return results
"""
Cache Service for managing LangChain caching.
"""

import logging
from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache


class CacheService:
    """Service for managing LangChain caching."""
    
    @staticmethod
    def setup_cache(enable_cache: bool = True, database_path: str = ".langchain.db") -> None:
        """
        Set up LangChain caching.
        
        Args:
            enable_cache: Whether to enable caching
            database_path: Path to the SQLite cache database
        """
        if enable_cache:
            logging.info(f"Enabling LLM cache with database: {database_path}")
            set_llm_cache(SQLiteCache(database_path=database_path))
        else:
            logging.info("LLM cache disabled")
            set_llm_cache(None)
    
    @staticmethod
    def clear_cache(database_path: str = ".langchain.db") -> None:
        """
        Clear the cache database.
        
        Args:
            database_path: Path to the SQLite cache database
        """
        import os
        if os.path.exists(database_path):
            os.remove(database_path)
            logging.info(f"Cache database cleared: {database_path}")
        else:
            logging.info(f"Cache database not found: {database_path}")
"""
Rally.io Python Package
=====================

This package provides tools for interacting with Rally.io services, including vector search and RAG capabilities.
"""

from .search import SearchTool
from .rag import RagTool

def get_search_tool(project_id: str, location: str, index_endpoint_id: str) -> SearchTool:
    """
    Get a vector search tool instance.

    Args:
        project_id (str): The Google Cloud project ID
        location (str): The Google Cloud location (e.g., "us-central1")
        index_endpoint_id (str): The ID of the deployed index endpoint

    Returns:
        SearchTool: A configured vector search tool instance
    """
    return SearchTool(project_id, location, index_endpoint_id)

def get_rag_function(project_id: str, rag_corpus_id: str, location: str = "us-central1") -> callable:
    """
    Get a RAG function that can be used to perform RAG queries.

    Args:
        project_id (str): The Google Cloud project ID
        rag_corpus_id (str): The RAG corpus ID
        location (str): The Google Cloud location (default: "us-central1")

    Returns:
        callable: A function that takes a query string and returns a response string
    """
    rag_tool = RagTool(project_id, rag_corpus_id, location)
    return rag_tool.get_rag_function()

__all__ = ['get_search_tool', 'get_rag_function']

__version__ = "0.1.0" 
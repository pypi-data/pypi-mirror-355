"""
Search Tool Module
================

This module provides the SearchTool class for interacting with Google Cloud Vector Search services.
"""

from typing import Dict, Any, Optional, List
from google.cloud import aiplatform
from google.cloud.aiplatform import MatchingEngineIndex, MatchingEngineIndexEndpoint
import numpy as np

class SearchTool:
    """
    A tool for performing vector searches using Google Cloud Vector Search services.
    
    This class handles authentication and provides methods for searching
    through vector embeddings using Google Cloud's Matching Engine.
    """
    
    def __init__(self, project_id: str, location: str, index_endpoint_id: str):
        """
        Initialize a new SearchTool instance.

        Args:
            project_id (str): The Google Cloud project ID
            location (str): The Google Cloud location (e.g., "us-central1")
            index_endpoint_id (str): The ID of the deployed index endpoint
        """
        self.project_id = project_id
        self.location = location
        self.index_endpoint_id = index_endpoint_id
        
        # Initialize the Vertex AI client
        aiplatform.init(project=project_id, location=location)
        
        # Get the index endpoint
        self.index_endpoint = MatchingEngineIndexEndpoint(
            index_endpoint_name=f"projects/{project_id}/locations/{location}/indexEndpoints/{index_endpoint_id}"
        )
        
    def search(self, query_vector: List[float], num_neighbors: int = 5, **kwargs) -> Dict[str, Any]:
        """
        Perform a vector search using the provided query vector.

        Args:
            query_vector (List[float]): The query vector to search with
            num_neighbors (int): Number of nearest neighbors to return (default: 5)
            **kwargs: Additional search parameters like filter, etc.

        Returns:
            Dict[str, Any]: The search results containing:
                - neighbors: List of nearest neighbors
                - distances: List of distances to neighbors
                - metadata: Additional metadata if available

        Raises:
            Exception: If the search request fails
        """
        try:
            # Convert query vector to numpy array
            query_vector = np.array(query_vector, dtype=np.float32)
            
            # Perform the search
            search_response = self.index_endpoint.search(
                deployed_index_id="default",  # or your specific deployed index ID
                queries=[query_vector],
                num_neighbors=num_neighbors,
                **kwargs
            )
            
            # Process and format the results
            results = {
                "neighbors": [],
                "distances": [],
                "metadata": []
            }
            
            # Extract results from the first query (since we only sent one)
            if search_response and len(search_response) > 0:
                query_results = search_response[0]
                
                for neighbor in query_results:
                    results["neighbors"].append(neighbor.id)
                    results["distances"].append(neighbor.distance)
                    if hasattr(neighbor, 'metadata'):
                        results["metadata"].append(neighbor.metadata)
            
            return results
            
        except Exception as e:
            raise Exception(f"Vector search failed: {str(e)}")
    
    def get_index_info(self) -> Dict[str, Any]:
        """
        Get information about the vector search index.

        Returns:
            Dict[str, Any]: Information about the index including:
                - index_name: Name of the index
                - dimensions: Number of dimensions in the vectors
                - approximate_neighbors_count: Number of approximate neighbors
                - distance_measure_type: Type of distance measure used
                - algorithm_config: Configuration of the algorithm

        Raises:
            Exception: If retrieving index info fails
        """
        try:
            # Get the index information
            index = self.index_endpoint.deployed_indexes[0].index  # Assuming first deployed index
            
            return {
                "index_name": index.name,
                "dimensions": index.dimensions,
                "approximate_neighbors_count": index.approximate_neighbors_count,
                "distance_measure_type": index.distance_measure_type,
                "algorithm_config": index.algorithm_config
            }
            
        except Exception as e:
            raise Exception(f"Failed to get index info: {str(e)}")
    
    def batch_search(self, query_vectors: List[List[float]], num_neighbors: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """
        Perform batch vector search with multiple query vectors.

        Args:
            query_vectors (List[List[float]]): List of query vectors to search with
            num_neighbors (int): Number of nearest neighbors to return per query (default: 5)
            **kwargs: Additional search parameters

        Returns:
            List[Dict[str, Any]]: List of search results for each query vector

        Raises:
            Exception: If the batch search request fails
        """
        try:
            # Convert query vectors to numpy array
            query_vectors = np.array(query_vectors, dtype=np.float32)
            
            # Perform the batch search
            search_responses = self.index_endpoint.search(
                deployed_index_id="default",  # or your specific deployed index ID
                queries=query_vectors,
                num_neighbors=num_neighbors,
                **kwargs
            )
            
            # Process results for each query
            all_results = []
            for query_response in search_responses:
                query_results = {
                    "neighbors": [],
                    "distances": [],
                    "metadata": []
                }
                
                for neighbor in query_response:
                    query_results["neighbors"].append(neighbor.id)
                    query_results["distances"].append(neighbor.distance)
                    if hasattr(neighbor, 'metadata'):
                        query_results["metadata"].append(neighbor.metadata)
                
                all_results.append(query_results)
            
            return all_results
            
        except Exception as e:
            raise Exception(f"Batch vector search failed: {str(e)}") 
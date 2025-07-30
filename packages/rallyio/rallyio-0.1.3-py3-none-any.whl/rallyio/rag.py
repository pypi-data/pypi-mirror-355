"""
RAG Tool Module
==============

This module provides the RagTool class for interacting with Google Cloud RAG services.
"""

from typing import Callable, Optional
from google import genai
from google.genai import types
import inspect
from functools import wraps

def test_get_param_name():
    # Create a RAG tool instance
    rag_tool = RagTool(project_id="test", rag_corpus_id="test")
    
    # Get a RAG function
    rag_func = rag_tool.get_rag_function()
    
    # Get the parameter name using inspect
    sig = inspect.signature(rag_func)
    param_names = list(sig.parameters.keys())
    print(f"Parameter name: {param_names[0]}")  # Will print: Parameter name: query

class RagTool:
    """
    A tool for performing RAG (Retrieval Augmented Generation) using Google Cloud services.
    
    This class handles authentication and provides methods for generating responses
    using RAG through Google Cloud's Gemini model.
    """
    
    def __init__(self, project_id: str, rag_corpus_id: str, location: str = "us-central1"):
        """
        Initialize a new RagTool instance.

        Args:
            project_id (str): The Google Cloud project ID
            rag_corpus_id (str): The RAG corpus ID
            location (str): The Google Cloud location (default: "us-central1")
        """
        self.project_id = project_id
        self.rag_corpus_id = rag_corpus_id
        self.location = location
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location="global",
        )
        self.model = "gemini-2.5-pro-preview-06-05"
        
    def get_rag_function(self, function_name: Optional[str] = None, parameter_name: Optional[str] = None) -> Callable[[str], str]:
        """
        Returns a function that can be used to perform RAG queries.

        Args:
            function_name (Optional[str]): Optional name for the returned function. If None, a default name will be used.
            parameter_name (Optional[str]): Optional name for the parameter of the returned function. If None, defaults to 'query'.

        Returns:
            Callable[[str], str]: A function that takes a query string and returns a response string
        """
        def inner_function(query: str) -> str:
            if query == "" or query is None:
                return "Please provide a valid query."
        
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part(text=query)]
                )
            ]
            
            tools = [
                types.Tool(
                    retrieval=types.Retrieval(
                        vertex_rag_store=types.VertexRagStore(
                            rag_resources=[
                                types.VertexRagStoreRagResource(
                                    rag_corpus=f"projects/{self.project_id}/locations/{self.location}/ragCorpora/{self.rag_corpus_id}"
                                )
                            ],
                        )
                    )
                )
            ]

            generate_content_config = types.GenerateContentConfig(
                temperature=1,
                top_p=1,
                seed=0,
                max_output_tokens=65535,
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
                ],
                tools=tools,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=-1,
                ),
            )

            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
                    continue
                response_text += chunk.text

            return response_text

        # Create a new function with the custom parameter name if provided
        if parameter_name:
            # Create a new function with the custom parameter name
            @wraps(inner_function)
            def wrapped_function(**kwargs):
                # Get the value using the custom parameter name
                query_value = kwargs[parameter_name]
                # Call the inner function with the query value
                return inner_function(query=query_value)
            
            # Set the function name if provided
            if function_name:
                wrapped_function.__name__ = function_name
                
            # Set the signature with the custom parameter name
            sig = inspect.signature(inner_function)
            param = list(sig.parameters.values())[0]
            new_param = inspect.Parameter(
                parameter_name,
                param.kind,
                default=param.default,
                annotation=param.annotation
            )
            wrapped_function.__signature__ = sig.replace(parameters=[new_param])
            
            return wrapped_function
        
        # If no custom parameter name, just set the function name if provided
        if function_name:
            inner_function.__name__ = function_name
            
        return inner_function 
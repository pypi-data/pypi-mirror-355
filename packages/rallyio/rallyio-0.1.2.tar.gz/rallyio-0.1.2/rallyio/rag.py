"""
RAG Tool Module
==============

This module provides the RagTool class for interacting with Google Cloud RAG services.
"""

from typing import Callable, Optional
from google import genai
from google.genai import types

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
        
    def get_rag_function(self) -> Callable[[str], str]:
        """
        Returns a function that can be used to perform RAG queries.

        Returns:
            Callable[[str], str]: A function that takes a query string and returns a response string
        """
        def function(parameter1: str) -> str:

            if parameter1 is "" or None:
                return "Please provide a valid query."
        
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part(text=parameter1)]
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

        return function 
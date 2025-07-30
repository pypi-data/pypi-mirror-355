# Rally.io Python Package

A Python package for interacting with Rally.io services, including search and RAG (Retrieval Augmented Generation) capabilities.

## Installation

### Quick Install (Recommended)

Simply use pip to install the package:

```bash
pip install rallyio
```

### Development Installation

If you want to install the package in development mode or contribute to the project:

1. Clone the repository:
```bash
git clone https://github.com/jatinarora2409/rallyio.git
cd rallyio
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the package in development mode:
```bash
pip install -e .
```

## Usage

### Search Tool

```python
import rallyio

# Initialize the search tool
search_tool = rallyio.get_search_tool(
    project_id="your-google-cloud-project-id",
    location="us-central1",
    index_endpoint_id="your-index-endpoint-id"
)

# Perform a search
results = search_tool.search(query_vector=[0.1, 0.2, 0.3])  # Your vector here
print(results)

# Get information about the index
index_info = search_tool.get_index_info()
print(index_info)
```

### RAG Tool

```python
import rallyio
import inspect

# Initialize the RAG function with custom names
my_rag = rallyio.get_rag_function(
    project_id="your-google-cloud-project-id",
    rag_corpus_id="your-rag-corpus-id",
    location="us-central1",  # optional, defaults to "us-central1"
    function_name="ask_ai",  # optional, customizes the function name
    parameter_name="question"  # optional, customizes the parameter name
)

# The function's name and parameter will be customized
print(my_rag.__name__)  # Output: ask_ai
print(inspect.signature(my_rag))  # Output: (question: str) -> str

# Use the RAG function with the custom parameter name
response = my_rag(question="What is the capital of France?")
print(response)

# You can also use the default function without custom names
default_rag = rallyio.get_rag_function(
    project_id="your-google-cloud-project-id",
    rag_corpus_id="your-rag-corpus-id"
)
print(default_rag.__name__)  # Output: function
print(inspect.signature(default_rag))  # Output: (query: str) -> str

# Use the default function
response = default_rag(query="Tell me about quantum computing")
print(response)
```

## Requirements

- Python 3.8 or higher
- Google Cloud credentials configured (for RAG functionality)
- Required Python packages (automatically installed with the package):
  - requests
  - google-cloud-aiplatform
  - google-generativeai

## Google Cloud Setup

To use the RAG functionality, you need to:

1. Have a Google Cloud project set up
2. Enable the Vertex AI API
3. Create a RAG corpus in your project
4. Set up authentication:
   ```bash
   # Install Google Cloud CLI
   # Then authenticate:
   gcloud auth application-default login
   ```

## Development

To run tests:
```bash
pytest
```

To format code:
```bash
black .
```

## License

[Your chosen license]

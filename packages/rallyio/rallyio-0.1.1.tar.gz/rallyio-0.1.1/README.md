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
    data_id="your-data-id",
    api_key="your-api-key"
)

# Perform a search
results = search_tool.search("your search query")
print(results)

# Get information about the data source
data_info = search_tool.get_data_info()
print(data_info)
```

### RAG Tool

```python
import rallyio

# Initialize the RAG function
rag_function = rallyio.get_rag_function(
    project_id="your-google-cloud-project-id",
    rag_corpus_id="your-rag-corpus-id",
    location="us-central1"  # optional, defaults to "us-central1"
)

# Use the RAG function to get responses
response = rag_function("What is the capital of France?")
print(response)

# You can reuse the same function for multiple queries
response2 = rag_function("Tell me about quantum computing")
print(response2)
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

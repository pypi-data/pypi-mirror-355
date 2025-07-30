from setuptools import setup, find_packages

setup(
    name="rallyio",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",  # For making HTTP requests
        "google-cloud-aiplatform>=1.38.0",  # For RAG functionality
        "google-generativeai>=0.3.0",  # For RAG functionality
    ],
    author="Jatin Arora",
    author_email="jatinarora2409@gmail.com",
    description="A Python library for interacting with Rally.io services",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jatinarora2409/rallyio",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",  # Updated to match README requirement
) 
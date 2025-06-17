# TLDR - Function Signature Extractor

TLDR is a Python tool that extracts function signatures from large codebases and generates concise summaries. It's particularly useful for providing context to Large Language Models (LLMs) when dealing with codebases that exceed their context window limits.

## Features

- **Multi-language Support**: Supports 40+ programming languages via Pygments lexer integration
- **Signature Extraction**: Extracts function, class, and method signatures from code files
- **JSON Output**: Produces structured JSON output for easy integration with other tools
- **Recursive Processing**: Can process entire directory trees recursively
- **Atomic File Writing**: Ensures data integrity with atomic file operations
- **(Optional) AI-Powered File Summaries**: Generates file summaries using LLM providers (Claude, OpenAI, Grok)

## Supported Languages

JavaScript/TypeScript, Python, Java, C/C++, C#, PHP, Ruby, Go, Rust, Swift, Scala, Kotlin, and many more.

## Installation

```bash
# Clone the repository
git clone https://github.com/csimoes1/tldr-code.git
cd tldr-code
# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Show usage help message
python tldr_code.py -h 

# Process a local directory tree to generate a tldr summary file
python tldr_code.py /path/to/directory

# Example: Process a GitHub repository and create a tldr summary file (example here is the Python fastapi project)
python tldr_code.py https://github.com/fastapi/fastapi 

# Example: Process a GitHub repository and store the downloaded files and the tldr summary file in a specific directory
python tldr_code.py https://github.com/fastapi/fastapi /Users/csimoes/repos/fastapi
```

### Command Line Options

- `input (GitHub URL | /path/to/directory)`: Path to the repo/directory to scan (required)
- `output_filename`: Output filename (optional, defaults to `tldr.json`)

## Output Format

TLDR generates JSON files with the following structure:

```json
{
  "directory_path": "/path/to/directory",
  "last_updated": "2025-06-16T10:30:00Z",
  "files": [
    {
      "file_path": "/path/to/file.py",
      "last_scanned": "2025-06-16T10:30:00Z",
      "signatures": [
        "class MyClass(BaseClass)",
        "def __init__(self, param1, param2)",
        "def process_data(self, data: List[str]) -> Dict[str, Any]"
      ],
      "summary": "This file implements data processing functionality..."
    }
  ]
}
```

## Use Cases

1. **LLM Context Preparation**: Quickly generate summaries of large codebases for LLM analysis
2. **Code Documentation**: Automatically extract API signatures for documentation
3. **Codebase Analysis**: Get an overview of code structure and functionality
4. **Code Review Assistance**: Understand code changes and their impact

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

See LICENSE file for details.
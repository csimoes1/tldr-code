# TLDR - Function Signature Extractor

TLDR is a Python tool that extracts function signatures from large codebases and generates concise summaries. It's particularly useful for providing context to Large Language Models (LLMs) when dealing with codebases that exceed their context window limits.

## Features

- **Multi-language Support**: Supports 40+ programming languages via Pygments lexer integration
- **AI-Powered Summaries**: Generates file summaries using LLM providers (Claude, OpenAI, Grok)
- **Signature Extraction**: Extracts function, class, and method signatures from code files
- **JSON Output**: Produces structured JSON output for easy integration with other tools
- **Recursive Processing**: Can process entire directory trees recursively
- **Atomic File Writing**: Ensures data integrity with atomic file operations

## Supported Languages

JavaScript/TypeScript, Python, Java, C/C++, C#, PHP, Ruby, Go, Rust, Swift, Scala, Kotlin, and many more.

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd tldr

# Install dependencies
pip install -r requirements.txt
```

## Configuration

TLDR supports multiple LLM providers. Set up your API keys:

```bash
# For Claude (Anthropic)
export ANTHROPIC_API_KEY='your-api-key-here'

# For OpenAI
export OPENAI_API_KEY='your-api-key-here'

# For Grok
export GROK_API_KEY='your-api-key-here'
```

## Usage

### Basic Usage

```bash
# Process a single directory
python tldr/TLDRFileCreator.py ./src

# Specify output filename
python tldr/TLDRFileCreator.py ./src my_summary.json

# Process recursively with AI summaries
python tldr/TLDRFileCreator.py ./src --recursive --llm claude

# Skip AI summaries (signatures only)
python tldr/TLDRFileCreator.py ./src --skip-file-summary
```

### Command Line Options

- `directory_path`: Path to the directory to scan (required)
- `output_filename`: Output filename (optional, defaults to `tldr.json`)
- `-r, --recursive`: Process directories recursively
- `--llm {claude,openai,grok}`: LLM provider for generating summaries
- `--skip-file-summary`: Skip AI-generated summaries
- `--setup-llm`: Show LLM setup instructions

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

For recursive processing, the output includes multiple directories:

```json
{
  "root_directory": "/path/to/project",
  "last_updated": "2025-06-16T10:30:00Z",
  "total_directories_processed": 5,
  "directories": [...]
}
```

## Use Cases

1. **LLM Context Preparation**: Quickly generate summaries of large codebases for LLM analysis
2. **Code Documentation**: Automatically extract API signatures for documentation
3. **Codebase Analysis**: Get an overview of code structure and functionality
4. **Code Review Assistance**: Understand code changes and their impact

## Architecture

- **TLDRFileCreator**: Main orchestrator class
- **SignatureExtractor**: Extracts signatures using Pygments lexers
- **LLM Providers**: Pluggable AI providers for generating summaries
- **Atomic File Operations**: Ensures data integrity during file writes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

See LICENSE file for details.
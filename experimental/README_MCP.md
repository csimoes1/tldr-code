# UNDER CONSTRUCTION - not ready yet

# TLDR Code MCP Server

This MCP (Model Context Protocol) server exposes the tldr-code functionality as tools that can be used by Claude and other LLMs to analyze codebases and generate function signature summaries.

## Installation

1. Install the package with MCP dependencies:
```bash
pip install -e .
```

2. The MCP server will be available as `tldr-mcp-server` command after installation.

## Configuration

### Claude Desktop

Add the following to your Claude Desktop configuration file:

**On macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**On Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
  {
  "mcpServers": {
    "tldr-code": {
      "command": "/path/to/repo/tldr-code/.venv/bin/python",
      "args": ["/path/to/repo/tldr-code/mcp_server.py"]
    }
  }
}
```

## Available Tools

The MCP server provides two main tools:

### 1. `generate_tldr`
Generates a TLDR JSON file containing function signatures from a codebase.

**Parameters:**
- `path` (required): Path to local directory or GitHub URL to analyze
- `output_filename` (optional): Custom output filename (defaults to tldr.json)

**Examples:**
- Analyze local directory: `{"path": "/path/to/project"}`
- Analyze GitHub repo: `{"path": "https://github.com/user/repo"}`
- Custom output: `{"path": "/path/to/project", "output_filename": "my_analysis.json"}`

### 2. `read_tldr`
Reads and returns the contents of an existing TLDR JSON file.

**Parameters:**
- `file_path` (required): Path to the TLDR JSON file to read

**Example:**
- `{"file_path": "/path/to/tldr.json"}`

## Usage in Claude

Once configured, you can use the tools in Claude by asking questions like:

- "Generate a TLDR analysis for the project at /path/to/my/project"
- "Analyze this GitHub repository: https://github.com/fastapi/fastapi"
- "Read the TLDR file at /path/to/existing/tldr.json"

The server will:
1. Run the tldr-code analysis on the specified path
2. Generate a .tldr.json file with function signatures
3. Return the contents along with a summary of files, functions, and classes found

## Troubleshooting

1. **Server not appearing in Claude**: Check that the configuration file path is correct and the JSON is valid.

2. **Command not found**: Ensure the package is installed with `pip install -e .` and the `tldr-mcp-server` command is available.

3. **Path errors**: The server supports both absolute paths and paths with `~` (home directory expansion).

4. **GitHub access**: For GitHub repositories, ensure you have internet access and the repository is public or accessible.

## Development

To test the server locally:

```bash
# Run the server directly
python mcp_server.py

# Or use the installed command
tldr-mcp-server
```

The server uses stdio for communication, so it will wait for MCP protocol messages on stdin.
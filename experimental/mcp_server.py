#!/usr/bin/env python3
"""
MCP Server for TLDR Code Analysis

This MCP server exposes the tldr-code functionality as tools that can be used
by Claude and other LLMs to analyze codebases and generate function signature summaries.
"""

import asyncio
import json
import os
import sys
import tempfile
import logging
from pathlib import Path
from typing import Any, Sequence

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Import our tldr_code functions
from tldr_code import process_local_path, process_github_url, is_github_url

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tldr-mcp-server")

# Initialize the MCP server
server = Server("tldr-code")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    List available tools.
    """
    return [
        Tool(
            name="generate_tldr",
            description="Generate a TLDR JSON file containing function signatures from a codebase",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to local directory or GitHub URL to analyze"
                    },
                    "output_filename": {
                        "type": "string",
                        "description": "Optional custom output filename (defaults to tldr.json)"
                    }
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="read_tldr",
            description="Read and return the contents of an existing TLDR JSON file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the TLDR JSON file to read"
                    }
                },
                "required": ["file_path"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle tool calls.
    """
    if name == "generate_tldr":
        return await generate_tldr(arguments)
    elif name == "read_tldr":
        return await read_tldr(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def generate_tldr(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Generate a TLDR JSON file from a codebase and return its contents.
    """
    try:
        path = arguments["path"]
        output_filename = arguments.get("output_filename")
        
        logger.info(f"Generating TLDR for path: {path}")
        
        # Determine if this is a GitHub URL or local path
        if is_github_url(path):
            tldr_file = process_github_url(path, ".", output_filename)
        else:
            # Expand user home directory if needed
            expanded_path = os.path.expanduser(path)
            if not os.path.exists(expanded_path):
                return [TextContent(
                    type="text",
                    text=f"Error: Path '{expanded_path}' does not exist."
                )]
            
            tldr_file = process_local_path(expanded_path, output_filename)
        
        # Read the generated file and return its contents
        with open(tldr_file, 'r', encoding='utf-8') as f:
            tldr_content = f.read()
        
        # Parse JSON to validate and get summary info
        try:
            tldr_data = json.loads(tldr_content)
            summary_info = f"Generated TLDR file: {tldr_file}\n"
            summary_info += f"Files analyzed: {len(tldr_data.get('files', []))}\n"
            
            # Count total functions/classes
            total_functions = 0
            total_classes = 0
            for file_info in tldr_data.get('files', []):
                total_functions += len(file_info.get('functions', []))
                total_classes += len(file_info.get('classes', []))
            
            summary_info += f"Total functions: {total_functions}\n"
            summary_info += f"Total classes: {total_classes}\n\n"
            summary_info += "TLDR JSON Content:\n"
            summary_info += tldr_content
            
            return [TextContent(
                type="text",
                text=summary_info
            )]
            
        except json.JSONDecodeError:
            return [TextContent(
                type="text",
                text=f"Generated TLDR file: {tldr_file}\n\nContent:\n{tldr_content}"
            )]
            
    except Exception as e:
        logger.error(f"Error generating TLDR: {e}")
        return [TextContent(
            type="text",
            text=f"Error generating TLDR: {str(e)}"
        )]

async def read_tldr(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Read and return the contents of an existing TLDR JSON file.
    """
    try:
        file_path = arguments["file_path"]
        expanded_path = os.path.expanduser(file_path)
        
        if not os.path.exists(expanded_path):
            return [TextContent(
                type="text",
                text=f"Error: File '{expanded_path}' does not exist."
            )]
        
        with open(expanded_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse and provide summary
        try:
            tldr_data = json.loads(content)
            summary_info = f"TLDR file: {expanded_path}\n"
            summary_info += f"Files analyzed: {len(tldr_data.get('files', []))}\n"
            
            # Count total functions/classes
            total_functions = 0
            total_classes = 0
            for file_info in tldr_data.get('files', []):
                total_functions += len(file_info.get('functions', []))
                total_classes += len(file_info.get('classes', []))
            
            summary_info += f"Total functions: {total_functions}\n"
            summary_info += f"Total classes: {total_classes}\n\n"
            summary_info += "TLDR JSON Content:\n"
            summary_info += content
            
            return [TextContent(
                type="text",
                text=summary_info
            )]
            
        except json.JSONDecodeError:
            return [TextContent(
                type="text",
                text=f"TLDR file: {expanded_path}\n\nContent:\n{content}"
            )]
            
    except Exception as e:
        logger.error(f"Error reading TLDR file: {e}")
        return [TextContent(
            type="text",
            text=f"Error reading TLDR file: {str(e)}"
        )]

async def main():
    """
    Main function to run the MCP server.
    """
    # Run the server using stdin/stdout streams
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="tldr-code",
                server_version="0.1.2",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
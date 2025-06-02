#!/usr/bin/env python3
"""
TLDRFileCreator.py - Creates design.md-like files for directories

This script scans a directory and creates a markdown file with signatures
extracted from each file using signature_extractor.py.

Usage:
    python TLDRFileCreator.py <directory_path> [output_filename]
"""
import logging_setup
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from signature_extractor import SignatureExtractor
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound
from llm_providers import LLMFactory, LLMConfig


class TLDRFileCreator:
    def __init__(self, llm_provider: str = None):
        self.signature_extractor = SignatureExtractor()
        self.llm_provider = None
        
        # Lexers to exclude (non-programming languages)
        self.excluded_lexers = {
            'TextLexer',           # Plain text
            'MarkdownLexer',       # Markdown
            'RstLexer',           # reStructuredText
            'IniLexer',           # INI/config files
            'YamlLexer',          # YAML
            'JsonLexer',          # JSON (data format)
            'XmlLexer',           # XML (markup)
            'HtmlLexer',          # HTML (markup)
            'CssLexer',           # CSS (styling, not programming logic)
            'DiffLexer',          # Diff files
            'LogsLexer',          # Log files
        }
        
        if llm_provider:
            self._setup_llm_provider(llm_provider)
        
    def create_tldr_file(self, directory_path, output_filename=None):
        """
        Creates a TLDR markdown file for the given directory.
        
        Args:
            directory_path (str): Path to the directory to scan
            output_filename (str): Optional output filename, defaults to 'design.md'
        """
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory '{directory_path}' not found.")
            
        if not os.path.isdir(directory_path):
            raise ValueError(f"'{directory_path}' is not a directory.")
            
        # Set default output filename if not provided
        if output_filename is None:
            output_filename = os.path.join(directory_path, 'tldr.md')
        
        # Get absolute path for the directory
        abs_directory_path = os.path.abspath(directory_path)
        
        # Collect all files in the directory (excluding subdirectories for now)
        files = []
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isfile(item_path) and self._is_programming_file(item_path):
                files.append(item_path)
        
        # Sort files for consistent output
        files.sort()
        
        # Generate the markdown content
        content = self._generate_markdown_content(abs_directory_path, files)
        
        # Write to output file
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"TLDR file created: {output_filename}")
        
    def _generate_markdown_content(self, directory_path, files):
        """
        Generates the markdown content for the TLDR file.
        
        Args:
            directory_path (str): Absolute path to the directory
            files (list): List of file paths to process
            
        Returns:
            str: Generated markdown content
        """
        # Current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Start building the markdown content
        content = []
        content.append("# File Markdown Summary")
        content.append(f"## Directory Path: `{directory_path}`")
        content.append("")
        
        # Process each file
        for file_path in files:
            abs_file_path = os.path.abspath(file_path)
            relative_file_path = os.path.relpath(abs_file_path, start=os.path.dirname(directory_path))
            
            content.append(f"## File Path: `{abs_file_path}`")
            content.append(f"#### Last scanned: '{timestamp}'")

            # Extract signatures using signature_extractor
            try:
                signatures = self.signature_extractor.get_signatures(file_path)
            except Exception as e:
                logging.warning(f"Could not extract signatures from {file_path}: {e}")
                content.append(f"Error extracting signatures: {e}")
                raise

            # Generate AI-powered summary if LLM provider is available
            logging.debug(f"Generating file summary from LLM for {file_path}")
            summary = self._generate_file_summary(file_path, signatures)

            content.append("")
            content.append("### File Summary:")
            content.append(summary)
            content.append("")
            content.append("### Signatures:")
            content.append(signatures.strip())

        return "\n".join(content)

    def _is_programming_file(self, file_path):
        """
        Use Pygments to determine if file is a recognized programming language.
        
        Args:
            file_path (str): Path to the file to check
            
        Returns:
            bool: True if file is a programming language, False otherwise
        """
        try:
            lexer = get_lexer_for_filename(file_path)
            lexer_name = lexer.__class__.__name__
            
            # Check if lexer is in our excluded list
            if lexer_name in self.excluded_lexers:
                logging.debug(f"Excluding file {file_path} (lexer: {lexer_name})")
                return False
                
            logging.debug(f"Including file {file_path} (lexer: {lexer_name})")
            return True
            
        except ClassNotFound:
            # If Pygments can't determine the file type, exclude it
            logging.debug(f"Excluding file {file_path} (unknown file type)")
            return False
        except Exception as e:
            # If there's any other error, exclude the file but log the issue
            logging.warning(f"Error analyzing file {file_path}: {e}")
            raise
            # return False

    def _setup_llm_provider(self, provider_name: str):
        """Setup LLM provider for generating summaries"""
        try:
            config = LLMConfig.from_env(provider_name)
            self.llm_provider = LLMFactory.create_provider(
                provider_name=config.provider,
                api_key=config.api_key,
                model=config.model
            )
            logging.info(f"LLM provider '{provider_name}' initialized successfully")
        except Exception as e:
            logging.warning(f"Failed to initialize LLM provider '{provider_name}': {e}")
            self.llm_provider = None
            raise

    def _generate_file_summary(self, file_path: str, signatures: str) -> str:
        """Generate AI-powered file summary"""
        if not self.llm_provider:
            return "Summary of what the file does goes here.\nNeeds to be less than 500 characters."
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Generate summary using LLM
            response = self.llm_provider.generate_summary(file_path, file_content, signatures)
            return response.content.strip()
            
        except Exception as e:
            logging.error(f"Failed to generate summary for {file_path}: {e}")
            raise


def main():
    """
    Main function to handle command line arguments and create TLDR file.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Create TLDR markdown files for directories')
    parser.add_argument('directory_path', help='Path to the directory to scan')
    parser.add_argument('output_filename', nargs='?', help='Optional output filename (defaults to tldr.md)')
    parser.add_argument('--llm', choices=LLMFactory.available_providers(), 
                       help='LLM provider to use for generating summaries')
    parser.add_argument('--setup-llm', action='store_true', 
                       help='Show LLM setup instructions')
    
    args = parser.parse_args()
    
    # Show LLM setup instructions if requested
    if args.setup_llm:
        LLMConfig.print_env_setup_instructions()
        return
    
    try:
        print("API Key:", os.environ.get("ANTHROPIC_API_KEY"))
        from anthropic import Anthropic
        client = Anthropic()
        creator = TLDRFileCreator(llm_provider=args.llm)
        creator.create_tldr_file(args.directory_path, args.output_filename)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
TLDRFileCreator.py - Creates design.md-like files for directories

This script scans a directory and creates a markdown file with signatures
extracted from each file using signature_extractor.py.

Usage:
    python TLDRFileCreator.py <directory_path> [output_filename]
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from signature_extractor import SignatureExtractor


class TLDRFileCreator:
    def __init__(self):
        self.signature_extractor = SignatureExtractor()
        
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
            output_filename = os.path.join(directory_path, 'design.md')
        
        # Get absolute path for the directory
        abs_directory_path = os.path.abspath(directory_path)
        
        # Collect all files in the directory (excluding subdirectories for now)
        files = []
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isfile(item_path):
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
            content.append("### Signatures:")
            
            # Extract signatures using signature_extractor
            try:
                signatures = self.signature_extractor.get_signatures(file_path)
                if signatures and signatures.strip():
                    # The signature extractor returns the signatures, we just need to add them
                    content.append(signatures.strip())
                else:
                    content.append("No signatures found.")
            except Exception as e:
                logging.warning(f"Could not extract signatures from {file_path}: {e}")
                content.append(f"Error extracting signatures: {e}")
            
            content.append("")
            content.append("### File Summary:")
            content.append("Summary of what the file does goes here.")
            content.append("Needs to be less than 500 characters.")
            content.append("")
        
        return "\n".join(content)


def main():
    """
    Main function to handle command line arguments and create TLDR file.
    """
    if len(sys.argv) < 2:
        print("Usage: python TLDRFileCreator.py <directory_path> [output_filename]")
        print("Example: python TLDRFileCreator.py ./src")
        print("Example: python TLDRFileCreator.py ./src custom_design.md")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    output_filename = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        creator = TLDRFileCreator()
        creator.create_tldr_file(directory_path, output_filename)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
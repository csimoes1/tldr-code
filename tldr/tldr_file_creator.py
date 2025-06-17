#!/usr/bin/env python3
"""
tldr_file_creator.py - Creates design.md-like files for directories

This script scans a directory and creates a markdown file with signatures
extracted from each file using signature_extractor.py.

Usage:
    python tldr_file_creator.py <directory_path> [output_filename]
"""
import logging_setup
import os
import sys
import logging
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from signature_extractor_pygments import SignatureExtractor
from pygments_tldr.lexers import get_lexer_for_filename
from pygments_tldr.util import ClassNotFound
from llm_providers import LLMFactory, LLMConfig

class TLDRFileCreator:
    def __init__(self, llm_provider: str = None, skip_file_summary: bool = True):
        if llm_provider is None and not skip_file_summary:
            raise ValueError("llm_provider must be specified when initializing TLDRFileCreator (unless skip_file_summary=True)")
            
        self.signature_extractor = SignatureExtractor()
        self.llm_provider = None
        self.skip_file_summary = skip_file_summary
        
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
        
        if not skip_file_summary:
            self._setup_llm_provider(llm_provider)
        
    def create_tldr_file(self, directory_path, output_filename=None, recursive=False):
        """
        Creates a TLDR markdown file for the given directory.
        
        Args:
            directory_path (str): Path to the directory to scan
            output_filename (str): Optional output filename, defaults to 'tldr.json'
            recursive (bool): If True, process subdirectories recursively
        """
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory '{directory_path}' not found.")
            
        if not os.path.isdir(directory_path):
            raise ValueError(f"'{directory_path}' is not a directory.")
            
        # Set default output filename if not provided
        if output_filename is None:
            output_filename = os.path.join(directory_path, 'tldr.json')
        
        # Get absolute path for the directory
        abs_directory_path = os.path.abspath(directory_path)
        
        if recursive:
            # Process each directory separately in recursive mode
            self._process_directories_recursively(directory_path, output_filename)
        else:
            # Process only the current directory
            self._process_single_directory(directory_path, output_filename)
    
    def _process_single_directory(self, directory_path, output_filename):
        """
        Process a single directory and create a TLDR file for it.
        
        Args:
            directory_path (str): Path to the directory to scan
            output_filename (str): Output filename for the TLDR file
        """
        # Get absolute path for the directory
        abs_directory_path = os.path.abspath(directory_path)
        
        # Collect files only in the current directory
        files = []
        for item in os.listdir(directory_path):
            # Skip hidden files and temporary files
            if item.startswith('.') or item.endswith('.tmp'):
                continue
            item_path = os.path.join(directory_path, item)
            if os.path.isfile(item_path) and self._is_programming_file(item_path):
                files.append(item_path)
        
        # Sort files for consistent output
        files.sort()
        
        # Generate the JSON content
        content = self._generate_json_content(abs_directory_path, files)
        
        # Write atomically using temporary file
        self._write_json_atomically(content, output_filename)
            
        print(f"TLDR file created: {output_filename}")
    
    def _process_directories_recursively(self, root_directory, base_output_filename):
        """
        Process directories recursively, creating one large TLDR file in the base directory
        with information for all directories that contain programming files.
        
        Args:
            root_directory (str): Root directory to start from
            base_output_filename (str): Base output filename (used for the single output file)
        """
        processed_count = 0
        all_directories = []
        
        # Walk through all directories
        for root, dirs, filenames in os.walk(root_directory):
            # Filter out hidden directories from dirs list to prevent os.walk from traversing them
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            # Check if this directory has any programming files
            programming_files = []
            for filename in filenames:
                # Skip hidden files and temporary files
                if filename.startswith('.') or filename.endswith('.tmp'):
                    continue
                item_path = os.path.join(root, filename)
                if self._is_programming_file(item_path):
                    programming_files.append(item_path)
            
            # Only process directory if it has programming files
            if programming_files:
                # Sort files for consistent output
                programming_files.sort()
                
                # Generate the JSON content for this directory
                abs_directory_path = os.path.abspath(root)
                directory_content = self._generate_json_content(abs_directory_path, programming_files)
                all_directories.append(directory_content)
                
                print(f"Processed directory: {abs_directory_path}")
                processed_count += 1
        
        # Create the combined JSON structure
        if all_directories:
            # Set default output filename if not provided
            if base_output_filename is None:
                output_filename = 'tldr_combined.json'
                # output_filename = os.path.join(root_directory, 'tldr_combined.json')
            else:
                output_filename = base_output_filename
                # Ensure the output file is in the base directory
                # if not os.path.isabs(base_output_filename):
                #     output_filename = os.path.join(root_directory, base_output_filename)
                # else:
                #     output_filename = base_output_filename
            
            timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            combined_content = {
                "root_directory": os.path.abspath(root_directory),
                "last_updated": timestamp,
                "total_directories_processed": processed_count,
                "directories": all_directories
            }
            
            # Write the combined file atomically
            self._write_json_atomically(combined_content, output_filename)
            
            print(f"Combined TLDR file created: {output_filename}")
        
        print(f"Recursive processing complete. Processed {processed_count} directories into one file.")
        
    def _generate_json_content(self, directory_path, files):
        """
        Generates the JSON content for the TLDR file.
        
        Args:
            directory_path (str): Absolute path to the directory
            files (list): List of file paths to process
            
        Returns:
            dict: Generated JSON content
        """
        # Current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Start building the JSON structure
        json_data = {
            "directory_path": directory_path,
            "files": []
        }
        
        # Process each file
        for file_path in files:
            abs_file_path = os.path.abspath(file_path)
            
            # Extract signatures using signature_extractor
            try:
                signatures_text = self.signature_extractor.get_signatures(file_path)
                signatures_list = self._parse_signatures(signatures_text)
            except Exception as e:
                logging.warning(f"Could not extract signatures from {file_path}: {e}")
                signatures_list = [f"Error extracting signatures: {e}"]
                raise

            file_data = {
                "file_path": abs_file_path,
                "last_scanned": timestamp,
                "signatures": signatures_list
            }
            
            # Generate AI-powered summary if LLM provider is available and not skipped
            if not self.skip_file_summary:
                logging.debug(f"Generating file summary from LLM for {file_path}")
                summary = self._generate_file_summary(file_path, signatures_text)
                file_data["summary"] = summary
            else:
                logging.debug(f"Skipping file summary generation for {file_path}")
            
            json_data["files"].append(file_data)

        return json_data

    def _is_programming_file(self, file_path):
        """
        Check if file has a known programming extension and is recognized by Pygments.
        
        Args:
            file_path (str): Path to the file to check
            
        Returns:
            bool: True if file is a programming language, False otherwise
        """
        # Common programming file extensions
        programming_extensions = {
            '.py', '.pyx', '.pyi',  # Python
            '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',  # JavaScript/TypeScript
            '.java', '.kt', '.kts',  # Java/Kotlin
            '.c', '.h', '.cpp', '.hpp', '.cc', '.cxx', '.c++',  # C/C++
            '.cs', '.vb',  # C#/VB.NET
            '.php', '.php3', '.php4', '.php5', '.phtml',  # PHP
            '.rb', '.rbw',  # Ruby
            '.go',  # Go
            '.rs',  # Rust
            '.swift',  # Swift
            '.m', '.mm',  # Objective-C
            '.scala', '.sc',  # Scala
            '.pl', '.pm', '.pod',  # Perl
            '.sh', '.bash', '.zsh', '.fish',  # Shell scripts
            '.ps1', '.psm1', '.psd1',  # PowerShell
            '.r', '.R',  # R
            '.matlab', '.m',  # MATLAB
            '.lua',  # Lua
            '.dart',  # Dart
            '.ex', '.exs',  # Elixir
            '.erl', '.hrl',  # Erlang
            '.hs', '.lhs',  # Haskell
            '.clj', '.cljs', '.cljc',  # Clojure
            '.fs', '.fsx', '.fsi',  # F#
            '.ml', '.mli',  # OCaml
            '.pas', '.pp', '.inc',  # Pascal
            '.ada', '.adb', '.ads',  # Ada
            '.d',  # D
            '.nim',  # Nim
            '.crystal', '.cr',  # Crystal
            '.zig',  # Zig
            '.v',  # V
            '.jl',  # Julia
            '.groovy', '.gvy', '.gy', '.gsh',  # Groovy
        }
        
        # Get file extension
        _, ext = os.path.splitext(file_path.lower())
        
        # First check if it has a known programming extension
        if ext not in programming_extensions:
            logging.debug(f"Excluding file {file_path} (unknown programming extension: {ext})")
            return False
        
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

    def _parse_signatures(self, signatures_text: str) -> list:
        """
        Parse signatures text into a list of individual signatures.
        
        Args:
            signatures_text (str): Raw signatures text from signature extractor
            
        Returns:
            list: List of individual signatures
        """
        if not signatures_text or not signatures_text.strip():
            return []
        
        # Split by lines and clean up
        lines = signatures_text.strip().split('\n')
        signatures = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                # Remove markdown formatting if present
                if line.startswith('- '):
                    line = line[2:]
                elif line.startswith('* '):
                    line = line[2:]
                
                # Remove code block markers if present
                if line.startswith('```') or line.endswith('```'):
                    continue
                    
                signatures.append(line)
        
        return signatures

    def _write_json_atomically(self, content: dict, output_filename: str):
        """
        Write JSON content atomically using temporary file and move operation.
        
        This ensures that readers never see a partially written file, and the
        operation is atomic on most filesystems.
        
        Args:
            content (dict): JSON content to write
            output_filename (str): Final output file path
        """
        # Get directory for temporary file (same as target for atomic move)
        output_dir = os.path.dirname(os.path.abspath(output_filename))
        
        # Create temporary file in the same directory as target
        temp_fd, temp_path = tempfile.mkstemp(
            suffix='.json.tmp', 
            prefix='tldr_',
            dir=output_dir
        )
        
        try:
            # Write to temporary file
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            
            # Atomic move (on most filesystems)
            if os.name == 'nt':  # Windows
                # Windows doesn't allow atomic replace of existing files
                if os.path.exists(output_filename):
                    os.unlink(output_filename)
            
            shutil.move(temp_path, output_filename)
            logging.debug(f"Atomically wrote JSON to {output_filename}")
            
        except Exception as e:
            # Clean up temporary file if something goes wrong
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass
            raise Exception(f"Failed to write JSON file atomically: {e}")


def main():
    """
    Main function to handle command line arguments and create TLDR file.
    """
    import argparse
    
    class CustomHelpFormatter(argparse.HelpFormatter):
        def format_help(self):
            help_text = super().format_help()
            
            # Add LLM setup instructions
            llm_setup = "\n\nLLM PROVIDER SETUP:\n"
            llm_setup += "=" * 20 + "\n"
            
            providers = LLMConfig.get_supported_providers()
            for provider, env_var in providers.items():
                llm_setup += f"\nFor {provider.upper()}:\n"
                llm_setup += f"  export {env_var}='your-api-key-here'\n"
            
            llm_setup += "\nExample usage:\n"
            llm_setup += "  python tldr_file_creator.py ./src\n"
            llm_setup += "  python tldr_file_creator.py ./src my_output.json\n"
            llm_setup += "\nNote: Directories are processed recursively by default.\n"
            
            return help_text + llm_setup
    
    parser = argparse.ArgumentParser(
        description='Creates TLDR JSON file for all file and directories under the directory_path'
        # ,
        # formatter_class=CustomHelpFormatter
    )
    parser.add_argument('directory_path', help='Path to the directory to scan (processed recursively)')
    parser.add_argument('output_filename', nargs='?', help='Optional output filename (defaults to tldr.json)')
    # parser.add_argument('--llm', choices=LLMFactory.available_providers(),
    #                    help='LLM provider to use for generating summaries')
    # parser.add_argument('--include-file-summary', action='store_true',
    #                    help='Include AI-generated file summaries (requires --llm)')
    
    args = parser.parse_args()
    
    # Note: File summaries and LLM functionality appear to be commented out
    # Default behavior is now recursive processing
    
    try:
        creator = TLDRFileCreator()
        creator.create_tldr_file(args.directory_path, args.output_filename, recursive=True)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
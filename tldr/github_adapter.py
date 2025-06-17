#!/usr/bin/env python3
"""
GitHubAdapter.py - Downloads GitHub repositories and creates TLDR files

This script downloads a GitHub repository to a local directory and then
processes it with TLDRFileCreator to generate a .tldr file.

Usage:
    from github_adapter import GitHubAdapter
    adapter = GitHubAdapter()
    adapter.process_github_repo("https://github.com/user/repo", output_dir="./downloads")
"""

import os
import sys
import logging
import tempfile
import shutil
import subprocess
import traceback
import time
from pathlib import Path
from urllib.parse import urlparse

from tldr_file_creator import TLDRFileCreator

# Configure logging to write to both console and file
def setup_logging():
    """Setup logging configuration for github_adapter"""
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'github_adapter.log')
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s(): - %(message)s"
    )
    
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logging.info(f"Logging configured. Log file: {log_file}")

# Setup logging when module is imported
setup_logging()

class GitHubAdapter:
    def __init__(self, llm_provider: str = None, skip_file_summary: bool = True):
        """
        Initialize the GitHub adapter.
        
        Args:
            llm_provider (str): Optional LLM provider for generating summaries (default: None)
            skip_file_summary (bool): Skip generating file summaries using LLM (default: True)
        """
        self.llm_provider = llm_provider
        self.skip_file_summary = skip_file_summary
        
    def process_github_repo(self, github_url: str, output_dir: str = None, cleanup: bool = True, recursive: bool = True):
        """
        Download a GitHub repository and create a TLDR file.
        
        Args:
            github_url (str): GitHub repository URL (e.g., https://github.com/user/repo)
            output_dir (str): Directory to download the repo to. If None, uses temp directory
            cleanup (bool): Whether to clean up the downloaded repo after processing
            recursive (bool): Whether to process subdirectories recursively (default: True)
            
        Returns:
            str: Path to the generated TLDR file
        """
        start_time = time.time()
        logging.info(f"Starting GitHub repository processing for: {github_url}")
        
        # Validate GitHub URL
        if not self._is_valid_github_url(github_url):
            raise ValueError(f"Invalid GitHub URL: {github_url}")
        
        # Extract repo name from URL
        repo_name = self._extract_repo_name(github_url)
        
        # Set up download directory
        if output_dir is None:
            temp_dir = tempfile.mkdtemp(prefix=f"github_{repo_name}_")
            download_path = temp_dir
            should_cleanup_temp = True
        else:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            download_path = os.path.join(output_dir, repo_name)
            should_cleanup_temp = False
        
        try:
            download_start = time.time()
            logging.info(f"Downloading repository {github_url} to {download_path}")
            
            # Download the repository
            self._download_repo(github_url, download_path)
            download_end = time.time()
            logging.info(f"Repository download completed in {download_end - download_start:.2f} seconds")
            
            # Create TLDR file
            tldr_start = time.time()
            tldr_filename = os.path.join(download_path, f"{repo_name}.tldr.json")
            logging.info(f"Creating TLDR file: {tldr_filename}")
            
            creator = TLDRFileCreator(llm_provider=self.llm_provider, skip_file_summary=self.skip_file_summary)
            creator.create_tldr_file(download_path, tldr_filename, recursive=recursive)
            tldr_end = time.time()
            logging.info(f"TLDR file creation completed in {tldr_end - tldr_start:.2f} seconds")
            
            # Copy TLDR file to output directory if using temp directory
            if should_cleanup_temp and output_dir:
                os.makedirs(output_dir, exist_ok=True)
                final_tldr_path = os.path.join(output_dir, f"{repo_name}.tldr")
                shutil.copy2(tldr_filename, final_tldr_path)
                logging.info(f"TLDR file copied to: {final_tldr_path}")
                final_result = final_tldr_path
            else:
                final_result = tldr_filename
            
            total_time = time.time() - start_time
            logging.info(f"GitHub repository processing completed in {total_time:.2f} seconds total")
            return final_result
                
        except Exception as e:
            total_time = time.time() - start_time
            logging.error(f"Error processing repository {github_url} after {total_time:.2f} seconds: {e}")
            raise
        finally:
            # Clean up temporary directory if requested
            if cleanup and should_cleanup_temp:
                try:
                    shutil.rmtree(download_path)
                    logging.info(f"Cleaned up temporary directory: {download_path}")
                except Exception as e:
                    logging.warning(f"Failed to clean up temporary directory {download_path}: {e}")
    
    def _is_valid_github_url(self, url: str) -> bool:
        """
        Validate if the URL is a valid GitHub repository URL.
        
        Args:
            url (str): URL to validate
            
        Returns:
            bool: True if valid GitHub URL, False otherwise
        """
        try:
            parsed = urlparse(url)
            
            # Check if it's a GitHub URL
            if parsed.netloc.lower() not in ['github.com', 'www.github.com']:
                return False
            
            # Check if path has at least user/repo format
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                return False
            
            # Basic validation that user and repo names aren't empty
            if not path_parts[0] or not path_parts[1]:
                return False
                
            return True
            
        except Exception:
            return False
    
    def _extract_repo_name(self, github_url: str) -> str:
        """
        Extract repository name from GitHub URL.
        
        Args:
            github_url (str): GitHub repository URL
            
        Returns:
            str: Repository name
        """
        parsed = urlparse(github_url)
        path_parts = parsed.path.strip('/').split('/')
        
        # Remove .git suffix if present
        repo_name = path_parts[1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
            
        return repo_name
    
    def _download_repo(self, github_url: str, local_path: str):
        """
        Download repository using git clone.
        
        Args:
            github_url (str): GitHub repository URL
            local_path (str): Local path to clone to
        """
        try:
            # Remove directory if it already exists
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
            
            # Clone the repository
            cmd = ['git', 'clone', github_url, local_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logging.debug(f"Git clone output: {result.stdout}")
            
            if not os.path.exists(local_path):
                raise Exception("Repository was not cloned successfully")
                
            logging.info(f"Successfully cloned repository to {local_path}")
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Git clone failed: {e.stderr if e.stderr else str(e)}"
            logging.error(error_msg)
            raise Exception(error_msg)
        except FileNotFoundError:
            raise Exception("Git is not installed or not in PATH. Please install Git to use this feature.")
        except Exception as e:
            logging.error(f"Failed to download repository: {e}")
            raise

def main():
    """
    Main function for command line usage.
    """
    import argparse
    # from llm_providers import LLMFactory  # No longer needed since we don't use LLM features
    
    parser = argparse.ArgumentParser(description='Download GitHub repository and create TLDR file with function signatures (processes recursively, no file summaries)')
    parser.add_argument('github_url', help='GitHub repository URL')
    parser.add_argument('-o', '--output-dir', help='Output directory for downloaded repo and TLDR file')
    parser.add_argument('--no-cleanup', action='store_true', help='Keep downloaded repository after processing')
    
    args = parser.parse_args()
    
    try:
        adapter = GitHubAdapter(llm_provider=None, skip_file_summary=True)
        tldr_file = adapter.process_github_repo(
            github_url=args.github_url,
            output_dir=args.output_dir,
            cleanup=not args.no_cleanup,
            recursive=True
        )
        print(f"TLDR file created: {tldr_file}")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        stack_trace = traceback.format_exc()
        logging.error("Stack trace:\n", stack_trace)

        sys.exit(1)

if __name__ == '__main__':
    main()
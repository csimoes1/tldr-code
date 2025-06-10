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
from pathlib import Path
from urllib.parse import urlparse

from TLDRFileCreator import TLDRFileCreator

class GitHubAdapter:
    def __init__(self, llm_provider: str = None):
        """
        Initialize the GitHub adapter.
        
        Args:
            llm_provider (str): Optional LLM provider for generating summaries
        """
        self.llm_provider = llm_provider
        
    def process_github_repo(self, github_url: str, output_dir: str = None, cleanup: bool = True, recursive: bool = True):
        """
        Download a GitHub repository and create a TLDR file.
        
        Args:
            github_url (str): GitHub repository URL (e.g., https://github.com/user/repo)
            output_dir (str): Directory to download the repo to. If None, uses temp directory
            cleanup (bool): Whether to clean up the downloaded repo after processing
            recursive (bool): Whether to process subdirectories recursively
            
        Returns:
            str: Path to the generated TLDR file
        """
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
            logging.info(f"Downloading repository {github_url} to {download_path}")
            
            # Download the repository
            self._download_repo(github_url, download_path)
            
            # Create TLDR file
            tldr_filename = os.path.join(download_path, f"{repo_name}.tldr")
            logging.info(f"Creating TLDR file: {tldr_filename}")
            
            creator = TLDRFileCreator(llm_provider=self.llm_provider)
            creator.create_tldr_file(download_path, tldr_filename, recursive=recursive)
            
            # Copy TLDR file to output directory if using temp directory
            if should_cleanup_temp and output_dir:
                os.makedirs(output_dir, exist_ok=True)
                final_tldr_path = os.path.join(output_dir, f"{repo_name}.tldr")
                shutil.copy2(tldr_filename, final_tldr_path)
                logging.info(f"TLDR file copied to: {final_tldr_path}")
                return final_tldr_path
            else:
                return tldr_filename
                
        except Exception as e:
            logging.error(f"Error processing repository {github_url}: {e}")
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
    from llm_providers import LLMFactory
    
    parser = argparse.ArgumentParser(description='Download GitHub repository and create TLDR file')
    parser.add_argument('github_url', help='GitHub repository URL')
    parser.add_argument('-o', '--output-dir', help='Output directory for downloaded repo and TLDR file')
    parser.add_argument('--no-cleanup', action='store_true', help='Keep downloaded repository after processing')
    parser.add_argument('--no-recursive', action='store_true', help='Do not process subdirectories recursively')
    parser.add_argument('--llm', choices=LLMFactory.available_providers(), 
                       help='LLM provider to use for generating summaries')
    
    args = parser.parse_args()
    
    try:
        adapter = GitHubAdapter(llm_provider=args.llm)
        tldr_file = adapter.process_github_repo(
            github_url=args.github_url,
            output_dir=args.output_dir,
            cleanup=not args.no_cleanup,
            recursive=not args.no_recursive
        )
        print(f"TLDR file created: {tldr_file}")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        stack_trace = traceback.format_exc()
        logging.error("Stack trace:\n", stack_trace)

        sys.exit(1)

if __name__ == '__main__':
    main()
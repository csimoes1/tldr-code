"""
TLDR - Function Signature Extractor

A Python tool that extracts function signatures from large codebases 
and generates concise summaries for LLM context preparation.
"""

__version__ = "0.1.0"
__author__ = "Chris Simoes"
__email__ = "csimoes1@gmail.com"

from .tldr_file_creator import TLDRFileCreator
from .signature_extractor_pygments import SignatureExtractor
from .github_adapter import GitHubAdapter

__all__ = [
    "TLDRFileCreator",
    "SignatureExtractor", 
    "GitHubAdapter",
]
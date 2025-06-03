#!/usr/bin/env python3
"""
llm_provider.py - Abstract base class for LLM providers

This module defines the interface that all LLM providers must implement
for generating file summaries in the TLDR system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider"""
    content: str
    usage: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    provider: Optional[str] = None


class LLMProvider(ABC):
    """Abstract base class for all LLM providers"""
    
    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model or self.get_default_model()
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Return the default model for this provider"""
        pass
    
    @abstractmethod
    def generate_summary(self, file_path: str, file_content: str, signatures: str) -> LLMResponse:
        """Generate a file summary given the file content and signatures"""
        pass
    
    @abstractmethod
    def _make_api_call(self, prompt: str, max_tokens: int) -> LLMResponse:
        """Make the actual API call to the LLM provider"""
        pass
    
    def _build_summary_prompt(self, file_path: str, file_content: str, signatures: str) -> str:
        """Build a standardized prompt for file summarization"""
        return f"""Analyze this code file and provide a concise summary (under 500 characters) of what it does.

File: {file_path}

Signatures:
{signatures}

Code:
{file_content}

Provide a clear, technical summary focusing on the file's main purpose and functionality. Keep it under 500 characters."""
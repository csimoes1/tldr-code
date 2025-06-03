#!/usr/bin/env python3
"""
claude_provider.py - Claude (Anthropic) LLM provider implementation

This module implements the Claude LLM provider for generating file summaries.
"""

import logging
from .llm_provider import LLMProvider, LLMResponse


class ClaudeProvider(LLMProvider):
    """Claude (Anthropic) LLM provider implementation"""
    
    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key, model)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package is required for Claude provider. Install with: pip install anthropic")
    
    def get_default_model(self) -> str:
        """Return the default Claude model"""
        return "claude-sonnet-4-20250514"
    
    def generate_summary(self, file_path: str, file_content: str, signatures: str) -> LLMResponse:
        """Generate a file summary using Claude"""
        prompt = self._build_summary_prompt(file_path, file_content, signatures)
        return self._make_api_call(prompt, max_tokens=200)
    
    def _make_api_call(self, prompt: str, max_tokens: int = 200) -> LLMResponse:
        """Make the actual API call to Claude"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,  # Use the passed parameter with default 200
                temperature=0.3,  # Low temperature for consistent technical summaries
                messages=[{"role": "user", "content": prompt}]
            )
            logging.debug(f"Claude response: {response}")
            
            return LLMResponse(
                content=response.content[0].text,
                usage=response.usage if response.usage else None,
                model=self.model,
                provider="claude"
            )
        except Exception as e:
            logging.error(f"Claude API error: {e}")
            raise Exception(f"Claude API error: {e}")
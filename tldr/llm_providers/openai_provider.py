#!/usr/bin/env python3
"""
openai_provider.py - OpenAI LLM provider implementation

This module implements the OpenAI LLM provider for generating file summaries.
"""

import logging
from .llm_provider import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation"""
    
    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key, model)
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai package is required for OpenAI provider. Install with: pip install openai")
    
    def get_default_model(self) -> str:
        """Return the default OpenAI model"""
        return "gpt-4-turbo-preview"
    
    def generate_summary(self, file_path: str, file_content: str, signatures: str) -> LLMResponse:
        """Generate a file summary using OpenAI"""
        prompt = self._build_summary_prompt(file_path, file_content, signatures)
        return self._make_api_call(prompt)
    
    def _make_api_call(self, prompt: str, max_tokens: int) -> LLMResponse:
        """Make the actual API call to OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,  # Keep summaries concise
                temperature=0.3  # Low temperature for consistent technical summaries
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                usage=response.usage._asdict() if response.usage else None,
                model=self.model,
                provider="openai"
            )
        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI API error: {e}")
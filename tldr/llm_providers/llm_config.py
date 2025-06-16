#!/usr/bin/env python3
"""
llm_config.py - Configuration management for LLM providers

This module handles configuration and API key management for different LLM providers.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    provider: str
    api_key: str
    model: Optional[str] = None
    
    @classmethod
    def from_env(cls, provider: str, model: str = None) -> 'LLMConfig':
        """
        Create config from environment variables
        
        Args:
            provider (str): Name of the LLM provider
            model (str, optional): Specific model to use
            
        Returns:
            LLMConfig: Configuration instance
            
        Raises:
            ValueError: If provider is not supported or API key not found
        """
        env_var_map = {
            'claude': 'ANTHROPIC_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'grok': 'GROK_API_KEY',
        }
        
        provider_lower = provider.lower()
        env_var = env_var_map.get(provider_lower)
        if not env_var:
            available_providers = list(env_var_map.keys())
            raise ValueError(f"No environment variable mapping for provider: {provider}. "
                           f"Available providers: {available_providers}")
        
        api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(f"API key not found in environment variable: {env_var}. "
                           f"Please set {env_var} with your API key.")
        
        return cls(provider=provider_lower, api_key=api_key, model=model)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, str]) -> 'LLMConfig':
        """
        Create config from dictionary
        
        Args:
            config_dict (Dict[str, str]): Configuration dictionary
            
        Returns:
            LLMConfig: Configuration instance
        """
        required_keys = ['provider', 'api_key']
        for key in required_keys:
            if key not in config_dict:
                raise ValueError(f"Missing required configuration key: {key}")
        
        return cls(
            provider=config_dict['provider'],
            api_key=config_dict['api_key'],
            model=config_dict.get('model')
        )
    
    @staticmethod
    def get_supported_providers() -> Dict[str, str]:
        """
        Get mapping of supported providers to their environment variables
        
        Returns:
            Dict[str, str]: Mapping of provider names to environment variable names
        """
        return {
            'claude': 'ANTHROPIC_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'grok': 'GROK_API_KEY',
        }
    
    @staticmethod
    def print_env_setup_instructions():
        """Print instructions for setting up environment variables"""
        print("LLM Provider Setup Instructions:")
        print("=" * 40)
        
        providers = LLMConfig.get_supported_providers()
        for provider, env_var in providers.items():
            print(f"\nFor {provider.upper()}:")
            print(f"  export {env_var}='your-api-key-here'")
        
        print("\nExample usage:")
        print("  python tldr_file_creator.py ./src --llm claude")
        print("  python tldr_file_creator.py ./src --llm openai")
        print("  python tldr_file_creator.py ./src --llm grok")
    
    def validate(self) -> bool:
        """
        Validate the configuration
        
        Returns:
            bool: True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.provider:
            raise ValueError("Provider cannot be empty")
        
        if not self.api_key:
            raise ValueError("API key cannot be empty")
        
        supported_providers = self.get_supported_providers()
        if self.provider.lower() not in supported_providers:
            available = list(supported_providers.keys())
            raise ValueError(f"Unsupported provider: {self.provider}. Available: {available}")
        
        return True
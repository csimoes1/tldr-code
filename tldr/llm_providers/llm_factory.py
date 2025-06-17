#!/usr/bin/env python3
"""
llm_factory.py - Factory for creating LLM provider instances

This module provides a factory pattern for creating different LLM providers
and managing their registration.
"""

import logging
from typing import Dict, Type
from .llm_provider import LLMProvider


class LLMFactory:
    """Factory for creating LLM provider instances"""
    
    _providers: Dict[str, Type[LLMProvider]] = {}
    
    @classmethod
    def _initialize_providers(cls):
        """Initialize built-in providers (lazy loading)"""
        if not cls._providers:
            try:
                from .claude_provider import ClaudeProvider
                cls._providers['claude'] = ClaudeProvider
            except ImportError as e:
                logging.warning(f"Claude provider not available: {e}")
            
            try:
                from .grok_provider import GrokProvider
                cls._providers['grok'] = GrokProvider
            except ImportError as e:
                logging.warning(f"Grok provider not available: {e}")
    
    @classmethod
    def create_provider(cls, provider_name: str, api_key: str, model: str = None) -> LLMProvider:
        """
        Create an LLM provider instance
        
        Args:
            provider_name (str): Name of the provider ('claude', 'openai', etc.)
            api_key (str): API key for the provider
            model (str, optional): Specific model to use
            
        Returns:
            LLMProvider: Configured provider instance
            
        Raises:
            ValueError: If provider name is not recognized
            ImportError: If required dependencies are not installed
        """
        cls._initialize_providers()
        
        if provider_name.lower() not in cls._providers:
            available = list(cls._providers.keys())
            raise ValueError(f"Unknown provider '{provider_name}'. Available: {available}")
        
        provider_class = cls._providers[provider_name.lower()]
        return provider_class(api_key=api_key, model=model)
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[LLMProvider]):
        """
        Register a new provider (for extensibility)
        
        Args:
            name (str): Name to register the provider under
            provider_class (Type[LLMProvider]): Provider class to register
        """
        cls._providers[name.lower()] = provider_class
        logging.info(f"Registered LLM provider: {name}")
    
    @classmethod
    def available_providers(cls) -> list:
        """
        Get list of available provider names
        
        Returns:
            list: List of available provider names
        """
        cls._initialize_providers()
        return list(cls._providers.keys())
    
    @classmethod
    def is_provider_available(cls, provider_name: str) -> bool:
        """
        Check if a provider is available
        
        Args:
            provider_name (str): Name of the provider to check
            
        Returns:
            bool: True if provider is available, False otherwise
        """
        cls._initialize_providers()
        return provider_name.lower() in cls._providers
#!/usr/bin/env python3
"""
grok_provider.py - Grok (xAI) LLM provider implementation

This module implements the Grok LLM provider for generating file summaries.
Grok typically uses an OpenAI-compatible API structure.
"""

import logging
import requests
import json

from .llm_provider import LLMProvider, LLMResponse


class GrokProvider(LLMProvider):
    """Grok (xAI) LLM provider implementation"""
    
    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key, model)
        self.base_url = "https://api.x.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_default_model(self) -> str:
        """Return the default Grok model"""
        return "grok-3"
    
    def generate_summary(self, file_path: str, file_content: str, signatures: str) -> LLMResponse:
        """Generate a file summary using Grok"""
        prompt = self._build_summary_prompt(file_path, file_content, signatures)
        return self._make_api_call(prompt, max_tokens=200)
    
    def _make_api_call(self, prompt: str, max_tokens: int = 200) -> LLMResponse:
        """Make the actual API call to Grok"""
        try:
            # Prepare the request payload (OpenAI-compatible format)
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3,  # Low temperature for consistent technical summaries
                "stream": False
            }
            
            # Make the API request
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            logging.debug(f"Grok response: {response_data}")
            
            # Extract the content from the response
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
                
                # Extract usage information if available
                usage_info = response_data.get("usage", {})
                
                return LLMResponse(
                    content=content,
                    usage=usage_info,
                    model=self.model,
                    provider="grok"
                )
            else:
                raise Exception("No valid response from Grok API")
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Grok API request error: {e}")
            raise Exception(f"Grok API request error: {e}")
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse Grok API response: {e}")
            raise Exception(f"Failed to parse Grok API response: {e}")
        except KeyError as e:
            logging.error(f"Unexpected Grok API response format: {e}")
            raise Exception(f"Unexpected Grok API response format: {e}")
        except Exception as e:
            logging.error(f"Grok API error: {e}")
            raise Exception(f"Grok API error: {e}")

    def get_available_models(self) -> list:
        """
        Get list of available models from Grok API
        
        Returns:
            list: List of available model names
        """
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            models_data = response.json()
            if "data" in models_data:
                return [model["id"] for model in models_data["data"]]
            else:
                logging.warning("No models data in Grok API response")
                return [self.get_default_model()]
                
        except Exception as e:
            logging.warning(f"Failed to fetch Grok models: {e}")
            return [self.get_default_model()]


# Example usage and testing
if __name__ == '__main__':
    import os
    
    def test_grok_provider():
        """Test the Grok provider"""
        api_key = os.getenv('GROK_API_KEY')
        if not api_key:
            print("Please set GROK_API_KEY environment variable")
            return
        
        try:
            provider = GrokProvider(api_key)
                        
            # Test available models
            print("\nFetching available models...")
            models = provider.get_available_models()
            print(f"Available models: {models}")
            
            # Test summary generation
            print("\nTesting summary generation...")
            test_code = '''
def hello_world():
    """Print hello world message"""
    print("Hello, World!")

class Calculator:
    def add(self, a, b):
        return a + b
'''
            
            response = provider.generate_summary("test.py", test_code, "def hello_world()\nclass Calculator\ndef add(self, a, b)")
            print(f"Generated summary: {response.content}")
            print(f"Usage: {response.usage}")
            
        except Exception as e:
            print(f"Error testing Grok provider: {e}")
    
    test_grok_provider()
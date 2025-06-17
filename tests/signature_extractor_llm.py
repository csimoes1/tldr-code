#!/usr/bin/env python3
"""
signature_extractor_llm.py - LLM-based signature extraction

This module uses Claude LLM to extract function signatures, class definitions,
and other important code signatures from source files. It provides an alternative
to the pygments-based signature_extractor.py.

Usage:
    from signature_extractor_llm import SignatureExtractorLLM
    
    extractor = SignatureExtractorLLM()
    signatures = extractor.get_signatures('path/to/file.py')
"""

import logging
import os
from typing import Optional
from pygments_tldr.lexers import get_lexer_for_filename
from pygments_tldr.util import ClassNotFound
from tldr.llm_providers import LLMFactory, LLMConfig


class SignatureExtractorLLM:
    """LLM-based signature extractor using Claude"""
    
    def __init__(self, llm_provider: str = 'claude'):
        """
        Initialize the LLM signature extractor
        
        Args:
            llm_provider (str): LLM provider to use ('claude' or 'openai')
        """
        self.llm_provider = None
        self._setup_llm_provider(llm_provider)
    
    def _setup_llm_provider(self, provider_name: str):
        """Setup LLM provider for signature extraction"""
        try:
            config = LLMConfig.from_env(provider_name)
            self.llm_provider = LLMFactory.create_provider(
                provider_name=config.provider,
                api_key=config.api_key,
                model=config.model
            )
            logging.info(f"LLM signature extractor initialized with '{provider_name}' provider")
        except Exception as e:
            logging.error(f"Failed to initialize LLM provider '{provider_name}': {e}")
            self.llm_provider = None
            raise
    
    def get_signatures(self, filename: str) -> str:
        """
        Extract signatures from the provided file using LLM.
        
        Args:
            filename (str): Path to the file to analyze
            
        Returns:
            str: Extracted signatures as formatted text
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            Exception: If LLM provider is not available or API call fails
        """
        # Check if file exists
        if not os.path.exists(filename):
            logging.error(f"Error: File '{filename}' not found.")
            raise FileNotFoundError(f"File '{filename}' does not exist.")
        
        if not self.llm_provider:
            raise Exception("LLM provider not available. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable.")
        
        try:
            # Read the file content
            with open(filename, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Detect the programming language
            language = self._detect_language(filename)
            
            # Create the extraction prompt
            prompt = self._build_signature_extraction_prompt(filename, file_content, language)
            logging.debug(f"Generated prompt for {filename}:\n{prompt}")

            # Get LLM response
            response = self.llm_provider._make_api_call(prompt, max_tokens=2000)
            logging.debug(f"LLM response for {filename}:\n{response.content}")

            # Extract and clean the signatures from the response
            signatures = self._parse_llm_response(response.content)
            
            logging.debug(f"LLM extracted signatures from {filename}:\n{signatures}")
            return signatures
            
        except Exception as e:
            logging.error(f"Error processing file {filename}: {e}")
            raise
    
    def _detect_language(self, filename: str) -> str:
        """
        Detect the programming language of the file
        
        Args:
            filename (str): Path to the file
            
        Returns:
            str: Detected language name
        """
        try:
            lexer = get_lexer_for_filename(filename)
            if hasattr(lexer, 'aliases') and lexer.aliases:
                return lexer.aliases[0]
            else:
                return lexer.__class__.__name__.replace('Lexer', '').lower()
        except ClassNotFound:
            # Try to guess from file extension
            ext = os.path.splitext(filename)[1].lower()
            ext_map = {
                '.py': 'python',
                '.java': 'java',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.cpp': 'cpp',
                '.c': 'c',
                '.h': 'c',
                '.cs': 'csharp',
                '.rb': 'ruby',
                '.go': 'go',
                '.rs': 'rust',
                '.php': 'php',
                '.swift': 'swift',
                '.kt': 'kotlin',
                '.scala': 'scala'
            }
            return ext_map.get(ext, 'unknown')
    
    def _build_signature_extraction_prompt(self, filename: str, file_content: str, language: str) -> str:
        """
        Build a prompt for LLM signature extraction
        
        Args:
            filename (str): Path to the file
            file_content (str): Content of the file
            language (str): Programming language
            
        Returns:
            str: Formatted prompt for signature extraction
        """
        return f"""You are a code analysis expert. Extract ALL function signatures, method signatures, class definitions, and other important code constructs from the following {language} file.

FILE: {filename}
LANGUAGE: {language}

CODE:
```{language}
{file_content}
```

Please extract and list ALL of the following that are present in the code:

1. **Function definitions** - Include function name, parameters, and return type if specified
2. **Class definitions** - Include class name and any inheritance
3. **Method definitions** - Include method name, parameters, and return type if specified  
4. **Constructor definitions** - Include constructor signatures
5. **Interface/Abstract class definitions** - If applicable to the language
6. **Important constants/variables** - Module-level or class-level constants
7. **Enum definitions** - If present
8. **Type definitions** - If the language supports custom types

Format your response as a clean list, one signature per line. Do not include implementation details, only the signatures. For example:

```
class MyClass:
def __init__(self, param1: str, param2: int)
def my_method(self, arg1: str) -> bool
def static_method() -> None
MY_CONSTANT = "value"
```

Focus on extracting the essential structural elements that define the API/interface of the code. Be thorough and ensure you don't miss any functions, methods, or classes.

EXTRACTED SIGNATURES:"""

    def _parse_llm_response(self, response_content: str) -> str:
        """
        Parse and clean the LLM response to extract just the signatures
        
        Args:
            response_content (str): Raw response from LLM
            
        Returns:
            str: Cleaned signatures text
        """
        lines = response_content.strip().split('\n')
        signature_lines = []
        in_code_block = False
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and common response prefixes
            if not line:
                continue
            if line.lower().startswith(('here are', 'the following', 'extracted signatures')):
                continue
            
            # Handle code blocks
            if line.startswith('```'):
                in_code_block = not in_code_block
                continue
            
            # If we're in a code block or line looks like a signature, include it
            if in_code_block or self._looks_like_signature(line):
                signature_lines.append(line)
        
        # Join and clean up the result
        result = '\n'.join(signature_lines)
        
        # Remove any remaining markdown formatting
        result = result.replace('**', '').replace('*', '')
        
        return result.strip()
    
    def _looks_like_signature(self, line: str) -> bool:
        """
        Check if a line looks like a code signature
        
        Args:
            line (str): Line to check
            
        Returns:
            bool: True if line appears to be a signature
        """
        line = line.strip()
        
        # Common signature patterns
        signature_patterns = [
            'class ',
            'def ',
            'function ',
            'public ',
            'private ',
            'protected ',
            'static ',
            'abstract ',
            'interface ',
            'enum ',
            'const ',
            'var ',
            'let ',
            'type ',
            '@',  # decorators/annotations
        ]
        
        # Check if line starts with any signature pattern
        for pattern in signature_patterns:
            if line.lower().startswith(pattern.lower()):
                return True
        
        # Check for method-like patterns (contains parentheses)
        if '(' in line and ')' in line:
            return True
        
        # Check for assignment patterns (constants/variables)
        if '=' in line and not line.startswith('#') and not line.startswith('//'):
            return True
        
        return False


# Example usage and testing
if __name__ == '__main__':
    def main():
        """
        Main function to test LLM signature extraction
        """
        # Test file path
        # filename = "/Users/csimoes/Projects/Python/tldr/tldr/llm_providers/claude_provider.py"
        filename = "/Users/csimoes/IdeaProjects/Amazon/AmazonScraper/adtrimmer-webapp/src/main/java/org/simoes"

        try:
            extractor = SignatureExtractorLLM()
            signatures = extractor.get_signatures(filename)
            logging.info(f"LLM extracted signatures:\n{signatures}")
            print(f"Extracted signatures from {filename}:")
            print("=" * 60)
            print(signatures)
            
        except Exception as e:
            logging.error(f"Error: {e}")
            print(f"Error: {e}")
    
    main()
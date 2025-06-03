#!/usr/bin/env python3
"""
test_signature_validation.py - Test signature extraction accuracy using LLM validation

This test validates that signature_extractor.py correctly extracts all function
signatures from a file by comparing its output with an LLM's assessment.
"""

import os
import sys
import logging
import pytest
from pathlib import Path

# Add parent directory to path to import tldr modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tldr'))

from tldr.signature_extractor_llm import SignatureExtractorLLM
from tldr.llm_providers import LLMFactory, LLMConfig


class TestSignatureValidation:
    """Test class for validating signature extraction accuracy"""
    
    def setup_method(self):
        """Setup test method - initialize signature extractor"""
        self.signature_extractor = SignatureExtractorLLM()
        
        # Try to initialize LLM provider from environment
        self.llm_provider = None
        for provider_name in ['grok']:
            try:
                config = LLMConfig.from_env(provider_name)
                self.llm_provider = LLMFactory.create_provider(
                    provider_name=config.provider,
                    api_key=config.api_key,
                    model=config.model
                )
                logging.info(f"Using LLM provider: {provider_name}")
                break
            except (ValueError, ImportError) as e:
                logging.debug(f"Could not initialize {provider_name} provider: {e}")
                raise
        
        if not self.llm_provider:
            pytest.skip("No LLM provider available. Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable.")
    
    def create_validation_prompt(self, file_path: str, file_content: str, extracted_signatures: str) -> str:
        """
        Create a prompt for the LLM to validate signature extraction
        
        Args:
            file_path (str): Path to the file being analyzed
            file_content (str): Content of the file
            extracted_signatures (str): Signatures extracted by signature_extractor
            
        Returns:
            str: Validation prompt for the LLM
        """
        return f"""You are a code analysis expert. Please analyze the following file and evaluate whether the signature extractor correctly identified ALL function signatures, method signatures, and other important code signatures.

FILE PATH: {file_path}

FILE CONTENT:
```
{file_content}
```

EXTRACTED SIGNATURES BY SIGNATURE_EXTRACTOR:
```
{extracted_signatures}
```

Please analyze the file and answer these questions:

1. Did the signature extractor find ALL function signatures in the file? List any missing functions.
2. Are there any false positives in the extracted signatures (things that aren't actually signatures)?

Provide your assessment in this format:

ASSESSMENT: [PASS/FAIL]
MISSING_SIGNATURES: [List any missing signatures, or "None" if all found]
FALSE_POSITIVES: [List any false positives, or "None" if none found]
EXPLANATION: [Brief explanation of your assessment]

Be thorough and precise in your analysis."""

    def validate_signatures_with_llm(self, file_path: str, extracted_signatures: str) -> dict:
        """
        Use LLM to validate extracted signatures
        
        Args:
            file_path (str): Path to the file that was analyzed
            extracted_signatures (str): Signatures extracted by signature_extractor
            
        Returns:
            dict: Validation results from LLM
        """
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # Create validation prompt
        prompt = self.create_validation_prompt(file_path, file_content, extracted_signatures)
        
        # Get LLM response using the private API call method with higher token limit for validation
        response = self.llm_provider._make_api_call(prompt, max_tokens=2000)
        logging.debug(f"LLM response: {response}")
        # Parse the response
        response_text = response.content.strip()
        
        # Extract structured information from response
        lines = response_text.split('\n')
        result = {
            'assessment': 'UNKNOWN',
            'missing_signatures': [],
            'false_positives': [],
            'explanation': '',
            'full_response': response_text
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith('ASSESSMENT:'):
                result['assessment'] = line.split(':', 1)[1].strip()
            elif line.startswith('MISSING_SIGNATURES:'):
                missing = line.split(':', 1)[1].strip()
                if missing.lower() != 'none':
                    result['missing_signatures'] = [s.strip() for s in missing.split(',')]
            elif line.startswith('FALSE_POSITIVES:'):
                false_pos = line.split(':', 1)[1].strip()
                if false_pos.lower() != 'none':
                    result['false_positives'] = [s.strip() for s in false_pos.split(',')]
            elif line.startswith('EXPLANATION:'):
                result['explanation'] = line.split(':', 1)[1].strip()
        
        return result

    def test_signature_extraction_on_python_file(self):
        """Test signature extraction on a Python file"""
        # Use the signature_extractor.py file itself as test input
        test_file = os.path.join(os.path.dirname(__file__), '..', 'tldr', 'signature_extractor.py')
        
        # Extract signatures
        extracted_signatures = self.signature_extractor.get_signatures(test_file)
        
        # Validate with LLM
        validation_result = self.validate_signatures_with_llm(test_file, extracted_signatures)
        
        # Log the results
        logging.info(f"Signature validation results for {test_file}:")
        logging.info(f"Assessment: {validation_result['assessment']}")
        logging.info(f"Missing signatures: {validation_result['missing_signatures']}")
        logging.info(f"False positives: {validation_result['false_positives']}")
        logging.info(f"Explanation: {validation_result['explanation']}")
        
        # The test passes if LLM assessment is PASS and no critical issues
        assert validation_result['assessment'].upper() == 'PASS', \
            f"LLM assessment failed: {validation_result['explanation']}"
        
        # Warn about missing signatures but don't fail the test
        if validation_result['missing_signatures']:
            logging.warning(f"Missing signatures detected: {validation_result['missing_signatures']}")
    
    def test_signature_extraction_on_tldr_creator(self):
        """Test signature extraction on TLDRFileCreator.py"""
        test_file = os.path.join(os.path.dirname(__file__), '..', 'tldr', 'TLDRFileCreator.py')
        
        # Extract signatures
        extracted_signatures = self.signature_extractor.get_signatures(test_file)
        
        # Validate with LLM
        validation_result = self.validate_signatures_with_llm(test_file, extracted_signatures)
        
        # Log the results
        logging.info(f"Signature validation results for {test_file}:")
        logging.info(f"Assessment: {validation_result['assessment']}")
        logging.info(f"Missing signatures: {validation_result['missing_signatures']}")
        logging.info(f"False positives: {validation_result['false_positives']}")
        logging.info(f"Explanation: {validation_result['explanation']}")
        
        # The test passes if LLM assessment is PASS
        assert validation_result['assessment'].upper() == 'PASS', \
            f"LLM assessment failed: {validation_result['explanation']}"
        
        # Warn about missing signatures but don't fail the test
        if validation_result['missing_signatures']:
            logging.warning(f"Missing signatures detected: {validation_result['missing_signatures']}")

    def test_signature_extraction_comprehensive_analysis(self):
        """Run comprehensive analysis on multiple files"""
        # test_files = [
        #     '/Users/csimoes/IdeaProjects/Amazon/AmazonScraper/adtrimmer-core/src/main/java/org/simoes/BodhiDogFixer.java'
        # ]
        test_files = [
            os.path.join(os.path.dirname(__file__), '..', 'tldr', 'signature_extractor.py'),
            os.path.join(os.path.dirname(__file__), '..', 'tldr', 'TLDRFileCreator.py'),
        ]
        
        # Add LLM provider files if they exist
        llm_dir = os.path.join(os.path.dirname(__file__), '..', 'tldr', 'llm_providers')
        for filename in ['llm_factory.py', 'llm_config.py', 'claude_provider.py', 'openai_provider.py']:
            filepath = os.path.join(llm_dir, filename)
            if os.path.exists(filepath):
                test_files.append(filepath)
        
        results = []
        for test_file in test_files:
            if not os.path.exists(test_file):
                logging.warning(f"File not found: {test_file}")
                continue
                
            try:
                # Extract signatures
                extracted_signatures = self.signature_extractor.get_signatures(test_file)
                
                # Validate with LLM
                validation_result = self.validate_signatures_with_llm(test_file, extracted_signatures)
                validation_result['file_path'] = test_file
                results.append(validation_result)
                
                logging.info(f"File: {os.path.basename(test_file)} - Assessment: {validation_result['assessment']}")
                
            except Exception as e:
                logging.error(f"Error processing {test_file}: {e}")
                results.append({
                    'file_path': test_file,
                    'assessment': 'ERROR',
                    'explanation': str(e)
                })
        
        # Summary report
        passed = sum(1 for r in results if r['assessment'].upper() == 'PASS')
        total = len(results)
        
        logging.info(f"Comprehensive analysis summary: {passed}/{total} files passed LLM validation")
        
        # Print detailed results
        for result in results:
            print(f"\n{'='*60}")
            print(f"File: {os.path.basename(result['file_path'])}")
            print(f"Assessment: {result['assessment']}")
            if result.get('missing_signatures'):
                print(f"Missing signatures: {result['missing_signatures']}")
            if result.get('false_positives'):
                print(f"False positives: {result['false_positives']}")
            print(f"Explanation: {result.get('explanation', 'N/A')}")
        
        # The test passes if at least 80% of files pass validation
        pass_rate = passed / total if total > 0 else 0
        assert pass_rate >= 0.8, f"Only {passed}/{total} files passed validation (need ≥80%)"


if __name__ == '__main__':
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run a simple test if executed directly
    test_instance = TestSignatureValidation()
    test_instance.setup_method()
    
    print("Running signature extraction validation test...")
    test_instance.test_signature_extraction_comprehensive_analysis()
    print("Test completed!")
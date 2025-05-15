"""
Run the OpenAI service tests directly without using pytest
"""
import sys
import os
import unittest
from pathlib import Path

# Add the project root directory to Python path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

# Import the test class
from tests.test_openai_service import TestOpenAIService

if __name__ == "__main__":
    # Create a test suite with just our OpenAI service tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOpenAIService)
    
    # Run the tests
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == "__main__":
    # Create a test suite with just our OpenAI service tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOpenAIService)
    
    # Run the tests
    unittest.TextTestRunner(verbosity=2).run(suite)

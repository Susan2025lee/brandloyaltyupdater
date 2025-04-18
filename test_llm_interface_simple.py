#!/usr/bin/env python3
"""
Simple test script for LLMInterface.
This tests that the .env configuration is working correctly.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import LLMInterface from the core module
from src.core.llm_interface import LLMInterface

def main():
    """Test the LLMInterface with a simple prompt."""
    print(f"Starting LLMInterface test...")
    print(f"USE_LLM_PROXY environment variable: {os.getenv('USE_LLM_PROXY')}")
    
    try:
        # Initialize the interface with the gpt-o1-mini model
        # The model key will be loaded from the DEFAULT_LLM_MODEL_KEY environment variable
        llm = LLMInterface()
        print(f"LLMInterface initialized with model: {llm.model_name}")
        
        # Test a simple prompt
        prompt = "What is the capital of France? Keep it short."
        print(f"\nSending prompt: '{prompt}'")
        
        response = llm.generate_response(prompt=prompt)
        print(f"\nResponse from LLM:\n{response}")
        
        print("\nTest completed successfully!")
        return 0
    except Exception as e:
        print(f"\nError testing LLMInterface: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
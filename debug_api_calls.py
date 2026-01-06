"""
Debug script - Shows all API calls in real-time
Run this to see exactly what prompts are sent to Gemini
"""

import os
import json
import sys
from dotenv import load_dotenv

# Patch to intercept API calls
original_invoke = None

def debug_invoke(self, messages, **kwargs):
    """Intercept and log all API calls."""
    prompt = messages[0].content if messages else ""
    
    print("\n" + "="*80)
    print("🔴 API CALL INTERCEPTED")
    print("="*80)
    print(f"\nModel: {self.model}")
    print(f"Temperature: {self.temperature}")
    print(f"\nPrompt ({len(prompt)} characters):\n")
    print("N"*80)
    print(f"{prompt}")
    print("N"*80)
    
    
    print("⏳ Waiting for response from Gemini...\n")
    
    # Call original method
    response = original_invoke(self, messages, **kwargs)
    
    print("✅ API RESPONSE RECEIVED")
    print("="*80)
    print(f"\nResponse ({len(response.content)} characters):\n")
    print(response.content[:1000])
    if len(response.content) > 1000:
        print(f"\n... [truncated, total {len(response.content)} chars] ...\n")
    print("="*80 + "\n")
    
    return response


if __name__ == "__main__":
    load_dotenv()
    
    # Check if API key exists
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not set")
        sys.exit(1)
    
    # Import after loading env
    from langchain_google_genai import ChatGoogleGenerativeAI
    from main import Orchestrator
    
    # Patch the invoke method
    original_invoke = ChatGoogleGenerativeAI.invoke
    ChatGoogleGenerativeAI.invoke = debug_invoke
    
    # Run orchestrator
    print("\n🔍 DEBUG MODE - All API calls will be logged\n")
    
    orchestrator = Orchestrator(
        target_dir="./sandbox/dataset_inconnu",
        max_iterations=1
    )
    
    exit_code = orchestrator.run()
    sys.exit(exit_code)

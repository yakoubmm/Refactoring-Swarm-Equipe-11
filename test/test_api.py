"""
Simple API test - Check if Gemini API is working
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

load_dotenv()

print("\n" + "="*60)
print("🧪 SIMPLE API TEST")
print("="*60 + "\n")

# Check API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ ERROR: GOOGLE_API_KEY not found in .env")
    print("   Please add: GOOGLE_API_KEY=your_key_here")
    exit(1)

print("✅ API key found\n")

# Try to call the API
try:
    print("🔄 Connecting to Gemini API...")
    client = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.2,
        max_retries=0
    )
    
    # Simple test prompt
    test_prompt = "SAY MY NAME "
    
    print(f"📝 Sending prompt: '{test_prompt}'\n")
    
    message = HumanMessage(content=test_prompt)
    response = client.invoke([message])
    
    print("✅ SUCCESS! API is working!\n")
    print(f"Response: {response.content}\n")
    print("="*60)
    print("🎉 Your API connection is good!")
    print("="*60 + "\n")
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}\n")
    print("Possible causes:")
    print("  1. Internet connection issue")
    print("  2. Invalid API key")
    print("  3. Google API server down")
    print("  4. Quota exceeded\n")

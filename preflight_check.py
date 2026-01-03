#!/usr/bin/env python3
"""
Pre-flight checklist before running orchestrator
"""
import os
import sys
from pathlib import Path

print("\n" + "="*70)
print("  PRE-FLIGHT TEST CHECKLIST")
print("="*70 + "\n")

checks = {
    "✅ main.py exists": Path("main.py").exists(),
    "✅ Agents exist": Path("src/agents/auditor.py").exists(),
    "✅ Logger configured": Path("src/utils/logger.py").exists(),
    "✅ Test code ready": Path("sandbox/dataset_inconnu/calculator.py").exists(),
    "✅ Test suite ready": Path("sandbox/dataset_inconnu/test_calculator.py").exists(),
}

all_good = True
for check, result in checks.items():
    status = "✅" if result else "❌"
    print(f"{status} {check.replace('✅ ', '')}")
    if not result:
        all_good = False

# Check API key
print("\n📌 API Key Configuration:")
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY", "").strip()

if api_key and api_key != "your_actual_key_here":
    print(f"✅ GOOGLE_API_KEY is set (first 10 chars: {api_key[:10]}...)")
else:
    print("❌ GOOGLE_API_KEY not configured or invalid")
    print("   You need to:")
    print("   1. Go to: https://makersuite.google.com/app/apikey")
    print("   2. Copy your API key")
    print("   3. Update .env file with: GOOGLE_API_KEY=\"your_actual_key\"")
    all_good = False

print("\n" + "="*70)

if all_good:
    print("🚀 READY TO TEST!\n")
    print("Run this command:")
    print("   python main.py --target_dir \"./sandbox/dataset_inconnu\"\n")
    sys.exit(0)
else:
    print("⚠️  FIX ISSUES ABOVE BEFORE RUNNING\n")
    sys.exit(1)

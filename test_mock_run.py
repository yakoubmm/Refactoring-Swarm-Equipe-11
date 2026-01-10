"""
Mock test runner - Tests the system without using real API calls.
Simulates Auditor, Fixer, Generator, and Judge responses.
"""

import os
import json
from unittest.mock import patch, MagicMock
import sys

# Set dummy API key for test
os.environ["GOOGLE_API_KEY"] = "test-key-dummy"

from src.agents.auditor import Auditor
from src.agents.fixer import Fixer
from src.agents.generator import Generator
from src.agents.judge import Judge
from src.utils.logger import log_experiment, ActionType


def mock_auditor_response():
    """Simulate Auditor LLM response"""
    return json.dumps({
        "files": {
            "sandbox/dataset_inconnu/calculator.py": {
                "issues": [
                    {
                        "type": "bug",
                        "severity": "high",
                        "description": "Division by zero not handled",
                        "suggested_fix": "Add check for divisor != 0"
                    }
                ]
            }
        }
    })


def mock_fixer_response():
    """Simulate Fixer LLM response"""
    return """def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
"""


def mock_generator_response():
    """Simulate Generator LLM response"""
    return """import pytest
from calculator import divide

def test_divide_normal():
    assert divide(10, 2) == 5

def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)

def test_divide_floats():
    assert divide(5.5, 1.1) == pytest.approx(5.0)
"""


def mock_judge_response():
    """Simulate successful test run"""
    return "2 passed in 0.05s"


def test_mock_run():
    """Run full orchestration with mocked LLM calls"""
    
    print("\n" + "="*70)
    print("🧪 MOCK TEST - No API calls required")
    print("="*70 + "\n")
    
    target_dir = "./sandbox/dataset_inconnu"
    
    # Check if target exists
    if not os.path.isdir(target_dir):
        print(f"❌ Target directory not found: {target_dir}")
        return False
    
    try:
        # Create a mock client response
        mock_response = MagicMock()
        
        # ===== MOCK AUDITOR =====
        print("🔍 [AUDITOR] Analyzing code (mocked)...")
        mock_response.content = mock_auditor_response()
        with patch('src.agents.auditor.ChatGoogleGenerativeAI') as mock_llm:
            mock_instance = MagicMock()
            mock_instance.invoke.return_value = mock_response
            mock_llm.return_value = mock_instance
            
            auditor = Auditor()
            audit_result = auditor.analyze(target_dir)
        
        if audit_result.get("success"):
            print(f"✅ [AUDITOR] Analysis complete - {len(audit_result.get('plan', {}).get('files', {}))} files analyzed")
            refactoring_plan = audit_result.get("plan", {})
        else:
            print(f"❌ [AUDITOR] Failed: {audit_result.get('error')}")
            return False
        
        # ===== MOCK FIXER =====
        print("\n🔧 [FIXER] Applying fixes (mocked)...")
        mock_response.content = mock_fixer_response()
        with patch('src.agents.fixer.ChatGoogleGenerativeAI') as mock_llm:
            mock_instance = MagicMock()
            mock_instance.invoke.return_value = mock_response
            mock_llm.return_value = mock_instance
            
            with patch('src.agents.fixer.HumanMessage') as mock_message:
                mock_message.return_value = MagicMock()
                
                fixer = Fixer()
                fix_result = fixer.apply_fixes(target_dir, refactoring_plan)
        
        if fix_result.get("success"):
            print(f"✅ [FIXER] Applied fixes to {fix_result.get('files_modified', 0)} file(s)")
        else:
            print(f"⚠️  [FIXER] Note: Some fixes may not have applied in mock mode")
        
        # ===== MOCK GENERATOR =====
        print("\n📝 [GENERATOR] Generating tests (mocked)...")
        mock_response.content = mock_generator_response()
        with patch('src.agents.generator.ChatGoogleGenerativeAI') as mock_llm:
            mock_instance = MagicMock()
            mock_instance.invoke.return_value = mock_response
            mock_llm.return_value = mock_instance
            
            generator = Generator()
            current_code = {"calculator.py": "def divide(a, b):\n    return a / b"}
            gen_result = generator.execute(target_dir, current_code, refactoring_plan)
        
        if gen_result.get("success"):
            print(f"✅ [GENERATOR] Generated {gen_result.get('test_files_created', 0)} test file(s)")
        else:
            print(f"⚠️  [GENERATOR] {gen_result.get('error', 'Unknown error')}")
        
        # ===== MOCK JUDGE =====
        print("\n✔️  [JUDGE] Running tests (mocked)...")
        with patch('src.agents.judge.ChatGoogleGenerativeAI') as mock_llm:
            mock_instance = MagicMock()
            mock_llm.return_value = mock_instance
            
            judge = Judge()
            
            # Mock the pytest execution
            with patch.object(judge, '_run_pytest', return_value=(mock_judge_response(), True)):
                judge_result = judge.validate(target_dir)
        
        if judge_result.get("tests_passed"):
            print(f"✅ [JUDGE] ALL TESTS PASSED!")
            print("\n" + "="*70)
            print("🏆 MOCK TEST COMPLETE - System works correctly!")
            print("="*70 + "\n")
            
            # Log successful mock test
            log_experiment(
                agent_name="MockTest",
                model_used="mock-llm",
                action=ActionType.DEBUG,
                details={
                    "input_prompt": "Mock test orchestration",
                    "output_response": "Mock test passed successfully",
                    "test_type": "mock_run",
                    "target_dir": target_dir,
                    "auditor_ok": True,
                    "fixer_ok": fix_result.get("success"),
                    "generator_ok": gen_result.get("success"),
                    "judge_ok": True
                },
                status="SUCCESS"
            )
            
            return True
        else:
            print(f"❌ [JUDGE] Tests failed: {judge_result.get('test_output')}")
            return False
    
    except Exception as e:
        print(f"\n❌ Error during mock test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = test_mock_run()
    sys.exit(0 if success else 1)

"""
Test mode for the orchestrator without API calls.
Mocks all agent responses with realistic test data.
"""

import os
import sys
import json
from src.agents.base_agent import BaseAgent
from src.agents.auditor import Auditor
from src.agents.fixer import Fixer
from src.agents.generator import Generator
from src.agents.judge import Judge


class MockAuditor(Auditor):
    """Mock Auditor that returns canned responses without API calls."""
    
    def execute(self, target_dir: str, previous_errors: str = None):
        print("🔍 [MOCK AUDITOR] Returning mock analysis (no API)...")
        return {
            "success": True,
            "model": "mock-auditor",
            "plan": {
                "files": {
                    "calculator.py": {
                        "issues": [
                            {
                                "line": 5,
                                "issue": "Missing type hints",
                                "fix": "Add type hints to function parameters"
                            }
                        ]
                    }
                }
            },
            "files_analyzed": 1
        }


class MockFixer(Fixer):
    """Mock Fixer that skips actual code changes."""
    
    def execute(self, target_dir: str, refactoring_plan):
        print("🔧 [MOCK FIXER] Skipping fixes (no API)...")
        return {
            "success": True,
            "model": "mock-fixer",
            "files_modified": 1,
            "changes_made": [
                {
                    "file": "calculator.py",
                    "changes": "Added mock type hints"
                }
            ]
        }


class MockGenerator(Generator):
    """Mock Generator that skips test generation."""
    
    def execute(self, target_dir: str):
        print("📝 [MOCK GENERATOR] Skipping test generation (no API)...")
        return {
            "success": True,
            "tests_generated": 0
        }


class MockJudge(Judge):
    """Mock Judge that returns success."""
    
    def validate(self, target_dir: str):
        print("✔️  [MOCK JUDGE] Returning mock validation (no API)...")
        return {
            "tests_passed": True,
            "test_output": "All mock tests passed!",
            "model": "mock-judge"
        }


if __name__ == "__main__":
    from main import Orchestrator
    
    # Create orchestrator with mock agents
    orchestrator = Orchestrator(
        target_dir="./sandbox/dataset_inconnu",
        max_iterations=2
    )
    
    # Replace agents with mocks
    orchestrator.auditor = MockAuditor()
    orchestrator.fixer = MockFixer()
    orchestrator.generator = MockGenerator()
    orchestrator.judge = MockJudge()
    
    # Run without API
    exit_code = orchestrator.run()
    sys.exit(exit_code)

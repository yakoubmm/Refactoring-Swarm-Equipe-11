"""
Judge Agent - Validates fixes using automated tests
"""

import os
import subprocess
import json
from typing import Dict, Any
from src.agents.base_agent import BaseAgent

class Judge(BaseAgent):
    """
    Judge Agent: Executes automated tests to validate fixes.
    
    Responsibilities:
    - Execute pytest on the modified codebase
    - Validate whether fixes are successful
    - Collect and return error logs if tests fail
    - Report test results back to orchestrator
    """
    
    def __init__(self, model_name: str = "pytest"):
        super().__init__(model_name=model_name)
    
    def validate(self, target_dir: str) -> Dict[str, Any]:
        """
        Run tests to validate fixes.
        
        Args:
            target_dir (str): Path to directory containing code to test
            
        Returns:
            Dict with keys:
                - "tests_passed" (bool): All tests passed
                - "test_output" (str): pytest output
                - "failed_tests" (List): Details of failed tests
                - "test_count" (int): Total tests run
        """
        return self.execute(target_dir)
    
    def execute(self, target_dir: str) -> Dict[str, Any]:
        """
        Main execution - run pytest on target directory.
        
        Implementation note: This uses subprocess to run pytest.
        Pytest must be installed (included in requirements.txt).
        """
        if not os.path.isdir(target_dir):
            return {
                "tests_passed": False,
                "test_output": f"Target directory not found: {target_dir}",
                "failed_tests": [],
                "test_count": 0,
                "model": self.model_name
            }
        
        # Run pytest with json report for detailed output
        test_output, success = self._run_pytest(target_dir)
        
        # Parse results
        failed_tests = self._extract_failed_tests(test_output)
        test_count = self._count_tests(test_output)
        
        return {
            "tests_passed": success,
            "test_output": test_output,
            "failed_tests": failed_tests,
            "test_count": test_count,
            "model": self.model_name
        }
    
    def _run_pytest(self, target_dir: str) -> tuple: # this should be in src/tools too
        """
        Run pytest on target directory.
        
        Returns:
            (test_output: str, success: bool)
        """
        try:
            # Run pytest with verbose output
            result = subprocess.run(
                ["python", "-m", "pytest", target_dir, "-v", "--tb=short"],
                cwd=target_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Combine stdout and stderr for complete output
            test_output = result.stdout + result.stderr
            success = result.returncode == 0
            
            return test_output, success
        
        except subprocess.TimeoutExpired:
            return "Tests timed out after 60 seconds", False
        except FileNotFoundError:
            return "pytest not found. Install via: pip install pytest", False
        except Exception as e:
            return f"Error running pytest: {str(e)}", False
    
    def _extract_failed_tests(self, test_output: str) -> list:
        """
        Extract information about failed tests from pytest output.
        
        Args:
            test_output (str): Raw output from pytest
            
        Returns:
            List of failed test info dicts
        """
        failed_tests = []
        
        # Parse pytest output for FAILED markers
        lines = test_output.split('\n')
        for line in lines:
            if "FAILED" in line or "ERROR" in line:
                failed_tests.append({
                    "test": line.strip(),
                    "status": "failed"
                })
        
        return failed_tests
    
    def _count_tests(self, test_output: str) -> int:
        """
        Count total number of tests from pytest output.
        
        Args:
            test_output (str): Raw output from pytest
            
        Returns:
            int: Number of tests found
        """
        # Look for test summary line
        for line in test_output.split('\n'):
            if "passed" in line or "failed" in line:
                # Try to extract count
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "passed" in part or "failed" in part:
                            # Look for number before 'passed' or 'failed'
                            if i > 0 and parts[i-1].isdigit():
                                return int(parts[i-1])
                except:
                    pass
        
        return 0

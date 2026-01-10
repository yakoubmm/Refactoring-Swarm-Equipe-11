"""
Judge Agent - Validates fixes using automated tests
"""

import os
import subprocess
import json
import time
from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.logger import ActionType, log_experiment

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
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    google_api_key=api_key,
                    temperature=0.2
                )
            else:
                self.llm = None
        except:
            self.llm = None
    
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
        Main execution - run pytest on target directory and diagnose failures.
        
        Implementation note: This uses subprocess to run pytest.
        Pytest must be installed (included in requirements.txt).
        """
        if not os.path.isdir(target_dir):
            return {
                "tests_passed": False,
                "test_output": f"Target directory not found: {target_dir}",
                "failed_tests": [],
                "test_count": 0,
                "diagnosis": None,
                "feedback": None,
                "model": self.model_name
            }
        
        # Run pytest with json report for detailed output
        test_output, success = self._run_pytest(target_dir)
        
        # Parse results
        failed_tests = self._extract_failed_tests(test_output)
        test_count = self._count_tests(test_output)
        
        # Diagnose failures if tests failed and LLM available
        diagnosis = None
        feedback = None
        if not success and self.llm:
            diagnosis, feedback = self._diagnose_failures(test_output, target_dir)
        
        return {
            "tests_passed": success,
            "test_output": test_output,
            "failed_tests": failed_tests,
            "test_count": test_count,
            "diagnosis": diagnosis,
            "feedback": feedback,
            "model": self.model_name
        }
    
    def _diagnose_failures(self, test_output: str, target_dir: str) -> tuple:
        """
        Use LLM to diagnose why tests are failing and provide feedback.
        
        Args:
            test_output (str): Output from pytest
            target_dir (str): Path to target directory
            
        Returns:
            (diagnosis: str, feedback: str) - LLM diagnosis and actionable feedback
        """
        if not self.llm:
            return None, None
        
        try:
            # Build diagnosis prompt
            prompt = f"""You are a code debugging expert. Analyze the following test failures and provide:
1. Root cause analysis of why tests are failing
2. Specific actionable feedback for the fixer agent to resolve these issues

Test Output:
{test_output[:2000]}

Target Directory: {target_dir}

Provide your diagnosis in this format:
DIAGNOSIS: [Root cause analysis]
FEEDBACK: [Specific actions for the fixer agent]"""
            
            # Call LLM with retry logic
            diagnosis_text = self._call_llm_with_retry(prompt)
            
            # Log the diagnosis using proper log_experiment
            log_experiment(
                agent_name="Judge",
                model_used="gemini-2.0-flash",
                action=ActionType.DEBUG,
                details={
                    "input_prompt": prompt,
                    "output_response": diagnosis_text,
                    "target_dir": target_dir
                },
                status="SUCCESS"
            )
            
            # Parse diagnosis and feedback
            diagnosis = None
            feedback = None
            for line in diagnosis_text.split('\n'):
                if line.startswith("DIAGNOSIS:"):
                    diagnosis = line.replace("DIAGNOSIS:", "").strip()
                elif line.startswith("FEEDBACK:"):
                    feedback = line.replace("FEEDBACK:", "").strip()
            
            return diagnosis or diagnosis_text[:200], feedback or diagnosis_text[200:400]
        
        except Exception as e:
            # Log failed diagnosis
            log_experiment(
                agent_name="Judge",
                model_used="gemini-2.0-flash",
                action=ActionType.DEBUG,
                details={
                    "input_prompt": prompt,
                    "output_response": str(e),
                    "target_dir": target_dir,
                    "error": str(e)
                },
                status="FAILURE"
            )
            return f"Diagnosis error: {str(e)}", None
    
    def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call LLM with exponential backoff retry logic.
        
        Args:
            prompt (str): The prompt to send to LLM
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            str: LLM response
        """
        wait_time = 1
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(prompt)
                return response.content if hasattr(response, 'content') else str(response)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    wait_time *= 2
        
        raise last_error or Exception("Failed to call LLM after retries")
    
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

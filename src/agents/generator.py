"""
Generator Agent - Creates pytest test files for code
"""

import os
import json
import time
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from src.agents.base_agent import BaseAgent
from src.utils.logger import log_experiment, ActionType


class Generator(BaseAgent):
    """
    Generator Agent: Creates pytest test files for analyzed code.
    
    Responsibilities:
    - Check if tests exist in sandbox/tests/
    - Generate comprehensive pytest files if missing
    - Write test files to sandbox
    - Log generation with ActionType.GENERATION
    """
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        super().__init__(model_name=model_name)
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        self.client = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0.2)
    
    def generate_tests(self, target_dir: str, current_code: Dict[str, str], audit_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate pytest test files if they don't exist.
        
        Args:
            target_dir (str): Target directory with code to test
            current_code (Dict): {filepath: code} of all files
            audit_plan (Dict): Audit plan with identified issues
            
        Returns:
            Dict with:
                - "success" (bool)
                - "test_files_created" (int)
                - "test_files" (list): paths of created test files
        """
        return self.execute(target_dir, current_code, audit_plan)
    
    def execute(self, target_dir: str, current_code: Dict[str, str], audit_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution - generate test files.
        """
        # Step 1: Check if tests already exist
        test_dir = os.path.join(target_dir, "tests")
        test_files_exist = self._check_tests_exist(test_dir)
        
        if test_files_exist:
            print(f"✅ Tests already exist in {test_dir}")
            return self.format_output({
                "success": True,
                "test_files_created": 0,
                "test_files": [],
                "message": "Tests already exist, skipping generation"
            })
        
        print(f"📝 Generating test files for {len(current_code)} file(s)...")
        
        # Step 2: Create tests/ directory
        os.makedirs(test_dir, exist_ok=True)
        
        # Step 3: For each main Python file, generate tests
        test_files_created = []
        generation_errors = []
        
        for filepath, code in current_code.items():
            # Skip test files themselves
            if "test_" in filepath:
                continue
            
            try:
                # Generate test file for this source file
                test_code = self._generate_test_for_file(filepath, code, audit_plan)
                
                # Determine test filename
                base_name = os.path.basename(filepath)
                test_filename = f"test_{base_name}"
                test_filepath = os.path.join(test_dir, test_filename)
                
                # Write test file
                with open(test_filepath, 'w', encoding='utf-8') as f:
                    f.write(test_code)
                
                test_files_created.append(test_filepath)
                print(f"✅ Created: {test_filepath}")
                
                # LOG THIS GENERATION
                log_experiment(
                    agent_name="Generator",
                    model_used=self.model_name,
                    action=ActionType.GENERATION,
                    details={
                        "input_prompt": self._build_test_prompt(filepath, code, audit_plan),
                        "output_response": test_code,
                        "source_file": filepath,
                        "test_file": test_filepath
                    },
                    status="SUCCESS"
                )
            
            except Exception as e:
                error_msg = f"Failed to generate tests for {filepath}: {str(e)}"
                print(f"❌ {error_msg}")
                generation_errors.append(error_msg)
                
                log_experiment(
                    agent_name="Generator",
                    model_used=self.model_name,
                    action=ActionType.GENERATION,
                    details={
                        "input_prompt": self._build_test_prompt(filepath, code, audit_plan),
                        "output_response": error_msg,
                        "source_file": filepath,
                        "error": str(e)
                    },
                    status="FAILURE"
                )
        
        return self.format_output({
            "success": len(generation_errors) == 0,
            "test_files_created": len(test_files_created),
            "test_files": test_files_created,
            "errors": generation_errors if generation_errors else None
        })
    
    def _check_tests_exist(self, test_dir: str) -> bool:
        """Check if test files already exist."""
        if not os.path.exists(test_dir):
            return False
        
        test_files = [f for f in os.listdir(test_dir) if f.startswith("test_") and f.endswith(".py")]
        return len(test_files) > 0
    
    def _generate_test_for_file(self, filepath: str, code: str, audit_plan: Dict[str, Any]) -> str:
        """Generate pytest code for a source file."""
        prompt = self._build_test_prompt(filepath, code, audit_plan)
        
        try:
            return self._call_llm_with_retry(prompt)
        except Exception as e:
            raise Exception(f"LLM test generation failed: {str(e)}")
    
    def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Call LLM with retry logic."""
        wait_time = 1
        
        for attempt in range(max_retries):
            try:
                message = HumanMessage(content=prompt)
                response = self.client.invoke([message])
                test_code = response.content
                
                # Extract code from markdown if present
                test_code = self._extract_code(test_code)
                
                return test_code
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                
                print(f"⚠️  Attempt {attempt + 1} failed: {str(e)}")
                time.sleep(wait_time)
                wait_time *= 2
    
    def _build_test_prompt(self, filepath: str, code: str, audit_plan: Dict[str, Any]) -> str:
        """Build prompt for test generation."""
        # Extract issues for this file from audit plan
        file_issues = audit_plan.get("files", {}).get(filepath, {}).get("issues", [])
        
        issues_text = ""
        if file_issues:
            issues_text = "\n\nKNOWN ISSUES IN THIS FILE:\n"
            for issue in file_issues[:5]:
                issues_text += f"- {issue.get('severity').upper()}: {issue.get('description')}\n"
        
        prompt = f"""You are an expert Python test engineer. Create comprehensive pytest tests for this code:

FILE: {filepath}
{issues_text}

SOURCE CODE:
```python
{code}
```

REQUIREMENTS FOR TEST FILE:
1. Create pytest test cases that:
   - Test all functions and classes
   - Cover edge cases and error conditions
   - Validate the issues mentioned above are fixed
   - Use clear, descriptive test names
   
2. Format:
   - Import the module being tested
   - Create test_* functions for each public function/method
   - Use assert statements for validation
   - Include docstrings for each test
   
3. Output ONLY valid Python code in ```python ... ``` blocks
4. Do NOT include explanations outside code blocks
5. Start with: import pytest
6. Ensure tests are independent and can run in any order

GENERATE THE COMPLETE TEST FILE:"""
        
        return prompt
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code from markdown blocks."""
        import re
        
        pattern = r'```python\n(.*?)\n```'
        match = re.search(pattern, response, re.DOTALL)
        
        if match:
            return match.group(1)
        
        pattern = r'```\n(.*?)\n```'
        match = re.search(pattern, response, re.DOTALL)
        
        if match:
            return match.group(1)
        
        return response

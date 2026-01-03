"""
Fixer Agent - Applies corrections to code based on audit plan
"""

import os
import json
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from src.agents.base_agent import BaseAgent
from src.utils.logger import log_experiment, ActionType

class Fixer(BaseAgent):
    """
    Fixer Agent: Applies corrections to Python code based on audit plan.
    
    Responsibilities:
    - Receive refactoring plan from Auditor
    - Modify Python files safely in target directory
    - Improve code correctness and quality
    - Handle file I/O and backups
    
    Logging: All LLM interactions are logged with ActionType.FIX
    """
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        super().__init__(model_name=model_name)
        # Initialize Gemini API via LangChain
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        self.client = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0.2)
    
    def apply_fixes(self, target_dir: str, refactoring_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply fixes based on refactoring plan.
        
        Args:
            target_dir (str): Path to directory containing Python files
            refactoring_plan (Dict): Plan from Auditor with issues and fixes
            
        Returns:
            Dict with keys:
                - "success" (bool): Fixes applied successfully
                - "model" (str): LLM model used
                - "files_modified" (int): Number of files changed
                - "changes_made" (List): Details of each change
        """
        return self.execute(target_dir, refactoring_plan)
    
    def execute(self, target_dir: str, refactoring_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution - apply fixes to files based on refactoring plan.
        
        Steps:
        1. Parse the refactoring plan
        2. For each file with issues, read the original code
        3. Call Gemini LLM to generate corrected code
        4. Apply fixes to files (with backup)
        5. Log interaction with ActionType.FIX
        6. Return summary of changes
        """
        if not os.path.isdir(target_dir):
            return self.format_output({
                "success": False,
                "error": f"Target directory not found: {target_dir}",
                "files_modified": 0
            })
        
        if not refactoring_plan or not refactoring_plan.get("files"):
            return self.format_output({
                "success": True,
                "files_modified": 0,
                "changes_made": []
            })
        
        changes_made = []
        files_to_fix = refactoring_plan.get("files", {})
        
        for file_path, file_plan in files_to_fix.items():
            issues = file_plan.get("issues", [])
            
            # Skip if no issues for this file
            if not issues:
                continue
            
            try:
                # Read original file
                original_code = self._read_file(file_path) # here too 
                
                # Build fix prompt for Gemini
                fix_prompt = self._build_fix_prompt(file_path, original_code, issues)
                
                # Call Gemini LLM to generate fixed code
                message = HumanMessage(content=fix_prompt)
                gemini_response = self.client.invoke([message])
                fixed_code = gemini_response.content
                
                # Extract code from response (remove markdown if present)
                fixed_code = self._extract_code(fixed_code)
                
                # Write fixed code to file (with backup)
                self._write_file(file_path, fixed_code) # again
                
                # LOG THE INTERACTION (Mandatory for scientific study)
                log_experiment(
                    agent_name="Fixer",
                    model_used=self.model_name,
                    action=ActionType.FIX,
                    details={
                        "input_prompt": fix_prompt,
                        "output_response": fixed_code,
                        "file": file_path,
                        "issues_fixed": len(issues)
                    },
                    status="SUCCESS"
                )
                
                changes_made.append({
                    "file": file_path,
                    "issues_fixed": len(issues),
                    "status": "modified"
                })
                
                print(f"✅ Fixed: {file_path} ({len(issues)} issues)")
            
            except Exception as e:
                error_msg = f"Error fixing {file_path}: {str(e)}"
                print(f"❌ {error_msg}")
                
                # Log failed fix attempt
                log_experiment(
                    agent_name="Fixer",
                    model_used=self.model_name,
                    action=ActionType.FIX,
                    details={
                        "input_prompt": fix_prompt if 'fix_prompt' in locals() else "",
                        "output_response": error_msg,
                        "file": file_path,
                        "error": str(e)
                    },
                    status="FAILURE"
                )
                
                changes_made.append({
                    "file": file_path,
                    "status": "failed",
                    "error": str(e)
                })
        
        return self.format_output({
            "success": True,
            "files_modified": len([c for c in changes_made if c.get("status") == "modified"]),
            "changes_made": changes_made
        })
    
    def _placeholder_fixes(self, refactoring_plan: Dict[str, Any]) -> list:
        """
        Placeholder fixes structure.
        
        Returns a template for the fixes applied.
        In production, this would be generated by LLM-based code generation.
        """
        changes = []
        
        for file_path, file_plan in refactoring_plan.items():
            if file_plan.get("issues"):
                changes.append({
                    "file": file_path,
                    "issues_fixed": len(file_plan["issues"]),
                    "status": "modified",
                    "new_quality_score": 0.85  # Placeholder
                })
        
        return changes
    
    def _build_fix_prompt(self, file_path: str, original_code: str, issues: list) -> str:
        """
        Build a structured prompt for Gemini to fix code.
        
        Args:
            file_path (str): Path to the file being fixed
            original_code (str): Original code content
            issues (list): List of issues to fix
            
        Returns:
            str: Formatted prompt for LLM
        """
        issues_text = ""
        for i, issue in enumerate(issues, 1):
            issues_text += f"\n{i}. [{issue.get('severity', 'unknown').upper()}] {issue.get('type', 'unknown')}"
            issues_text += f"\n   Problem: {issue.get('description', '')}"
            issues_text += f"\n   Suggested fix: {issue.get('suggested_fix', '')}\n"
        
        prompt = f"""You are an expert Python code refactorer. Fix the following Python code to address these issues:

FILE: {file_path}
ISSUES TO FIX:{issues_text}

ORIGINAL CODE:
```python
{original_code}
```

REQUIREMENTS:
1. Fix all identified issues
2. Maintain the original functionality
3. Improve code quality and readability
4. Add docstrings if missing
5. Follow PEP 8 standards
6. Return ONLY the fixed Python code, wrapped in ```python ... ``` blocks
7. Do NOT add any explanations or comments outside the code block

FIXED CODE:"""
        
        return prompt
    
    def _extract_code(self, response: str) -> str:
        """
        Extract Python code from Gemini response.
        
        Args:
            response (str): Raw response from Gemini
            
        Returns:
            str: Extracted Python code
        """
        # Look for ```python ... ``` blocks
        import re
        
        pattern = r'```python\n(.*?)\n```'
        match = re.search(pattern, response, re.DOTALL)
        
        if match:
            return match.group(1)
        
        # If no markdown found, try to extract plain code
        pattern = r'```\n(.*?)\n```'
        match = re.search(pattern, response, re.DOTALL)
        
        if match:
            return match.group(1)
        
        return response
    
    def _read_file(self, file_path: str) -> str: # same thing here 
        """Safely read a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Error reading {file_path}: {str(e)}")
    
    def _write_file(self, file_path: str, content: str) -> None: # and here 
        """Safely write modified content to a Python file with backup."""
        try:
            # Create backup
            backup_path = file_path + ".backup"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    with open(backup_path, 'w', encoding='utf-8') as bf:
                        bf.write(f.read())
            
            # Write new content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"Error writing {file_path}: {str(e)}")

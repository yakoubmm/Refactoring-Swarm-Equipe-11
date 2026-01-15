"""
Fixer Agent - Applies corrections to code based on audit plan
"""

import os
import json
import time
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from src.agents.base_agent import BaseAgent
from src.utils.logger import log_experiment, ActionType
from src.utils.quota import log_api_call

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
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        super().__init__(model_name=model_name)
        # Initialize Gemini API via LangChain
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        self.client = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0.2, max_retries=0)
    
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
        3. Chunk large files if needed
        4. Call Gemini LLM to generate corrected code with retry logic
        5. Apply fixes to files (with backup)
        6. Log interaction with ActionType.FIX
        7. Return summary of changes
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
                original_code = self._read_file(file_path)
                
                # Chunk if large
                chunks = self._chunk_code(original_code, max_tokens=8000)
                
                if len(chunks) > 1:
                    # Process chunks sequentially
                    fixed_code_parts = []
                    for i, chunk in enumerate(chunks):
                        print(f"  Processing chunk {i+1}/{len(chunks)}...")
                        
                        fix_prompt = self._build_fix_prompt(
                            file_path,
                            chunk,
                            issues,
                            is_chunk=True,
                            chunk_number=i+1,
                            total_chunks=len(chunks)
                        )
                        
                        fixed_chunk = self._get_fixed_code(fix_prompt)
                        fixed_code_parts.append(fixed_chunk)
                    
                    # Recombine chunks
                    fixed_code = '\n'.join(fixed_code_parts)
                else:
                    # Single chunk - process normally
                    fix_prompt = self._build_fix_prompt(file_path, original_code, issues)
                    
                    # Log API call for quota monitoring
                    quota_status = log_api_call("Fixer")
                    if quota_status.get("is_low_quota"):
                        print(quota_status["warning_message"])
                    
                    fixed_code = self._get_fixed_code(fix_prompt)
                
                # Extract code from response (remove markdown if present)
                fixed_code = self._extract_code(fixed_code)
                
                # Write fixed code to file (with backup)
                self._write_file(file_path, fixed_code)
                
                # LOG THE INTERACTION (Mandatory for scientific study)
                log_experiment(
                    agent_name="Fixer",
                    model_used=self.model_name,
                    action=ActionType.FIX,
                    details={
                        "input_prompt": fix_prompt if 'fix_prompt' in locals() else "",
                        "output_response": fixed_code,
                        "file": file_path,
                        "issues_fixed": len(issues),
                        "chunks_processed": len(chunks) if 'chunks' in locals() else 1
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
    
    def _chunk_code(self, code: str, max_tokens: int = 8000) -> list:
        """Split code into chunks to avoid token overflow."""
        lines = code.split('\n')
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for line in lines:
            line_tokens = len(line.split())
            
            if current_tokens + line_tokens > max_tokens and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_tokens = line_tokens
            else:
                current_chunk.append(line)
                current_tokens += line_tokens
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks if chunks else [code]
    
    def _get_fixed_code(self, prompt: str) -> str:
        """Call LLM with retry logic."""
        wait_time = 1
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                message = HumanMessage(content=prompt)
                response = self.client.invoke([message])
                return response.content
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"⚠️  Attempt {attempt + 1} failed: {str(e)}")
                time.sleep(wait_time)
                wait_time *= 2
    
    def _build_fix_prompt(self, file_path: str, original_code: str, issues: list, is_chunk: bool = False, chunk_number: int = None, total_chunks: int = None) -> str:
        """
        Build a structured prompt for Gemini to fix code.
        
        Args:
            file_path (str): Path to the file being fixed
            original_code (str): Original code content
            issues (list): List of issues to fix
            is_chunk (bool): Whether this is a chunk of a larger file
            chunk_number (int): Which chunk this is
            total_chunks (int): Total number of chunks
            
        Returns:
            str: Formatted prompt for LLM
        """
        issues_text = ""
        for i, issue in enumerate(issues, 1):
            issues_text += f"\n{i}. [{issue.get('severity', 'unknown').upper()}] {issue.get('type', 'unknown')}"
            issues_text += f"\n   Problem: {issue.get('description', '')}"
            issues_text += f"\n   Suggested fix: {issue.get('suggested_fix', '')}\n"
        
        chunk_info = ""
        if is_chunk:
            chunk_info = f"\n[PROCESSING CHUNK {chunk_number}/{total_chunks}]\nMaintain compatibility with the rest of the file.\n"
        
        prompt = f"""You are an expert Python code refactorer. Fix the following Python code to address these issues:

FILE: {file_path}{chunk_info}
ISSUES TO FIX:{issues_text}

GOAL:
Fix ONLY the issues listed below in the given file.

CONSTRAINTS (MANDATORY):
- Modify ONLY the provided file
- Do NOT invent new files, functions, or dependencies
- Preserve original behavior unless fixing a bug
- Do NOT use markdown
- Return the FULL corrected Python file only
- If unsure, return the original code unchanged

FILE:
{file_path}

ISSUES:
{issues_text}

ORIGINAL CODE:
{original_code}
"""
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
    
    def _read_file(self, file_path: str) -> str: 
        """Safely read a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Error reading {file_path}: {str(e)}")
    
    def _write_file(self, file_path: str, content: str) -> None:
        """Safely write modified content to a Python file with backup."""
        # Validate path is in sandbox
        from pathlib import Path
        try:
            resolved = Path(file_path).resolve()
            sandbox = Path("sandbox").resolve()
            if not str(resolved).startswith(str(sandbox)):
                raise PermissionError(f"Cannot write outside sandbox: {file_path}")
        except:
            pass  # If validation fails, still attempt write
        
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

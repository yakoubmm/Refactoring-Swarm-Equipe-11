"""
Auditor Agent - Analyzes code and produces refactoring plan
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

class Auditor(BaseAgent):
    """
    Auditor Agent: Analyzes Python code and produces a structured refactoring plan.
    
    Responsibilities:
    - Read and understand the codebase
    - Run pylint static analysis
    - Detect bugs, bad practices, and quality issues
    - Produce a structured refactoring plan
    - Return actionable feedback for the Fixer
    
    Logging: All LLM interactions are logged with ActionType.ANALYSIS
    """
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        super().__init__(model_name=model_name)
        # Initialize Gemini API via LangChain
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        self.client = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0.2, max_retries=0)
    
    def analyze(self, target_dir: str, previous_errors: str = None) -> Dict[str, Any]:
        """
        Analyze Python code in target directory and produce refactoring plan.
        
        Args:
            target_dir (str): Path to directory containing Python files
            previous_errors (str): Error context from previous iteration for iterative improvement
            
        Returns:
            Dict with keys:
                - "success" (bool): Analysis completed
                - "model" (str): LLM model used
                - "plan" (Dict): Refactoring plan with issues and fixes
                - "files_analyzed" (int): Number of files analyzed
        """
        return self.execute(target_dir, previous_errors=previous_errors)
    
    def execute(self, target_dir: str, previous_errors: str = None) -> Dict[str, Any]:
        """
        Main execution - analyze target directory using Gemini LLM.
        
        Steps:
        1. Scan all Python files in target_dir
        2. Run pylint static analysis
        3. Read file contents
        4. Chunk large files if needed
        5. Call Gemini LLM with code + pylint report
        6. Build a structured refactoring plan
        7. Log interaction with ActionType.ANALYSIS
        8. Return plan with specific file/line/fix mappings
        """
        if not os.path.isdir(target_dir):
            return self.format_output({
                "success": False,
                "error": f"Target directory not found: {target_dir}"
            })
        
        # Step 1: Scan Python files
        python_files = self._find_python_files(target_dir)
        
        if not python_files:
            return self.format_output({
                "success": True,
                "plan": {},
                "files_analyzed": 0
            })
        
        # Step 2: Run pylint analysis
        from src.tools.analysis import run_pylint_analysis, format_analysis_for_llm
        
        print(f"🔍 Running pylint analysis on {len(python_files)} file(s)...")
        pylint_analysis = run_pylint_analysis(target_dir)
        pylint_report = format_analysis_for_llm(pylint_analysis)
        
        # Step 3: Read file contents
        file_contents = self._read_files(python_files)
        
        # Step 4: Chunk large files if needed
        chunked_contents = self._chunk_files_if_large(file_contents)
        
        # Step 5: Create analysis prompt
        analysis_prompt = self._build_analysis_prompt(chunked_contents, pylint_report, previous_errors)
        
        # Step 6: Call LLM with retry logic
        try:
            # Log API call for quota monitoring
            quota_status = log_api_call("Auditor")
            if quota_status.get("is_low_quota"):
                print(quota_status["warning_message"])
            
            llm_output = self._call_llm_with_retry(analysis_prompt)
            
            # Step 7: Parse response into structured plan
            plan = self._parse_analysis_response(llm_output, python_files)
            
            # Step 8: LOG THE INTERACTION (Mandatory for scientific study)
            log_experiment(
                agent_name="Auditor",
                model_used=self.model_name,
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": analysis_prompt,
                    "output_response": llm_output,
                    "files_analyzed": len(python_files),
                    "issues_found": self._count_issues(plan),
                    "pylint_score": pylint_analysis.get("overall_score")
                },
                status="SUCCESS"
            )
            
            return self.format_output({
                "success": True,
                "plan": plan,
                "files_analyzed": len(python_files),
                "pylint_analysis": pylint_analysis
            })
        
        except Exception as e:
            error_msg = f"Gemini API error: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Log failed interaction
            log_experiment(
                agent_name="Auditor",
                model_used=self.model_name,
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": analysis_prompt,
                    "output_response": error_msg,
                    "files_analyzed": len(python_files),
                    "error": str(e)
                },
                status="FAILURE"
            )
            
            return self.format_output({
                "success": False,
                "error": error_msg
            })
    
    def _find_python_files(self, target_dir: str) -> list:
        """Find all Python files in target directory."""
        python_files = []
        for root, dirs, files in os.walk(target_dir):
            # Skip __pycache__ and .git directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', '.venv']]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    python_files.append(os.path.join(root, file))
        return python_files
    
    def _read_files(self, python_files: list) -> Dict[str, str]:
        """
        Read contents of all Python files.
        
        Args:
            python_files (list): List of file paths
            
        Returns:
            Dict mapping file paths to their contents
        """
        file_contents = {}
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_contents[file_path] = f.read()
            except Exception as e:
                file_contents[file_path] = f"[Error reading file: {str(e)}]"
        return file_contents
    
    def _chunk_files_if_large(self, file_contents: Dict[str, str], max_tokens: int = 8000) -> Dict[str, str]:
        """
        Chunk large files to prevent token overflow.
        
        Args:
            file_contents (Dict): {filepath: code}
            max_tokens (int): Max tokens per chunk
            
        Returns:
            Dict: Possibly chunked contents
        """
        chunked = {}
        
        for filepath, code in file_contents.items():
            # Estimate tokens (rough: ~4 chars per token)
            estimated_tokens = len(code) // 4
            
            if estimated_tokens > max_tokens:
                # Split into chunks
                lines = code.split('\n')
                chunks = []
                current_chunk = []
                current_tokens = 0
                
                for line in lines:
                    line_tokens = len(line) // 4
                    
                    if current_tokens + line_tokens > max_tokens and current_chunk:
                        chunks.append('\n'.join(current_chunk))
                        current_chunk = [line]
                        current_tokens = line_tokens
                    else:
                        current_chunk.append(line)
                        current_tokens += line_tokens
                
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                
                # Store first chunk as primary (Auditor reads first chunk)
                chunked[filepath] = chunks[0] + f"\n\n# ... [{len(chunks)} chunks total, showing chunk 1] ..."
            else:
                chunked[filepath] = code
        
        return chunked
    
    def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call LLM with exponential backoff retry logic.
        
        Args:
            prompt (str): Prompt to send to LLM
            max_retries (int): Maximum number of attempts
            
        Returns:
            str: LLM response
            
        Raises:
            Exception: If all retries fail
        """
        wait_time = 1
        
        for attempt in range(max_retries):
            try:
                message = HumanMessage(content=prompt)
                response = self.client.invoke([message])
                return response.content
            
            except Exception as e:
                if attempt == max_retries - 1:
                    raise  # Last attempt failed, propagate error
                
                print(f"⚠️  Attempt {attempt + 1} failed: {str(e)}")
                print(f"⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                wait_time *= 2  # Exponential backoff
    
    def _build_analysis_prompt(self, file_contents: Dict[str, str], pylint_report: str, previous_errors: str = None) -> str:
        """
        Build a structured prompt for Gemini to analyze Python code.
        
        Args:
            file_contents (Dict): Dictionary of file paths and contents
            pylint_report (str): Formatted pylint analysis report
            previous_errors (str): Errors from previous iteration (if any)
            
        Returns:
            str: Formatted prompt for LLM
        """
        files_text = ""
        for file_path, content in file_contents.items():
            files_text += f"\n{'='*60}\nFILE: {file_path}\n{'='*60}\n{content}\n"
        
        previous_context = ""
        if previous_errors:
            previous_context = f"\n\nPREVIOUS ITERATION ERRORS (address these specifically):\n{previous_errors[:1000]}"
        
        prompt = f"""You are a code quality expert. Analyze the following Python code and provide a detailed refactoring plan.

STATIC ANALYSIS REPORT (from pylint):
{pylint_report}

CODE TO ANALYZE:
{files_text}{previous_context}

ANALYSIS REQUIREMENTS:
1. Review the pylint issues above
2. Identify additional bugs, bad practices, and quality issues NOT caught by pylint
3. Focus on issues that will cause test failures
4. For each issue, provide:
   - Type of issue (bug, style, performance, security, documentation)
   - Severity (critical, high, medium, low)
   - Location (file, line number if possible)
   - Description of the problem
   - Suggested fix

5. Output MUST be valid JSON format with this structure:
{{
  "files": {{
    "file.py": {{
      "issues": [
        {{
          "type": "bug|style|design|performance|security|documentation",
          "severity": "critical|high|medium|low",
          "description": "short factual explanation",
          "suggested_fix": "high-level idea"
        }}
      ]
    }}
  }}
}}

RULES:
- Valid JSON only
- No markdown
- No explanations outside JSON
"""
        return prompt
    
    def _parse_analysis_response(self, llm_output: str, python_files: list) -> Dict[str, Any]:
        """
        Parse Gemini's response into a structured refactoring plan.
        
        Args:
            llm_output (str): Raw response from Gemini
            python_files (list): List of analyzed file paths
            
        Returns:
            Dict: Structured refactoring plan
        """
        try:
            # Try to extract JSON from response
            json_start = llm_output.find('{')
            json_end = llm_output.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = llm_output[json_start:json_end]
                plan = json.loads(json_str)
                return plan
            else:
                # If no valid JSON found, create basic plan
                return {
                    "analysis_summary": llm_output,
                    "files": {f: {"quality_score": 0.5, "issues": []} for f in python_files},
                    "total_issues": 0,
                    "priority_actions": []
                }
        except json.JSONDecodeError:
            # Return basic structure if JSON parsing fails
            return {
                "analysis_summary": "Analysis completed but parsing failed",
                "files": {f: {"quality_score": 0.5, "issues": []} for f in python_files},
                "total_issues": 0,
                "priority_actions": [],
                "raw_response": llm_output
            }
    
    def _count_issues(self, plan: Dict[str, Any]) -> int:
        """Count total issues in refactoring plan."""
        return plan.get("total_issues", 0)

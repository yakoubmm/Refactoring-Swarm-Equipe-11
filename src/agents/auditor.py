"""
Auditor Agent - Analyzes code and produces refactoring plan
"""

import os
import json
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from src.agents.base_agent import BaseAgent
from src.utils.logger import log_experiment, ActionType

class Auditor(BaseAgent):
    """
    Auditor Agent: Analyzes Python code and produces a structured refactoring plan.
    
    Responsibilities:
    - Read and understand the codebase
    - Detect bugs, bad practices, and quality issues
    - Produce a structured refactoring plan
    - Return actionable feedback for the Fixer
    
    Logging: All LLM interactions are logged with ActionType.ANALYSIS
    """
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        super().__init__(model_name=model_name)
        # Initialize Gemini API via LangChain
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        self.client = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0.2)
    
    def analyze(self, target_dir: str) -> Dict[str, Any]:
        """
        Analyze Python code in target directory and produce refactoring plan.
        
        Args:
            target_dir (str): Path to directory containing Python files
            
        Returns:
            Dict with keys:
                - "success" (bool): Analysis completed
                - "model" (str): LLM model used
                - "plan" (Dict): Refactoring plan with issues and fixes
                - "files_analyzed" (int): Number of files analyzed
        """
        return self.execute(target_dir)
    
    def execute(self, target_dir: str) -> Dict[str, Any]:
        """
        Main execution - analyze target directory using Gemini LLM.
        
        Steps:
        1. Scan all Python files in target_dir
        2. Read file contents
        3. Call Gemini LLM to analyze code quality
        4. Identify bugs, bad practices, type issues
        5. Build a structured refactoring plan
        6. Log interaction with ActionType.ANALYSIS
        7. Return plan with specific file/line/fix mappings
        """
        if not os.path.isdir(target_dir):
            return self.format_output({
                "success": False,
                "error": f"Target directory not found: {target_dir}"
            })
        
        # Scan Python files
        python_files = self._find_python_files(target_dir) # here too it should call the function from src/tools/filesystem.py
        
        if not python_files:
            return self.format_output({
                "success": True,
                "plan": {},
                "files_analyzed": 0
            })
        
        # Read file contents
        file_contents = self._read_files(python_files) # here too it should call the read function from src/tools/filesystem.py

        # there should be a here call to the analysis function that runs pylint from src/tools/analysis 
        # the returned analysis+score should go in the prompt sent to gemini
        
        # Create analysis prompt for Gemini
        analysis_prompt = self._build_analysis_prompt(file_contents)
        # Call Gemini LLM for code analysis
        try:
            message = HumanMessage(content=analysis_prompt)
            gemini_response = self.client.invoke([message])
            llm_output = gemini_response.content
            
            # Parse LLM response into structured plan
            plan = self._parse_analysis_response(llm_output, python_files)
            
            # LOG THE INTERACTION (Mandatory for scientific study)
            log_experiment(
                agent_name="Auditor",
                model_used=self.model_name,
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": analysis_prompt,
                    "output_response": llm_output,
                    "files_analyzed": len(python_files),
                    "issues_found": self._count_issues(plan)
                },
                status="SUCCESS"
            )
            
            return self.format_output({
                "success": True,
                "plan": plan,
                "files_analyzed": len(python_files)
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
    
    def _find_python_files(self, target_dir: str) -> list: # same thing here  
        """Find all Python files in target directory."""
        python_files = []
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files
    
    def _read_files(self, python_files: list) -> Dict[str, str]: # and here 
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
    
    def _build_analysis_prompt(self, file_contents: Dict[str, str]) -> str:
        files_text = ""
        for file_path, content in file_contents.items():
            files_text += f"\nFILE: {file_path}\n{content}\n"

        return f"""
ROLE:
You are a senior Python code auditor.

GOAL:
Identify ONLY real and verifiable issues present in the code.

CONSTRAINTS (MANDATORY):
- Do NOT invent files, functions, variables, or dependencies
- Do NOT modify the code
- Do NOT repeat the code in your output
- Report ONLY issues that are visible in the code
- If no issues are found, return an empty JSON structure

CODE:
{files_text}

OUTPUT FORMAT (JSON ONLY):
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
    
    def _placeholder_analysis(self, python_files: list) -> Dict[str, Any]:
        """
        Placeholder analysis structure (legacy).
        
        Returns a template for the refactoring plan.
        """
        plan = {}
        
        for file_path in python_files:
            plan[file_path] = {
                "issues": [],
                "quality_score": 0.0  # 0.0 to 1.0
            }
        
        return plan

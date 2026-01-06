# Implementation Guide - Completing the Refactoring Swarm

This guide provides step-by-step code samples to implement all missing components.

---

## IMPLEMENTATION 1: Pylint Integration in analysis.py

### File: `src/tools/analysis.py`

```python
"""
Static Code Analysis Tools - Pylint Integration
"""

import subprocess
import json
from typing import Dict, Any
from pathlib import Path


def run_pylint_analysis(target_dir: str) -> Dict[str, Any]:
    """
    Execute pylint on all Python files in target directory.
    
    Args:
        target_dir (str): Path to directory containing Python files
        
    Returns:
        Dict with structure:
        {
            "success": bool,
            "overall_score": float (0-10),
            "files": {
                "file.py": {
                    "score": 8.5,
                    "issues_count": 3,
                    "messages": [
                        {
                            "type": "convention|refactor|warning|error|fatal",
                            "message": "...",
                            "line": 42,
                            "column": 10
                        }
                    ]
                }
            },
            "total_issues": int,
            "error": str (if failed)
        }
    """
    try:
        # Run pylint with JSON output
        result = subprocess.run(
            [
                "python", "-m", "pylint",
                target_dir,
                "--output-format=json",
                "--recursive=y"
            ],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Parse JSON output
        if result.stdout:
            pylint_output = json.loads(result.stdout)
        else:
            pylint_output = []
        
        # Aggregate results by file
        analysis = {
            "success": True,
            "files": {},
            "total_issues": 0,
            "messages": pylint_output
        }
        
        # Process each issue
        for message in pylint_output:
            filepath = message.get("path", "unknown")
            
            if filepath not in analysis["files"]:
                analysis["files"][filepath] = {
                    "issues_count": 0,
                    "issues": []
                }
            
            analysis["files"][filepath]["issues_count"] += 1
            analysis["files"][filepath]["issues"].append({
                "type": message.get("type"),
                "message": message.get("message"),
                "line": message.get("line"),
                "column": message.get("column")
            })
            
            analysis["total_issues"] += 1
        
        # Calculate overall score (approximate)
        # Pylint: 10.0 is perfect, 0.0 is worst
        analysis["overall_score"] = max(0, 10 - (analysis["total_issues"] * 0.1))
        
        return analysis
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Pylint analysis timed out (120s limit)"
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Pylint output parsing failed"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Pylint execution failed: {str(e)}"
        }


def format_analysis_for_llm(analysis: Dict[str, Any]) -> str:
    """
    Format pylint analysis into readable text for LLM prompt.
    
    Args:
        analysis (Dict): Output from run_pylint_analysis()
        
    Returns:
        str: Formatted analysis report
    """
    if not analysis.get("success"):
        return f"Analysis failed: {analysis.get('error')}"
    
    report = f"""
CODE QUALITY ANALYSIS REPORT
=============================

Overall Score: {analysis.get('overall_score', 'N/A')}/10.0
Total Issues Found: {analysis.get('total_issues', 0)}

ISSUES BY FILE:
"""
    
    for filepath, file_data in analysis.get("files", {}).items():
        report += f"\n{filepath}:"
        report += f"\n  Issues: {file_data.get('issues_count', 0)}"
        
        for issue in file_data.get("issues", [])[:5]:  # Show top 5 per file
            report += f"\n    - Line {issue.get('line')}: "
            report += f"[{issue.get('type')}] {issue.get('message')}"
    
    return report


def parse_pylint_issues(analysis: Dict[str, Any]) -> list:
    """
    Extract issues from pylint analysis into refactoring plan format.
    
    Args:
        analysis (Dict): Output from run_pylint_analysis()
        
    Returns:
        list: Issues formatted for refactoring plan
    """
    issues_list = []
    
    for message in analysis.get("messages", []):
        issue_type_map = {
            "convention": "code-style",
            "refactor": "refactoring",
            "warning": "warning",
            "error": "bug",
            "fatal": "critical"
        }
        
        severity_map = {
            "convention": "low",
            "refactor": "medium",
            "warning": "high",
            "error": "critical",
            "fatal": "critical"
        }
        
        issues_list.append({
            "type": issue_type_map.get(message.get("type"), "unknown"),
            "severity": severity_map.get(message.get("type"), "medium"),
            "description": message.get("message"),
            "line": message.get("line"),
            "path": message.get("path")
        })
    
    return issues_list
```

---

## IMPLEMENTATION 2: Update Auditor to Use Pylint

### File: `src/agents/auditor.py` (MODIFY)

Replace the analysis section with:

```python
def execute(self, target_dir: str) -> Dict[str, Any]:
    """
    Main execution - analyze target directory using Gemini LLM.
    
    Steps:
    1. Scan all Python files in target_dir
    2. Run pylint static analysis
    3. Read file contents
    4. Chunk large files if needed
    5. Call Gemini LLM with code + pylint report
    6. Identify bugs, bad practices, type issues
    7. Build structured refactoring plan
    8. Log interaction with ActionType.ANALYSIS
    9. Return plan with specific file/line/fix mappings
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
    
    # Step 2: RUN PYLINT ANALYSIS ✅ NEW
    from src.tools.analysis import run_pylint_analysis, format_analysis_for_llm
    
    pylint_analysis = run_pylint_analysis(target_dir)
    pylint_report = format_analysis_for_llm(pylint_analysis)
    
    # Step 3: Read file contents
    file_contents = self._read_files(python_files)
    
    # Step 4: Chunk large files if needed ✅ NEW
    chunked_contents = self._chunk_files_if_large(file_contents)
    
    # Step 5: Create analysis prompt
    analysis_prompt = self._build_analysis_prompt(chunked_contents, pylint_report)
    
    # Step 6: Call LLM with retry logic ✅ NEW
    try:
        llm_output = self._call_llm_with_retry(analysis_prompt)
        
        # Step 7: Parse response into structured plan
        plan = self._parse_analysis_response(llm_output, python_files)
        
        # Step 8: LOG THE INTERACTION
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


# Add these helper methods to Auditor class

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
    import time
    
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


def _build_analysis_prompt(self, file_contents: Dict[str, str], pylint_report: str) -> str:
    """
    Build prompt with pylint analysis included. ✅ UPDATED
    """
    files_text = ""
    for file_path, content in file_contents.items():
        files_text += f"\n{'='*60}\nFILE: {file_path}\n{'='*60}\n{content}\n"
    
    prompt = f"""You are a code quality expert. Analyze the following Python code and provide a detailed refactoring plan.

STATIC ANALYSIS REPORT (from pylint):
{pylint_report}

CODE TO ANALYZE:
{files_text}

ANALYSIS REQUIREMENTS:
1. Review the pylint issues above
2. Identify additional bugs, bad practices, and quality issues NOT caught by pylint
3. For each issue, provide:
   - Type of issue (bug, style, performance, security, documentation)
   - Severity (critical, high, medium, low)
   - Location (file, line number if possible)
   - Description of the problem
   - Suggested fix

4. Output MUST be valid JSON format with this structure:
{{
  "analysis_summary": "Brief overview of code quality",
  "files": {{
    "file_path": {{
      "quality_score": 0.0-1.0,
      "issues": [
        {{
          "type": "string",
          "severity": "critical|high|medium|low",
          "description": "string",
          "suggested_fix": "string"
        }}
      ]
    }}
  }},
  "total_issues": number,
  "priority_actions": ["list of highest priority fixes"]
}}

Provide the JSON response only, no additional text."""
    
    return prompt
```

---

## IMPLEMENTATION 3: Test Generation Phase

### New File: `src/agents/generator.py`

```python
"""
Generator Agent - Creates pytest test files for code
"""

import os
import json
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
            message = HumanMessage(content=prompt)
            response = self.client.invoke([message])
            test_code = response.content
            
            # Extract code from markdown if present
            test_code = self._extract_code(test_code)
            
            return test_code
        
        except Exception as e:
            raise Exception(f"LLM test generation failed: {str(e)}")
    
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
```

---

## IMPLEMENTATION 4: Update Orchestrator to Use Generator

### File: `src/agents/orchestrator.py` (MODIFY main.py)

Add to imports:
```python
from src.agents.generator import Generator
```

Add to `Orchestrator.__init__()`:
```python
self.generator = Generator()
```

Add between Fixer and Judge phases:
```python
# Step 2.5: TEST GENERATION (if needed)
print(f"\n📝 [GENERATOR] Checking/creating test files...")
generator_result = self.generator.generate_tests(
    self.target_dir,
    file_contents,  # Current code
    refactoring_plan
)

if not generator_result.get("success"):
    print(f"⚠️  Generator encountered issues (non-blocking)")
else:
    files_created = generator_result.get("test_files_created", 0)
    if files_created > 0:
        print(f"✅ [GENERATOR] Created {files_created} test file(s)")
    else:
        print(f"✅ [GENERATOR] Tests already exist")
```

---

## IMPLEMENTATION 5: Judge LLM Diagnosis

### File: `src/agents/judge.py` (MODIFY)

Add to execute() method after test run:

```python
def execute(self, target_dir: str) -> Dict[str, Any]:
    """
    Main execution - run pytest on target directory.
    """
    if not os.path.isdir(target_dir):
        return {
            "tests_passed": False,
            "test_output": f"Target directory not found: {target_dir}",
            "failed_tests": [],
            "test_count": 0,
            "model": self.model_name
        }
    
    # Step 1: Run pytest
    test_output, success = self._run_pytest(target_dir)
    
    # Step 2: Parse results
    failed_tests = self._extract_failed_tests(test_output)
    test_count = self._count_tests(test_output)
    
    result = {
        "tests_passed": success,
        "test_output": test_output,
        "failed_tests": failed_tests,
        "test_count": test_count,
        "model": self.model_name
    }
    
    # Step 3: ✅ NEW - If tests failed, diagnose with LLM
    if not success and test_output:
        try:
            diagnosis = self._diagnose_failures(test_output, target_dir)
            result["diagnosis"] = diagnosis
            result["feedback_for_fixer"] = diagnosis
            
            # LOG THE DIAGNOSIS
            log_experiment(
                agent_name="Judge",
                model_used="gemini-2.0-flash",
                action=ActionType.DEBUG,
                details={
                    "input_prompt": self._build_diagnosis_prompt(test_output, target_dir),
                    "output_response": diagnosis,
                    "failed_tests_count": len(failed_tests),
                    "test_output": test_output[:500]  # First 500 chars
                },
                status="FAILURE"
            )
        except Exception as e:
            print(f"⚠️  Diagnosis failed: {str(e)}")
            result["diagnosis"] = f"Diagnosis failed: {str(e)}"
    
    return result


def _diagnose_failures(self, test_output: str, target_dir: str) -> str:
    """
    Use LLM to diagnose test failures and suggest fixes.
    
    Args:
        test_output (str): Pytest output with errors
        target_dir (str): Directory with code
        
    Returns:
        str: LLM diagnosis and suggestions
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.schema import HumanMessage
    import os
    
    api_key = os.getenv("GOOGLE_API_KEY")
    client = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=api_key)
    
    prompt = self._build_diagnosis_prompt(test_output, target_dir)
    
    try:
        message = HumanMessage(content=prompt)
        response = client.invoke([message])
        return response.content
    except Exception as e:
        raise Exception(f"LLM diagnosis failed: {str(e)}")


def _build_diagnosis_prompt(self, test_output: str, target_dir: str) -> str:
    """Build prompt for test failure diagnosis."""
    prompt = f"""You are an expert Python developer debugging failed tests. Analyze these test failures:

TEST OUTPUT:
```
{test_output}
```

ANALYZE AND PROVIDE:
1. Root cause: What is the core issue causing these test failures?
2. Specific problems: List the specific bugs or issues in the code
3. Suggested fixes: Provide concrete code changes to fix these issues
4. Priority: Which issues should be fixed first?
5. Prevention: What changes would prevent these failures?

Focus on actionable insights that the Fixer agent can use to correct the code.
Be specific about line numbers and code changes needed."""
    
    return prompt
```

Also add import at top of judge.py:
```python
from src.utils.logger import log_experiment, ActionType
```

---

## IMPLEMENTATION 6: Add File Chunking to Fixer

### File: `src/agents/fixer.py` (UPDATE)

Add chunking in `execute()` method:

```python
def execute(self, target_dir: str, refactoring_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main execution - apply fixes to files based on refactoring plan.
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
        
        if not issues:
            continue
        
        try:
            # Read original file
            original_code = self._read_file(file_path)
            
            # ✅ NEW: Chunk if large
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
                fixed_code = self._get_fixed_code(fix_prompt)
            
            # Extract code from markdown
            fixed_code = self._extract_code(fixed_code)
            
            # Write fixed code
            self._write_file(file_path, fixed_code)
            
            # LOG
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
            
            print(f"✅ Fixed: {file_path}")
        
        except Exception as e:
            # ... error handling ...
            pass
    
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
    import time
    
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
```

---

## IMPLEMENTATION 7: Error Context Propagation

### File: `main.py` (MODIFY Orchestrator)

Update the main loop to track and pass error context:

```python
def run_orchestration_loop(self) -> bool:
    """Run main orchestration loop with error context."""
    previous_errors = None
    
    for iteration in range(1, self.max_iterations + 1):
        self.current_iteration = iteration
        
        try:
            # Step 1: AUDITOR (with error context from previous iteration)
            print(f"\n🔍 [AUDITOR] Analyzing code (iteration {iteration})...")
            
            audit_context = ""
            if previous_errors:
                audit_context = f"\n\nPREVIOUS ITERATION ERRORS:\n{previous_errors[:1000]}"
            
            audit_result = self.auditor.analyze(self.target_dir)
            
            # ... rest of the loop ...
            
            # Store errors if tests fail
            if not tests_passed:
                previous_errors = test_output + "\n" + judge_result.get("diagnosis", "")
                
                self.execution_history.append({
                    "iteration": iteration,
                    "status": "FAILED",
                    "test_errors": test_output,
                    "diagnosis": judge_result.get("diagnosis")
                })
                
                continue
        
        except Exception as e:
            # ... error handling ...
            pass
```

---

## Summary Checklist

After implementing all changes:

- [ ] Pylint integration in `analysis.py`
- [ ] Auditor updated to use pylint & chunking
- [ ] Generator agent created
- [ ] Orchestrator updated to call Generator
- [ ] Judge updated with LLM diagnosis
- [ ] Fixer updated with chunking & retry logic
- [ ] Error context propagation in loop
- [ ] All new code uses correct `ActionType` enums
- [ ] All LLM calls include `input_prompt` + `output_response` in logs
- [ ] Sandbox validation in file operations
- [ ] Test locally with `python check_setup.py`
- [ ] Run on example: `python main.py --target_dir "./sandbox/dataset_inconnu"`


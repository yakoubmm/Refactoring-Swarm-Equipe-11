"""
API Call Purposes - Comprehensive Guide
Each agent makes ONE API call to Gemini for a specific purpose
"""

╔════════════════════════════════════════════════════════════════════════════╗
║                         API CALL PURPOSES BY AGENT                         ║
╚════════════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════════════
🔍 API CALL #1: AUDITOR AGENT
═══════════════════════════════════════════════════════════════════════════════

File:     src/agents/auditor.py (Line 107 & 252)
Method:   _call_llm_with_retry()
API Call: self.client.invoke([message])

PURPOSE:
  Analyze Python source code and GENERATE A REFACTORING PLAN

INPUTS SENT TO GEMINI:
  ├─ All Python file contents from target directory
  ├─ Pylint analysis report (code quality violations)
  ├─ Line-by-line issues with severity levels
  └─ Previous errors (if iterating after failed tests)

PROMPT STRUCTURE:
  "You are a code quality expert. Analyze these Python files:
   [File 1 code]
   [File 2 code]
   ...
   
   Pylint found these issues:
   [Pylint output]
   
   Generate a structured plan with:
   1. Issues to fix (organized by file)
   2. Severity levels (error/warning/style)
   3. Specific line numbers where changes needed
   4. Recommended fixes for each issue"

OUTPUT FROM GEMINI:
  ✓ Structured refactoring plan (JSON-like)
  ✓ List of all code issues found
  ✓ Priority ordering for fixes
  ✓ Recommendations for each file

EXAMPLE OUTPUT:
  {
    "files": {
      "string_utils.py": {
        "issues": [
          {
            "line": 5,
            "issue": "unused import 'os'",
            "severity": "warning",
            "fix": "Remove line 5"
          },
          {
            "line": 12,
            "issue": "inconsistent spacing in format string",
            "severity": "style",
            "fix": "Change double space to single space"
          }
        ]
      }
    },
    "summary": "Found 5 issues across 2 files"
  }

WHY THIS API CALL?
  → Human brains + LLMs are good at understanding intent
  → Pylint finds WHAT's wrong, Gemini explains WHY and HOW to fix
  → Creates intelligent, context-aware fixes (not just regex replacements)

═══════════════════════════════════════════════════════════════════════════════
🔧 API CALL #2: FIXER AGENT
═══════════════════════════════════════════════════════════════════════════════

File:     src/agents/fixer.py (Line 137 & similar)
Method:   _get_fixed_code() → _call_llm_with_retry()
API Call: self.client.invoke([message])

PURPOSE:
  GENERATE CORRECTED CODE by applying the fixes identified by AUDITOR

INPUTS SENT TO GEMINI:
  ├─ Original Python source code (with issues)
  ├─ The refactoring plan from AUDITOR
  ├─ Specific issues to fix in this file
  ├─ Line numbers and descriptions of problems
  └─ Context about what "good" code looks like

PROMPT STRUCTURE:
  "You are a Python code refactoring expert. Here is Python code with issues:
   
   [Original code with line numbers]
   
   Based on this refactoring plan:
   1. Remove unused import 'os' (line 5)
   2. Fix inconsistent spacing (line 12)
   3. Add missing docstrings (lines 20-25)
   4. Replace bare except (line 30)
   
   Generate ONLY the corrected Python code.
   Keep all functionality the same.
   Only fix the identified issues.
   Return complete working code."

OUTPUT FROM GEMINI:
  ✓ Fixed Python source code
  ✓ All issues resolved from the plan
  ✓ Code syntax is valid and executable
  ✓ Comments added if needed

EXAMPLE TRANSFORMATION:
  
  BEFORE (with issues):
  ─────────────────────
  import os  # ← Unused
  import sys
  
  def format_name(first, last):
      return f"{first}  {last}"  # ← Double space
  
  def dangerous_divide(a, b):
      try:
          return a / b
      except:  # ← Bare except - bad!
          return None
  
  AFTER (fixed):
  ──────────────
  import sys
  
  def format_name(first, last):
      """Format a full name with proper spacing."""
      return f"{first} {last}"
  
  def dangerous_divide(a, b):
      """Safely divide two numbers."""
      try:
          return a / b
      except ZeroDivisionError:  # ← Specific exception
          return None

WHY THIS API CALL?
  → Gemini can understand context better than simple regex patterns
  → Handles complex refactoring that requires understanding semantics
  → Adds documentation/docstrings intelligently
  → Preserves functionality while improving quality
  → Much safer than automated regex replacements

═══════════════════════════════════════════════════════════════════════════════
📝 API CALL #3: GENERATOR AGENT
═══════════════════════════════════════════════════════════════════════════════

File:     src/agents/generator.py (Line 155-166)
Method:   _call_llm_with_retry()
API Call: self.client.invoke([message])

PURPOSE:
  GENERATE TEST FILES (pytest) for validating the fixed code

INPUTS SENT TO GEMINI:
  ├─ The fixed Python source code
  ├─ Function signatures and parameters
  ├─ Docstrings describing what functions do
  ├─ The audit plan (issues that were fixed)
  └─ Best practices for pytest

PROMPT STRUCTURE:
  "You are a Python testing expert. Generate comprehensive pytest tests for:
   
   [Fixed Python source code]
   
   Requirements:
   1. Test each function with valid inputs
   2. Test edge cases (empty lists, None values, etc.)
   3. Test error conditions if applicable
   4. Follow pytest best practices
   5. Use descriptive test names
   6. Include docstrings
   7. Import the module correctly
   
   Return ONLY the test file code in Python format."

OUTPUT FROM GEMINI:
  ✓ Complete pytest test file (test_*.py)
  ✓ Tests for each function in the source
  ✓ Edge case coverage
  ✓ Ready to run with pytest

EXAMPLE GENERATED TEST:
  ────────────────────
  """Tests for string_utils module."""
  import pytest
  from string_utils import format_name, count_vowels
  
  def test_format_name():
      """Test name formatting."""
      assert format_name("John", "Doe") == "John Doe"
      assert format_name("", "") == ""
      assert format_name("Jane", "Smith") == "Jane Smith"
  
  def test_count_vowels():
      """Test vowel counting."""
      assert count_vowels("hello") == 2
      assert count_vowels("xyz") == 0
      assert count_vowels("AEIOU") == 5

WHY THIS API CALL?
  → LLMs are better at understanding function intent from code
  → Can infer test cases automatically
  → Ensures test quality beyond simple "does it run"
  → Tests validate that fixes actually work correctly
  → User doesn't need to write tests themselves

═══════════════════════════════════════════════════════════════════════════════
✔️ API CALL #4: JUDGE AGENT (OPTIONAL - Only if tests fail)
═══════════════════════════════════════════════════════════════════════════════

File:     src/agents/judge.py (Line 128 & 186)
Method:   _diagnose_failures() → _call_llm_with_retry()
API Call: self.llm.invoke(prompt)

PURPOSE:
  DIAGNOSE WHY TESTS ARE FAILING and provide feedback for improvement

INPUTS SENT TO GEMINI:
  ├─ The test failure output (from pytest)
  ├─ Error messages and stack traces
  ├─ The fixed code (to understand context)
  ├─ The test code (to understand what was tested)
  └─ Import errors or syntax problems

PROMPT STRUCTURE:
  "You are a Python debugging expert. Tests are failing:
   
   Test output:
   [pytest error messages]
   
   Source code that was tested:
   [Fixed source code]
   
   Test code:
   [The test file]
   
   Diagnose:
   1. Why tests are failing
   2. Whether it's a fixer issue or test issue
   3. What should be fixed next
   4. Provide specific recommendations"

OUTPUT FROM GEMINI:
  ✓ Analysis of why tests failed
  ✓ Root cause identification
  ✓ Recommendations for fixing
  ✓ Guidance for next iteration

EXAMPLE DIAGNOSIS:
  ────────────────
  "The tests failed because:
   - Line 15 has import error: 'from string_utils import format_name'
   - The fixer didn't preserve the correct function signature
   - Recommendation: Re-run fixer with updated prompt focusing on preserving
     the original function signatures
   
   Next steps:
   1. Verify format_name function exists
   2. Check import paths are correct
   3. Run fixer again with stricter constraints"

WHEN IS THIS CALLED?
  → Only if tests fail (test_output not all passed)
  → Only if LLM is available (optional)
  → Purpose is to provide FEEDBACK for the next iteration loop

WHY THIS API CALL?
  → Automated error diagnosis is complex
  → Human-readable explanations help orchestrator decide what to do
  → Enables iterative improvement (loop feedback)
  → Makes debugging output actionable

═══════════════════════════════════════════════════════════════════════════════
📊 SUMMARY TABLE: API CALLS AND PURPOSES
═══════════════════════════════════════════════════════════════════════════════

┌─────────┬──────────┬──────────────────┬──────────────────┬────────────────┐
│ Agent   │ Call #   │ Purpose          │ Input            │ Output         │
├─────────┼──────────┼──────────────────┼──────────────────┼────────────────┤
│AUDITOR  │    1     │ Analyze code &   │ Source code +    │ Refactoring    │
│         │          │ generate plan    │ Pylint report    │ plan (JSON)    │
├─────────┼──────────┼──────────────────┼──────────────────┼────────────────┤
│FIXER    │    2     │ Generate fixed   │ Source code +    │ Fixed Python   │
│         │          │ code             │ Audit plan       │ code           │
├─────────┼──────────┼──────────────────┼──────────────────┼────────────────┤
│GENERATOR│    3     │ Generate tests   │ Fixed code +     │ Test file      │
│         │          │                  │ Function info    │ (pytest)       │
├─────────┼──────────┼──────────────────┼──────────────────┼────────────────┤
│JUDGE    │    4*    │ Diagnose failures│ Test failures +  │ Diagnosis &    │
│         │ (optional)                  │ Code & tests     │ feedback       │
└─────────┴──────────┴──────────────────┴──────────────────┴────────────────┘

* Only called if tests fail AND LLM available

═══════════════════════════════════════════════════════════════════════════════
🔄 DATA FLOW: How the API Outputs Connect
═══════════════════════════════════════════════════════════════════════════════

AUDITOR API OUTPUT          FIXER API INPUT
(Refactoring plan)      →   (Plan guides which code to fix)
                        →   FIXER API OUTPUT
                            (Fixed code)
                                    ↓
                            GENERATOR API INPUT
                            (Needs code to test)
                                    ↓
                            GENERATOR API OUTPUT
                            (Test files created)
                                    ↓
                            JUDGE EXECUTION
                            (Run tests)
                                    ↓
                        Did tests pass?
                        /           \
                      YES             NO
                      ↓               ↓
                   SUCCESS        JUDGE API INPUT
                   Report         (Failure diagnosis)
                                      ↓
                                  JUDGE API OUTPUT
                                  (Diagnosis & feedback)
                                      ↓
                                  Loop back to AUDITOR
                                  with error context

═══════════════════════════════════════════════════════════════════════════════
💡 KEY INSIGHTS
═══════════════════════════════════════════════════════════════════════════════

1. LAYERED INTELLIGENCE:
   - Each agent specializes in ONE task
   - Uses LLM for that specific purpose
   - Chains outputs to create intelligent workflow

2. WHY NOT JUST REGEX?
   - API Calls #1-3 use LLMs because they need SEMANTIC understanding
   - Regex can't understand code intent
   - LLMs understand context and best practices

3. WHY DIFFERENT FROM PLAIN TEXT ANALYSIS?
   - AUDITOR: Goes beyond syntax checking → understands design patterns
   - FIXER: Goes beyond replacement → refactors intelligently
   - GENERATOR: Creates tests that validate INTENT, not just syntax
   - JUDGE: Provides human-readable diagnoses, not just error codes

4. THE LOOP:
   - If tests pass: Done! (3 API calls minimum)
   - If tests fail: Loop with feedback (4+ API calls)
   - Each loop can improve further

5. COST-BENEFIT:
   - 3 API calls minimum per project
   - Automats all code review + testing + documentation
   - Saves hours of manual work
   - Each call costs < $0.01 (depending on code size)

═══════════════════════════════════════════════════════════════════════════════

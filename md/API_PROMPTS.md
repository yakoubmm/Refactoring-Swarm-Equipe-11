# API Prompts Documentation

This document shows the exact prompts sent to Google Gemini API by each agent.

---

## 1. AUDITOR AGENT - Analysis Phase

**Model:** `gemini-2.0-flash`  
**Temperature:** 0.2 (low randomness)  
**Purpose:** Analyze code and identify issues

### Input to API:
```
You are a code quality expert. Analyze the following Python code and provide a detailed refactoring plan.

STATIC ANALYSIS REPORT (from pylint):
[pylint results with error codes, line numbers, severity]

CODE TO ANALYZE:
============================================================
FILE: ./sandbox/dataset_inconnu/calculator.py
============================================================
[full Python code contents]
[repeated for each file in the directory]

PREVIOUS ITERATION ERRORS (address these specifically):
[error messages from failed tests in previous iteration, if any]

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
{
  "analysis_summary": "Brief overview of code quality",
  "files": {
    "file_path": {
      "quality_score": 0.0-1.0,
      "issues": [
        {
          "type": "string",
          "severity": "critical|high|medium|low",
          "description": "string",
          "suggested_fix": "string"
        }
      ]
    }
  },
  "total_issues": number,
  "priority_actions": ["list of highest priority fixes"]
}

Provide the JSON response only, no additional text.
```

### Expected Output from API:
```json
{
  "analysis_summary": "The code has several issues...",
  "files": {
    "./sandbox/dataset_inconnu/calculator.py": {
      "quality_score": 0.65,
      "issues": [
        {
          "type": "bug",
          "severity": "critical",
          "description": "Function divide() allows division by zero",
          "suggested_fix": "Add check: if b == 0: raise ValueError('Cannot divide by zero')"
        },
        {
          "type": "style",
          "severity": "medium",
          "description": "Missing type hints on function parameters",
          "suggested_fix": "Add type hints: def add(a: float, b: float) -> float:"
        }
      ]
    }
  },
  "total_issues": 2,
  "priority_actions": ["Fix division by zero bug", "Add type hints"]
}
```

---

## 2. FIXER AGENT - Fix Phase

**Model:** `gemini-2.0-flash`  
**Temperature:** 0.2  
**Purpose:** Generate fixed code based on issues identified by Auditor

### Input to API:
```
You are an expert Python code refactorer. Fix the following Python code to address these issues:

FILE: ./sandbox/dataset_inconnu/calculator.py

ISSUES TO FIX:
1. [CRITICAL] bug
   Problem: Function divide() allows division by zero
   Suggested fix: Add check: if b == 0: raise ValueError('Cannot divide by zero')

2. [MEDIUM] style
   Problem: Missing type hints on function parameters
   Suggested fix: Add type hints: def add(a: float, b: float) -> float:

ORIGINAL CODE:
```python
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def divide(a, b):
    return a / b
```

REQUIREMENTS:
1. Fix all identified issues
2. Maintain the original functionality
3. Improve code quality and readability
4. Add docstrings if missing
5. Follow PEP 8 standards
6. Return ONLY the fixed Python code, wrapped in ```python ... ``` blocks
7. Do NOT add any explanations or comments outside the code block

FIXED CODE:
```

### Expected Output from API:
```python
def add(a: float, b: float) -> float:
    """Add two numbers and return the result."""
    return a + b

def subtract(a: float, b: float) -> float:
    """Subtract b from a and return the result."""
    return a - b

def divide(a: float, b: float) -> float:
    """Divide a by b with zero-check safety."""
    if b == 0:
        raise ValueError('Cannot divide by zero')
    return a / b
```

---

## 3. GENERATOR AGENT - Test Generation Phase

**Model:** `gemini-2.0-flash`  
**Temperature:** 0.2  
**Purpose:** Generate pytest test files

### Input to API:
```
You are an expert Python test engineer. Create comprehensive pytest tests for this code:

FILE: ./sandbox/dataset_inconnu/calculator.py

KNOWN ISSUES IN THIS FILE:
- CRITICAL: Function divide() allows division by zero
- MEDIUM: Missing type hints on function parameters

SOURCE CODE:
```python
def add(a: float, b: float) -> float:
    """Add two numbers and return the result."""
    return a + b

def subtract(a: float, b: float) -> float:
    """Subtract b from a and return the result."""
    return a - b

def divide(a: float, b: float) -> float:
    """Divide a by b with zero-check safety."""
    if b == 0:
        raise ValueError('Cannot divide by zero')
    return a / b
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

GENERATE THE COMPLETE TEST FILE:
```

### Expected Output from API:
```python
import pytest
from calculator import add, subtract, divide

def test_add_positive_numbers():
    """Test adding two positive numbers."""
    assert add(2, 3) == 5

def test_divide_by_zero():
    """Test that dividing by zero raises ValueError."""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)

def test_divide_normal():
    """Test normal division."""
    assert divide(10, 2) == 5.0
```

---

## 4. JUDGE AGENT - Validation Phase

**Note:** Judge does NOT call the API for testing. It runs `pytest` directly using subprocess.

The Judge does use the Gemini API only if tests fail, to diagnose the issues:

### Input to API (if tests fail):
```
Analyze why these tests failed and suggest fixes:

Test Failures:
[output from pytest showing failures]

Source Code:
[code being tested]

Provide diagnostic analysis and suggested fixes.
```

---

## Summary of API Calls per Iteration

For each orchestration iteration:

1. **Auditor** → 1 API call (analyze code + pylint)
2. **Fixer** → 1 API call per file with issues (fix code)
3. **Generator** → 1 API call per source file (create tests)
4. **Judge** → 0-1 API calls (only if tests fail AND diagnosing)

**Total API calls per iteration:** 3-5 calls (depending on files and failures)

---

## Token Usage Estimation

- Small file (<1000 LOC): ~500-1000 tokens per call
- Medium file (1000-5000 LOC): ~1000-3000 tokens per call
- Large file (>5000 LOC): Files are chunked, ~2000 tokens per chunk

---

## How to Monitor API Calls

All API interactions are logged to `logs/experiment_data.json`:

```bash
# View recent API calls
cat logs/experiment_data.json | jq '.[-10:]'

# Count API calls by agent
jq '.[] | select(.agent_name) | .agent_name' logs/experiment_data.json | sort | uniq -c
```

---

## Testing Without API

To test the system without making actual API calls, use the mock version:

```bash
python test_without_api.py
```

This returns canned responses instead of calling Gemini.

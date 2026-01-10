"""
AGENT RETURN CONTRACT
=====================

This document defines the exact return structure each agent MUST provide.
The Orchestrator depends on these exact keys and structures.

⚠️ CRITICAL: If agents don't return these exact structures, 
the orchestrator will crash or behave unpredictably.
"""

# ============================================================================
# AUDITOR RETURN CONTRACT
# ============================================================================

AUDITOR_RETURN_SUCCESS = {
    "success": True,                    # ✅ REQUIRED - bool
    "model": "gemini-pro",              # ✅ REQUIRED - str (model name used)
    "plan": {                           # ✅ REQUIRED - dict
        "files": {                      # REQUIRED - dict of files analyzed
            "file_path": {
                "issues": [             # List of issues found
                    {
                        "type": "string",
                        "severity": "critical|high|medium|low",
                        "description": "string",
                        "suggested_fix": "string"
                    }
                ],
                "quality_score": 0.0    # 0.0 to 1.0
            }
        },
        "total_issues": 0,              # Total count
        "priority_actions": []          # List of top priorities
    },
    "files_analyzed": 3                 # ✅ REQUIRED - int
}

AUDITOR_RETURN_FAILURE = {
    "success": False,                   # ✅ REQUIRED - bool
    "model": "gemini-pro",              # ✅ REQUIRED - str
    "error": "Error description"        # REQUIRED on failure
}


# ============================================================================
# FIXER RETURN CONTRACT
# ============================================================================

FIXER_RETURN_SUCCESS = {
    "success": True,                    # ✅ REQUIRED - bool
    "model": "gemini-pro",              # ✅ REQUIRED - str (model name used)
    "files_modified": 2,                # ✅ REQUIRED - int (count of fixed files)
    "changes_made": [                   # ✅ REQUIRED - list of changes
        {
            "file": "path/to/file.py",
            "issues_fixed": 3,
            "status": "modified"
        }
    ]
}

FIXER_RETURN_FAILURE = {
    "success": False,                   # ✅ REQUIRED - bool
    "model": "gemini-pro",              # ✅ REQUIRED - str
    "files_modified": 0,                # ✅ REQUIRED - int (0 on failure)
    "error": "Error description"        # REQUIRED on failure
}


# ============================================================================
# JUDGE RETURN CONTRACT
# ============================================================================

JUDGE_RETURN = {
    "tests_passed": True,               # ✅ REQUIRED - bool
    "test_output": "pytest output...",  # ✅ REQUIRED - str (raw output)
    "failed_tests": [],                 # List of failed test details
    "test_count": 5,                    # Count of tests
    "model": "pytest"                   # Model/tool used (always "pytest")
}


# ============================================================================
# ORCHESTRATOR EXPECTATIONS
# ============================================================================

"""
The Orchestrator in main.py checks for these keys:

1. AUDITOR:
   - audit_result["success"]       → bool
   - audit_result["plan"]          → dict (has "files" key)
   - audit_result["model"]         → str (for logging)

2. FIXER:
   - fix_result["success"]         → bool
   - fix_result["files_modified"]  → int
   - fix_result["model"]           → str (for logging)

3. JUDGE:
   - judge_result["tests_passed"]  → bool
   - judge_result["test_output"]   → str
   - judge_result["model"]         → str (always "pytest")

If any of these keys are missing or have wrong type,
the orchestrator will fail with KeyError or TypeError.
"""

# ============================================================================
# VERIFICATION CHECKLIST
# ============================================================================

"""
Before submitting, verify:

✅ Auditor.execute() returns dict with:
   - "success" (bool)
   - "model" (str)
   - "plan" (dict with "files" key)
   - "files_analyzed" (int)

✅ Fixer.execute() returns dict with:
   - "success" (bool)
   - "model" (str)
   - "files_modified" (int)
   - "changes_made" (list)

✅ Judge.execute() returns dict with:
   - "tests_passed" (bool)
   - "test_output" (str)
   - "failed_tests" (list)
   - "test_count" (int)
   - "model" (str = "pytest")

✅ Agents log LLM calls ONLY (with input_prompt + output_response)

✅ Orchestrator logs only high-level events (iterations, final status)

✅ All ActionType values are correct (ANALYSIS, FIX, DEBUG)
"""

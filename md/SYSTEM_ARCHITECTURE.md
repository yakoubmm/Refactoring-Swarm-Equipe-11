# The Refactoring Swarm - Complete System Architecture

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATOR INITIALIZATION                         │
│  • Validate target_dir                                                       │
│  • Initialize agents (Auditor, Fixer, Generator, Judge)                     │
│  • Set max_iterations = 10                                                   │
│  • Initialize iteration counter = 1                                          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
        ┌──────────────────────────────────────────────────────────┐
        │                                                          │
        │        ╔═══════════════════════════════════════════╗    │
        │        ║   ITERATION LOOP (max 10 times)           ║    │
        │        ╚═══════════════════════════════════════════╝    │
        │                       │                                 │
        │                       ▼                                 │
        │      ┌────────────────────────────────────────┐        │
        │      │   PHASE 1: AUDITOR ANALYSIS            │        │
        │      │   (ActionType.ANALYSIS)                │        │
        │      └────────────────────────────────────────┘        │
        │                       │                                 │
        │      ┌────────────────┴────────────────┐               │
        │      │                                 │               │
        │      ▼                                 ▼               │
        │   ┌──────────────┐            ┌──────────────────┐    │
        │   │ find_python_ │            │  read_file()     │    │
        │   │   files()    │            │  (all .py files) │    │
        │   └──────────────┘            └──────────────────┘    │
        │      │                                 │               │
        │      └────────────────┬────────────────┘               │
        │                       ▼                                │
        │   ┌──────────────────────────────────────────────┐   │
        │   │  pylint execution (analysis.py)              │   │
        │   │  • Run pylint on all files                   │   │
        │   │  • Collect quality report & scores           │   │
        │   │  • Output: {file: score, issues}             │   │
        │   └──────────────────────────────────────────────┘   │
        │      │                                                │
        │      ▼                                                │
        │   ┌──────────────────────────────────────────────┐   │
        │   │  CHUNK LARGE FILES (if > token limit)        │   │
        │   │  • Split code into manageable chunks         │   │
        │   │  • Process sequentially to LLM               │   │
        │   └──────────────────────────────────────────────┘   │
        │      │                                                │
        │      ▼                                                │
        │   ┌──────────────────────────────────────────────┐   │
        │   │  LLM CALL (Gemini) - Auditor Prompt         │   │
        │   │  Input:                                      │   │
        │   │  • Code + pylint report                      │   │
        │   │  • Previous iteration errors (if loop)       │   │
        │   │  Output:                                     │   │
        │   │  • Refactoring plan (JSON):                  │   │
        │   │    {                                         │   │
        │   │      "files": {                              │   │
        │   │        "file.py": {                          │   │
        │   │          "issues": [                         │   │
        │   │            {                                 │   │
        │   │              "type": "string",               │   │
        │   │              "severity": "critical|high",    │   │
        │   │              "description": "...",           │   │
        │   │              "suggested_fix": "..."          │   │
        │   │            }                                 │   │
        │   │          ],                                  │   │
        │   │          "quality_score": 0.45               │   │
        │   │        }                                     │   │
        │   │      },                                      │   │
        │   │      "total_issues": 12,                     │   │
        │   │      "priority_actions": [...]               │   │
        │   │    }                                         │   │
        │   └──────────────────────────────────────────────┘   │
        │      │                                                │
        │      ▼                                                │
        │   ┌──────────────────────────────────────────────┐   │
        │   │  LOG: log_experiment(                        │   │
        │   │    agent_name="Auditor",                     │   │
        │   │    model_used="gemini-2.0-flash",            │   │
        │   │    action=ActionType.ANALYSIS,               │   │
        │   │    details={                                 │   │
        │   │      "input_prompt": "...",  ◀─ MANDATORY   │   │
        │   │      "output_response": "...",  ◀─ MANDATORY │   │
        │   │      "files_analyzed": 3,                    │   │
        │   │      "pylint_scores": {...}                  │   │
        │   │    },                                        │   │
        │   │    status="SUCCESS"                          │   │
        │   │  )                                           │   │
        │   └──────────────────────────────────────────────┘   │
        │      │                                                │
        │      ▼                                                │
        │      ┌────────────────────────────────────────┐      │
        │      │   PHASE 2: FIXER CORRECTIONS           │      │
        │      │   (ActionType.FIX)                     │      │
        │      └────────────────────────────────────────┘      │
        │                       │                               │
        │      ┌────────────────┴────────────────┐              │
        │      │                                 │              │
        │      ▼                                 ▼              │
        │   ┌──────────────┐            ┌──────────────────┐   │
        │   │ For each     │            │  read_file()     │   │
        │   │ file in plan │            │  (original code) │   │
        │   └──────────────┘            └──────────────────┘   │
        │      │                                 │              │
        │      └────────────────┬────────────────┘              │
        │                       ▼                               │
        │   ┌──────────────────────────────────────────────┐   │
        │   │  CHUNK LARGE FILES (if > token limit)        │   │
        │   │  • Split code into manageable chunks         │   │
        │   │  • Apply fixes chunk by chunk                │   │
        │   └──────────────────────────────────────────────┘   │
        │      │                                                │
        │      ▼                                                │
        │   ┌──────────────────────────────────────────────┐   │
        │   │  LLM CALL (Gemini) - Fixer Prompt          │   │
        │   │  Input:                                      │   │
        │   │  • Original code                             │   │
        │   │  • Audit plan + issues to fix                │   │
        │   │  Output:                                     │   │
        │   │  • Fixed Python code                         │   │
        │   └──────────────────────────────────────────────┘   │
        │      │                                                │
        │      ▼                                                │
        │   ┌──────────────────────────────────────────────┐   │
        │   │  Retry Logic (if LLM call fails)             │   │
        │   │  • Exponential backoff (1s, 2s, 4s, 8s)      │   │
        │   │  • Max retries: 3                            │   │
        │   │  • Timeout: 60 seconds per attempt           │   │
        │   └──────────────────────────────────────────────┘   │
        │      │                                                │
        │      ▼                                                │
        │   ┌──────────────────────────────────────────────┐   │
        │   │  write_file() - SANDBOX ONLY                 │   │
        │   │  • Create .backup before overwriting         │   │
        │   │  • Write fixed code                          │   │
        │   │  • Validate path is in sandbox/              │   │
        │   └──────────────────────────────────────────────┘   │
        │      │                                                │
        │      ▼                                                │
        │   ┌──────────────────────────────────────────────┐   │
        │   │  LOG: log_experiment(                        │   │
        │   │    agent_name="Fixer",                       │   │
        │   │    model_used="gemini-2.0-flash",            │   │
        │   │    action=ActionType.FIX,                    │   │
        │   │    details={                                 │   │
        │   │      "input_prompt": "...",  ◀─ MANDATORY   │   │
        │   │      "output_response": "...",  ◀─ MANDATORY │   │
        │   │      "file": "file.py",                      │   │
        │   │      "issues_fixed": 3                       │   │
        │   │    },                                        │   │
        │   │    status="SUCCESS"                          │   │
        │   │  )                                           │   │
        │   └──────────────────────────────────────────────┘   │
        │      │                                                │
        │      ▼                                                │
        │      ┌────────────────────────────────────────┐      │
        │      │   PHASE 3: TEST GENERATION (if needed) │      │
        │      │   (ActionType.GENERATION)              │      │
        │      └────────────────────────────────────────┘      │
        │                       │                               │
        │      ┌────────────────┴────────────────┐              │
        │      ▼                                 ▼              │
        │   ┌──────────────────┐        ┌──────────────────┐   │
        │   │ Check if tests   │        │  list_python_    │   │
        │   │ exist in sandbox/│        │  files() in      │   │
        │   │ tests/           │        │  sandbox/tests/  │   │
        │   └──────────────────┘        └──────────────────┘   │
        │      │                                 │              │
        │      └─────────────┬──────────────────┘              │
        │                   ▼                                  │
        │          ┌──────────────────┐                        │
        │          │ Tests exist?     │                        │
        │          └──────┬───────┬───┘                        │
        │          ┌──────┘       └──────┐                     │
        │     YES  │                     │  NO                 │
        │          │                     ▼                     │
        │          │         ┌──────────────────────────────┐  │
        │          │         │ LLM CALL - Generate Tests    │  │
        │          │         │ Input:                       │  │
        │          │         │ • Current code (all files)   │  │
        │          │         │ • Audit plan (issues found)  │  │
        │          │         │ Output:                      │  │
        │          │         │ • pytest test files          │  │
        │          │         │   (test_*.py format)         │  │
        │          │         └──────────────────────────────┘  │
        │          │                     │                     │
        │          │                     ▼                     │
        │          │         ┌──────────────────────────────┐  │
        │          │         │ write_file() → sandbox/tests/│  │
        │          │         │ • Create test_*.py files     │  │
        │          │         │ • Ensure comprehensive       │  │
        │          │         │   coverage of issues         │  │
        │          │         └──────────────────────────────┘  │
        │          │                     │                     │
        │          │                     ▼                     │
        │          │         ┌──────────────────────────────┐  │
        │          │         │ LOG: log_experiment(         │  │
        │          │         │   agent_name="Generator",    │  │
        │          │         │   action=ActionType.GENERATION,
        │          │         │   details={                  │  │
        │          │         │     "input_prompt": "...",   │  │
        │          │         │     "output_response": "...", │  │
        │          │         │     "test_files_created": 2  │  │
        │          │         │   },                         │  │
        │          │         │   status="SUCCESS"           │  │
        │          │         │ )                            │  │
        │          │         └──────────────────────────────┘  │
        │          │                     │                     │
        │          └─────────────┬───────┘                     │
        │                        ▼                              │
        │      ┌────────────────────────────────────────┐      │
        │      │   PHASE 4: JUDGE VALIDATION            │      │
        │      │   (Tests & Diagnosis)                  │      │
        │      └────────────────────────────────────────┘      │
        │                       │                               │
        │                       ▼                               │
        │      ┌────────────────────────────────────────┐      │
        │      │ pytest execution (testing.py)          │      │
        │      │ • Run: pytest sandbox/ -v --tb=short   │      │
        │      │ • Capture: stdout + stderr             │      │
        │      │ • Result: tests_passed (bool)          │      │
        │      │ • Extract: failed_tests (list)         │      │
        │      └────────────────────────────────────────┘      │
        │                       │                               │
        │                       ▼                               │
        │              ╔════════════════╗                      │
        │              ║ ALL PASS? ✓    ║                      │
        │              ╚════╦═════════╦═╝                      │
        │                   │         │                        │
        │               YES │         │ NO                     │
        │                   ▼         ▼                        │
        │          ┌──────────────┐  ┌──────────────────────┐  │
        │          │ SUCCESS! 🎉  │  │ DIAGNOSIS PHASE      │  │
        │          │              │  │ (ActionType.DEBUG)   │  │
        │          │ log_experiment│  └──────────────────────┘  │
        │          │ (success)    │           │                │
        │          │              │           ▼                │
        │          │ Return: True │  ┌──────────────────────┐  │
        │          └──────────────┘  │ LLM CALL - Diagnose  │  │
        │                            │ Input:               │  │
        │                            │ • Failed test output │  │
        │                            │ • Current code       │  │
        │                            │ • Previous fixes     │  │
        │                            │ Output:              │  │
        │                            │ • Root cause analysis│  │
        │                            │ • Suggested fixes    │  │
        │                            │ • Retry hints        │  │
        │                            └──────────────────────┘  │
        │                                    │                 │
        │                                    ▼                 │
        │                            ┌──────────────────────┐  │
        │                            │ LOG: log_experiment( │  │
        │                            │   agent_name="Judge",│  │
        │                            │   action=ActionType. │  │
        │                            │         DEBUG,       │  │
        │                            │   details={          │  │
        │                            │     "input_prompt"   │  │
        │                            │       :"...",        │  │
        │                            │     "output_response"│  │
        │                            │       :"...",        │  │
        │                            │     "failed_tests"   │  │
        │                            │       :[...],        │  │
        │                            │     "diagnosis"      │  │
        │                            │       :"..."         │  │
        │                            │   },                 │  │
        │                            │   status="FAILURE"   │  │
        │                            │ )                    │  │
        │                            └──────────────────────┘  │
        │                                    │                 │
        │                                    ▼                 │
        │                            ┌──────────────────────┐  │
        │                            │ Has iterations left? │  │
        │                            │ (iteration < 10)     │  │
        │                            └─────┬──────┬─────────┘  │
        │                                  │      │            │
        │                          YES ◀───┘      └──► NO       │
        │                                              │        │
        │                                              ▼        │
        │                                    ┌──────────────┐   │
        │                                    │ FAILURE ❌   │   │
        │                                    │              │   │
        │                                    │ Max iters    │   │
        │                                    │ reached      │   │
        │                                    │              │   │
        │                                    │ Return: False│   │
        │                                    └──────────────┘   │
        │                                            │          │
        │     ┌──────────────────────────────────────┘          │
        │     │  PASS ERROR FEEDBACK TO NEXT ITERATION          │
        │     │  • Store test errors in context                 │
        │     │  • Send to Auditor in next loop                 │
        │     │  • Auditor re-analyzes with error context       │
        │     └──────────────────────────────────────┐          │
        │                                            │          │
        │                                    [LOOP BACK]        │
        │                                      │               │
        │                                   iteration++         │
        │                                      │               │
        │                                      ▼               │
        │                          ┌─────────────────────┐     │
        │                          │ Back to PHASE 1:    │     │
        │                          │ AUDITOR ANALYSIS    │     │
        │                          │ (with error context)│     │
        │                          └──────────┬──────────┘     │
        │                                     │               │
        │                                     │ iteration++    │
        │                                     │               │
        └─────────────────────────────────────┘               │
                                              │                │
                                              ▼                │
                                    ┌──────────────────┐       │
                                    │  EXIT            │       │
                                    │  return code     │       │
                                    │  0 = success     │       │
                                    │  1 = max iters   │       │
                                    └──────────────────┘       │
```

---

## Phase Details

### Phase 1: Auditor Analysis
- **Input**: Target directory with Python files
- **Process**:
  1. Find all `.py` files recursively
  2. Read file contents
  3. Run pylint on each file (get quality scores & issues)
  4. Chunk large files if needed (prevent token overflow)
  5. Send code + pylint report to LLM
  6. Parse response into structured plan
- **Output**: Refactoring plan (JSON) with issues, severity, suggested fixes
- **Logging**: `ActionType.ANALYSIS` with input_prompt + output_response

### Phase 2: Fixer Corrections
- **Input**: Refactoring plan from Auditor
- **Process**:
  1. For each file with issues:
     - Read original code
     - Chunk if large
     - Send to LLM with specific fixes
     - Extract corrected code
     - Create backup (.backup)
     - Write to file (sandbox only)
  2. Retry on failure (exponential backoff, max 3 attempts)
- **Output**: Modified files in sandbox
- **Logging**: `ActionType.FIX` with input_prompt + output_response

### Phase 3: Test Generation
- **Input**: Current code (fixed by Fixer)
- **Process**:
  1. Check if tests already exist in `sandbox/tests/`
  2. If NOT:
     - Send code to LLM to generate pytest files
     - Create comprehensive test coverage
     - Write to `sandbox/tests/test_*.py`
  3. If YES: Skip to Phase 4
- **Output**: pytest test files
- **Logging**: `ActionType.GENERATION` with input_prompt + output_response

### Phase 4: Judge Validation
- **Input**: Fixed code + tests
- **Process**:
  1. Run `pytest sandbox/ -v --tb=short`
  2. Capture output and exit code
  3. If **PASS**: End successfully ✅
  4. If **FAIL**:
     - Extract failed test names & error messages
     - Send test output + code to LLM for diagnosis
     - Get root cause analysis & suggested fixes
     - Loop back to Phase 2 (Fixer) with error context
- **Output**: Test results + diagnostics
- **Logging**: 
  - `ActionType.DEBUG` for failure diagnosis
  - Test validation also logged

---

## Critical Implementation Notes

### 1. **Mandatory Logging**
Every LLM call MUST include:
```python
log_experiment(
    agent_name="AgentName",
    model_used="gemini-2.0-flash",
    action=ActionType.ANALYSIS,  # or FIX, GENERATION, DEBUG
    details={
        "input_prompt": "...",      # ◀─ MANDATORY
        "output_response": "...",   # ◀─ MANDATORY
        "other_data": ...
    },
    status="SUCCESS" or "FAILURE"
)
```

### 2. **File Chunking Strategy**
For files > ~8000 tokens:
```python
def chunk_code(code, chunk_size=8000):
    """Split code into manageable chunks"""
    chunks = []
    current_chunk = ""
    for line in code.split('\n'):
        if len(current_chunk) + len(line) > chunk_size:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk += '\n' + line
    chunks.append(current_chunk)
    return chunks
```

### 3. **Retry Logic with Exponential Backoff**
```python
def retry_with_backoff(func, max_retries=3, initial_wait=1):
    """Retry with exponential backoff"""
    wait = initial_wait
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(wait)
            wait *= 2  # Exponential backoff
```

### 4. **Sandbox Security**
```python
def is_safe_path(filepath):
    """Ensure filepath is within sandbox/"""
    resolved = Path(filepath).resolve()
    sandbox = Path("sandbox").resolve()
    return resolved.is_relative_to(sandbox)
```

### 5. **Error Context Propagation**
The Judge's error output should be stored and passed to the next Auditor iteration:
```python
if not tests_passed:
    execution_history.append({
        "iteration": current_iteration,
        "test_errors": test_output,
        "diagnosis": llm_diagnosis  # From Judge's LLM call
    })
    # Pass to next Auditor: "Previous iteration failed with: {error}"
```

---

## Scoring Alignment

| Dimension | Criteria | Implementation |
|-----------|----------|-----------------|
| **Performance (40%)** | Tests pass? | Judge validates with pytest |
| | Pylint score improved? | Auditor runs pylint before & after |
| **Robustness (30%)** | No crashes? | Try-catch + logging |
| | Max 10 iterations? | Iteration counter check |
| | Respects --target_dir? | CLI argument handling |
| **Data Quality (30%)** | Valid experiment_data.json? | Strict logging protocol |
| | Complete history? | Every action logged |
| | All prompts recorded? | input_prompt + output_response mandatory |


# Quick Reference Card - The Refactoring Swarm

## System Overview (One Page)

```
INPUT:  folder/buggy_code.py  (with bugs and issues)
OUTPUT: folder/fixed_code.py  (tested and working)

PROCESS (Automated Loop - max 10 iterations):

  1️⃣ AUDITOR              2️⃣ FIXER                3️⃣ GENERATOR            4️⃣ JUDGE
  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐   ┌────────────┐
  │ • Read code     │    │ • Read code     │    │ • Check tests    │   │ • Run      │
  │ • Run pylint    │    │ • Fix issues    │    │ • Create if need │   │   pytest   │
  │ • Send to LLM   │    │ • Backup files  │    │ • Log generation │   │ • Pass? ✓  │
  │ • Get issues    │    │ • Log fixes     │    │                  │   │   Fail? ↻  │
  │ • Log ANALYSIS  │    │ • Log FIX       │    │ • Log GENERATION │   │ • Diagnose │
  └─────┬───────────┘    └────────┬────────┘    └────────┬─────────┘   │ • Log DEBUG│
        │                         │                      │            └────┬────────┘
        └──────────────┬──────────┘──────────────┬───────┘                 │
                       ▼                         ▼                         ▼
                  Refactoring Plan           Tests Generated        Test Results
                  (issues + fixes)           (or already exist)      (pass/fail)
                                                                          │
                                                        If FAIL: ──────────┘
                                                        If PASS: Done! ✅

KEY LOGGING REQUIREMENTS:
─────────────────────────
Every LLM call MUST log:
  log_experiment(
    agent_name = "AgentName",
    model_used = "gemini-2.0-flash",
    action = ActionType.ANALYSIS  # or FIX, GENERATION, DEBUG
    details = {
      "input_prompt": "...FULL PROMPT...",        ◀─ MANDATORY
      "output_response": "...FULL RESPONSE...",   ◀─ MANDATORY
      "other_data": ...
    },
    status = "SUCCESS" or "FAILURE"
  )
```

---

## Action Types (Enum)

```python
from src.utils.logger import ActionType

ActionType.ANALYSIS     # Auditor reads code, static analysis, finds bugs
ActionType.FIX          # Fixer rewrites code to fix issues
ActionType.GENERATION   # Generator creates new test files
ActionType.DEBUG        # Judge diagnoses test failures
```

---

## Missing Components (CRITICAL)

| # | Component | Where | Why | Status |
|---|-----------|-------|-----|--------|
| 1 | Pylint in Auditor | src/tools/analysis.py + auditor.py | Measure quality improvement | ❌ TODO |
| 2 | Generator Agent | src/agents/generator.py | Create tests automatically | ❌ TODO |
| 3 | Judge LLM Diagnosis | judge.py | Diagnose test failures intelligently | ❌ TODO |
| 4 | File Chunking | auditor.py, fixer.py | Handle large files | ⚠️ OPTIONAL |
| 5 | Retry Logic | agents | Recover from API errors | ⚠️ OPTIONAL |
| 6 | Error Context | main.py loop | Pass errors to next iteration | ⚠️ OPTIONAL |

---

## Grading Formula

```
TOTAL SCORE = (Performance × 0.40) + (Robustness × 0.30) + (DataQuality × 0.30)

PERFORMANCE (40%):
  ✓ Do final tests pass?
  ✓ Did Pylint score improve?  ◀─ Requires #1 (Pylint)

ROBUSTNESS (30%):
  ✓ System doesn't crash?
  ✓ Respects --target_dir?
  ✓ Max 10 iterations?

DATA QUALITY (30%):  ◀─ If ZERO, total score = ZERO
  ✓ experiment_data.json valid JSON?
  ✓ Contains ANALYSIS, FIX, GENERATION, DEBUG logs?
  ✓ Every log has input_prompt + output_response?
  ✓ Complete history of all iterations?

If any dimension = 0: TOTAL = 0 (AUTOMATIC FAILURE)
```

---

## Implementation Checklist

### Phase 1: CRITICAL (Do First)
- [ ] Implement `run_pylint_analysis()` in src/tools/analysis.py
- [ ] Update Auditor to call pylint and include report in prompt
- [ ] Create Generator agent (src/agents/generator.py)
- [ ] Add Generator call to Orchestrator (after Fixer, before Judge)
- [ ] Test: `python main.py --target_dir "./sandbox/dataset_inconnu"`
- [ ] Verify logs have: ANALYSIS, FIX, GENERATION entries

### Phase 2: IMPORTANT (Do Next)
- [ ] Add LLM diagnosis to Judge (ActionType.DEBUG)
- [ ] Update Orchestrator to pass error context to next iteration
- [ ] Test with intentionally buggy code in sandbox

### Phase 3: NICE-TO-HAVE (If Time)
- [ ] Implement file chunking for large files
- [ ] Add retry logic with exponential backoff
- [ ] Add sandbox path validation

### Final: BEFORE SUBMISSION
- [ ] Run `python check_setup.py`
- [ ] Check `logs/experiment_data.json` exists and is valid
- [ ] Verify all action types are present in logs
- [ ] Commit logs: `git add -f logs/experiment_data.json`
- [ ] Push to GitHub
- [ ] Test on multiple examples in sandbox

---

## Common Mistakes to Avoid

### ❌ WRONG:
```python
# Missing input_prompt or output_response
log_experiment(
    agent_name="Auditor",
    action=ActionType.ANALYSIS,
    details={"result": "found issues"},  # ❌ Missing prompts!
    status="SUCCESS"
)
```

### ✅ CORRECT:
```python
log_experiment(
    agent_name="Auditor",
    action=ActionType.ANALYSIS,
    details={
        "input_prompt": "Analyze this code...",      # ✅ Required
        "output_response": "I found these issues...", # ✅ Required
        "issues_found": 5
    },
    status="SUCCESS"
)
```

---

### ❌ WRONG:
```python
# Generator phase missing = no ActionType.GENERATION logs
# Result: Data Quality score = 0
for iteration in range(10):
    auditor_result = auditor.analyze(target_dir)    # ANALYSIS
    fixer_result = fixer.apply_fixes(target_dir)    # FIX
    # ❌ No test generation!
    judge_result = judge.validate(target_dir)       # Only has tests_passed/failed
```

### ✅ CORRECT:
```python
for iteration in range(10):
    auditor_result = auditor.analyze(target_dir)      # ✅ ANALYSIS
    fixer_result = fixer.apply_fixes(target_dir)      # ✅ FIX
    generator_result = generator.generate_tests()     # ✅ GENERATION
    judge_result = judge.validate(target_dir)         # ✅ DEBUG (on failure)
```

---

## Files to Create/Modify

```
CREATE:
  src/agents/generator.py          ← Copy from IMPLEMENTATION_GUIDE.md §3
  SYSTEM_ARCHITECTURE.md           ← ALREADY CREATED ✓
  AUDIT_REPORT.md                  ← ALREADY CREATED ✓
  IMPLEMENTATION_GUIDE.md          ← ALREADY CREATED ✓
  DELIVERY_SUMMARY.md              ← ALREADY CREATED ✓

MODIFY:
  src/tools/analysis.py            ← Add run_pylint_analysis()
  src/agents/auditor.py            ← Call pylint, add chunking
  src/agents/fixer.py              ← Add chunking, retry logic
  src/agents/judge.py              ← Add LLM diagnosis
  main.py                          ← Add generator call, error context
```

---

## Test Your Implementation

```bash
# 1. Check environment
python check_setup.py

# 2. Run on example
python main.py --target_dir "./sandbox/dataset_inconnu"

# 3. Check logs
cat logs/experiment_data.json | python -m json.tool

# 4. Verify all action types present
grep -c "ANALYSIS" logs/experiment_data.json
grep -c "FIX" logs/experiment_data.json
grep -c "GENERATION" logs/experiment_data.json
grep -c "DEBUG" logs/experiment_data.json

# 5. Run actual calculator tests
python -m pytest ./sandbox/dataset_inconnu -v
```

---

## Git Workflow (Team)

```bash
# Before starting work
git pull origin main

# Create your feature branch
git checkout -b feature/auditor-pylint

# Make changes, test locally
python main.py --target_dir "./sandbox/dataset_inconnu"

# Commit with clear message
git add .
git commit -m "feat: Add pylint integration to Auditor"

# Push your branch
git push origin feature/auditor-pylint

# Create Pull Request on GitHub
# (Get reviewed, merge to main)

# Force-add logs for submission
git add -f logs/experiment_data.json
git commit -m "data: Final submission logs"
git push origin main
```

---

## Final Submission Requirements

✅ **Must Have:**
1. Code runs: `python main.py --target_dir "./sandbox/dataset_inconnu"` succeeds
2. Logs exist: `logs/experiment_data.json` is valid JSON
3. Logs complete: Contains ANALYSIS, FIX, GENERATION, DEBUG entries
4. All prompts: Every log has `input_prompt` + `output_response`
5. Tests pass: Final code passes all tests
6. Git clean: All files committed (including logs with `git add -f`)

❌ **Will Fail If:**
- System crashes (Technical Robustness = 0)
- No logs (Data Quality = 0)
- Missing action types (Data Quality = 0)
- Only 1 commit at the end (Plagiarism detection)

---

## Quick Links to Docs

- **Understanding**: SYSTEM_ARCHITECTURE.md
- **What's Missing**: AUDIT_REPORT.md
- **Implementation Code**: IMPLEMENTATION_GUIDE.md
- **Full Summary**: DELIVERY_SUMMARY.md

**YOU ARE HERE**: Quick Reference Card (this file)

---

## Questions?

Before asking instructor:
1. Check SYSTEM_ARCHITECTURE.md for design questions
2. Check IMPLEMENTATION_GUIDE.md for code examples
3. Check spec documents for requirement questions

Good luck! 🚀


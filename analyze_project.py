"""
Project Analysis and Diagram Generation Script
Analyzes the Refactoring-Swarm project structure and generates diagrams
"""

import os
import json
from pathlib import Path


def analyze_project_structure():
    """Analyze the project structure and components."""
    
    root = Path(".")
    project_info = {
        "name": "Refactoring-Swarm-Equipe-11",
        "purpose": "Automated Python code refactoring using multi-agent system",
        "structure": {},
        "agents": {},
        "tools": {},
        "workflow": {}
    }
    
    # Analyze src/agents
    agents_dir = root / "src" / "agents"
    if agents_dir.exists():
        project_info["agents"] = {
            "base_agent.py": "Base class for all agents",
            "auditor.py": "Analyzes code for issues using pylint",
            "fixer.py": "Applies corrections to identified issues",
            "generator.py": "Generates missing test files",
            "judge.py": "Validates fixes by running tests"
        }
    
    # Analyze src/tools
    tools_dir = root / "src" / "tools"
    if tools_dir.exists():
        project_info["tools"] = {
            "analysis.py": "Code analysis and issue detection",
            "filesystem.py": "File system operations and discovery",
            "testing.py": "Test execution and validation"
        }
    
    # Analyze src/utils
    utils_dir = root / "src" / "utils"
    if utils_dir.exists():
        project_info["tools"]["utils"] = {
            "logger.py": "Logging and progress tracking",
            "quota.py": "API quota management"
        }
    
    project_info["workflow"] = {
        "stage_1": {
            "name": "AUDITOR",
            "description": "Analyzes Python files for code quality issues",
            "uses": ["analysis.py", "pylint"],
            "output": "Plan of issues to fix"
        },
        "stage_2": {
            "name": "FIXER",
            "description": "Applies automatic corrections based on audit plan",
            "uses": ["filesystem.py", "analysis.py"],
            "output": "Fixed Python files"
        },
        "stage_3": {
            "name": "GENERATOR",
            "description": "Generates test files if they don't exist",
            "uses": ["testing.py", "filesystem.py"],
            "output": "Test files in tests/ directory"
        },
        "stage_4": {
            "name": "JUDGE",
            "description": "Runs tests to validate all fixes",
            "uses": ["testing.py", "pytest"],
            "output": "Test results and validation report"
        }
    }
    
    return project_info


def generate_mermaid_workflow():
    """Generate Mermaid diagram for workflow."""
    
    mermaid_code = """graph TD
    A["🔍 User Uploads Unknown Python Files"] -->|target_dir| B["main.py"]
    
    B -->|1. Analyze| C["🔍 AUDITOR Agent"]
    C -->|Uses| C1["analysis.py<br/>pylint"]
    C -->|Generates| C2["📋 Audit Plan<br/>- Code Issues<br/>- Violations<br/>- Warnings"]
    
    C2 -->|2. Fix| D["🔧 FIXER Agent"]
    D -->|Uses| D1["filesystem.py<br/>analysis.py"]
    D -->|Applies| D2["✅ Auto Corrections<br/>- Fix syntax<br/>- Format code<br/>- Improve style"]
    
    D2 -->|3. Generate| E["📝 GENERATOR Agent"]
    E -->|Uses| E1["testing.py<br/>filesystem.py"]
    E -->|Creates| E2["🧪 Test Files<br/>- Auto-generated tests<br/>- Function validation<br/>- Edge cases"]
    
    E2 -->|4. Validate| F["✔️ JUDGE Agent"]
    F -->|Uses| F1["testing.py<br/>pytest"]
    F -->|Produces| F2["📊 Validation Report<br/>- Test results<br/>- Coverage<br/>- Status"]
    
    F2 -->|Output| G["✨ Refactored Project<br/>+ Test Files<br/>+ Report"]
    
    style C fill:#4CAF50,color:#fff
    style D fill:#FF9800,color:#fff
    style E fill:#2196F3,color:#fff
    style F fill:#9C27B0,color:#fff
    style G fill:#4CAF50,color:#fff
"""
    
    return mermaid_code


def generate_mermaid_architecture():
    """Generate Mermaid diagram for system architecture."""
    
    mermaid_code = """graph LR
    subgraph "Agents"
        A["AUDITOR<br/>Code Analysis"]
        B["FIXER<br/>Auto Repair"]
        C["GENERATOR<br/>Test Creation"]
        D["JUDGE<br/>Validation"]
    end
    
    subgraph "Tools"
        T1["analysis.py"]
        T2["filesystem.py"]
        T3["testing.py"]
    end
    
    subgraph "External"
        EXT1["pylint"]
        EXT2["pytest"]
    end
    
    subgraph "Utilities"
        U1["logger.py"]
        U2["quota.py"]
    end
    
    A -->|uses| T1
    A -->|uses| EXT1
    B -->|uses| T1
    B -->|uses| T2
    C -->|uses| T2
    C -->|uses| T3
    D -->|uses| T3
    D -->|uses| EXT2
    
    A -->|logs| U1
    B -->|logs| U1
    C -->|logs| U1
    D -->|logs| U1
    
    A -->|checks| U2
    B -->|checks| U2
    C -->|checks| U2
    D -->|checks| U2
    
    style A fill:#4CAF50,color:#fff
    style B fill:#FF9800,color:#fff
    style C fill:#2196F3,color:#fff
    style D fill:#9C27B0,color:#fff
"""
    
    return mermaid_code


def generate_data_flow_diagram():
    """Generate data flow diagram."""
    
    mermaid_code = """graph TD
    A["📂 Input: Python Files<br/>- Unknown code<br/>- Potential errors"]
    
    B["🔍 AUDITOR Analysis"]
    C["📋 Issues Found"]
    
    D["🔧 FIXER Corrections"]
    E["✅ Fixed Code"]
    
    F["📝 GENERATOR Tests"]
    G["🧪 Test Suite"]
    
    H["✔️ JUDGE Validation"]
    I["📊 Results"]
    
    J{"Tests<br/>Pass?"}
    
    K["✨ Success<br/>Refactored + Tests"]
    L["🔄 Loop Back<br/>with Error Feedback"]
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J -->|Yes| K
    J -->|No| L
    L --> B
    
    style A fill:#E3F2FD
    style B fill:#4CAF50,color:#fff
    style D fill:#FF9800,color:#fff
    style F fill:#2196F3,color:#fff
    style H fill:#9C27B0,color:#fff
    style K fill:#4CAF50,color:#fff
    style L fill:#F44336,color:#fff
"""
    
    return mermaid_code


def generate_project_description():
    """Generate comprehensive project description."""
    
    description = """
╔════════════════════════════════════════════════════════════════════════════╗
║                 REFACTORING-SWARM-EQUIPE-11 PROJECT OVERVIEW              ║
╚════════════════════════════════════════════════════════════════════════════╝

PROJECT NAME: Refactoring-Swarm-Equipe-11
PURPOSE: Automated Python code refactoring and quality improvement using a 
         multi-agent cooperative system

═══════════════════════════════════════════════════════════════════════════════

📁 PROJECT STRUCTURE
═══════════════════════════════════════════════════════════════════════════════

Refactoring-Swarm-Equipe-11/
├── main.py                    # Entry point - orchestrates the refactoring pipeline
├── check_setup.py             # Setup verification utility
├── requirements.txt           # Python dependencies
│
├── src/                       # Source code
│   ├── agents/                # Multi-agent system
│   │   ├── base_agent.py      # Abstract base class for all agents
│   │   ├── auditor.py         # Stage 1: Code analysis agent
│   │   ├── fixer.py           # Stage 2: Code fixing agent
│   │   ├── generator.py       # Stage 3: Test generation agent
│   │   └── judge.py           # Stage 4: Validation agent
│   │
│   ├── tools/                 # Shared utilities for agents
│   │   ├── analysis.py        # Code analysis tools (pylint integration)
│   │   ├── filesystem.py      # File system operations
│   │   └── testing.py         # Test execution and validation
│   │
│   └── utils/                 # General utilities
│       ├── logger.py          # Logging and progress tracking
│       └── quota.py           # API quota management
│
├── sandbox/                   # Test projects area
│   └── demo_project/          # Example project with errors
│       ├── string_utils.py    # Module with issues
│       ├── math_utils.py      # Module with issues
│       ├── list_utils.py      # Module with issues
│       └── tests/             # Auto-generated or provided tests
│           ├── test_string_utils.py
│           ├── test_math_utils.py
│           └── test_list_utils.py
│
├── test/                      # Testing utilities
│   ├── test_api.py            # API testing
│   ├── test_mock_run.py       # Mock workflow tests
│   └── test_without_api.py    # Local testing
│
├── logs/                      # Execution logs
│   ├── experiment_data.json   # Experiment metrics
│   └── quota_usage.json       # API usage tracking
│
└── md/                        # Documentation
    ├── START_HERE.md          # Quick start guide
    ├── SYSTEM_ARCHITECTURE.md # System design
    ├── IMPLEMENTATION_GUIDE.md# Implementation details
    ├── README_ANALYSIS.md     # Analysis details
    ├── AGENT_CONTRACT.md      # Agent interfaces
    └── ...                    # Other documentation

═══════════════════════════════════════════════════════════════════════════════

🤖 MULTI-AGENT SYSTEM
═══════════════════════════════════════════════════════════════════════════════

The system implements a 4-stage pipeline with specialized agents:

┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: AUDITOR AGENT 🔍                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Role:        Analyzes Python code for issues and violations                 │
│ Inputs:      Python source files from target directory                      │
│ Tools:       - analysis.py (code inspection)                                │
│              - pylint (static analysis)                                     │
│ Process:     1. Discover all Python files                                   │
│              2. Run pylint analysis                                         │
│              3. Extract issues and violations                               │
│              4. Create remediation plan                                     │
│ Outputs:     - Audit plan with categorized issues                          │
│              - Priority ordering for fixes                                  │
│ Example Issues:                                                              │
│   - Missing docstrings                                                      │
│   - Unused imports                                                          │
│   - Poor variable naming                                                    │
│   - Bare except clauses                                                     │
│   - Long lines                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: FIXER AGENT 🔧                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Role:        Applies automatic corrections to identified issues             │
│ Inputs:      Audit plan from AUDITOR                                        │
│ Tools:       - filesystem.py (file operations)                              │
│              - analysis.py (code transformation)                            │
│ Process:     1. Read audit plan                                             │
│              2. For each issue:                                             │
│                 - Parse affected file                                       │
│                 - Apply auto-fix rules                                      │
│                 - Validate syntax                                           │
│              3. Write corrected files                                       │
│              4. Track applied fixes                                         │
│ Outputs:     - Refactored Python files                                      │
│              - Fix report with details                                      │
│ Auto-Fixes Applied:                                                         │
│   - Remove unused imports                                                   │
│   - Add missing docstrings                                                  │
│   - Rename poorly-named variables                                           │
│   - Replace bare except with specific exceptions                            │
│   - Format code according to PEP 8                                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: GENERATOR AGENT 📝                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ Role:        Creates or updates test files for code validation              │
│ Inputs:      Fixed source files (from FIXER)                                │
│ Tools:       - testing.py (test generation)                                 │
│              - filesystem.py (file discovery)                               │
│ Process:     1. Check if tests/ directory exists                            │
│              2. Analyze each source module                                  │
│              3. For missing test files:                                     │
│                 - Inspect function signatures                               │
│                 - Generate basic test cases                                 │
│                 - Create test_*.py files                                    │
│              4. Ensure proper structure                                     │
│ Outputs:     - Test files in tests/ subdirectory                            │
│              - Test generation report                                       │
│ Generated Tests Include:                                                    │
│   - Basic functionality tests                                               │
│   - Edge case tests                                                         │
│   - Return value validation                                                 │
│   - Input parameter checking                                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: JUDGE AGENT ✔️                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Role:        Validates all fixes by running the test suite                  │
│ Inputs:      Fixed code + Generated tests                                   │
│ Tools:       - testing.py (pytest execution)                                │
│              - pytest (test framework)                                      │
│ Process:     1. Execute all tests in tests/ directory                       │
│              2. Collect test results                                        │
│              3. Analyze failures/errors                                     │
│              4. Generate validation report                                  │
│              5. Provide feedback for next iteration                         │
│ Outputs:     - Test results (pass/fail)                                     │
│              - Coverage metrics                                             │
│              - Validation report                                            │
│ Success Criteria:                                                           │
│   - All tests pass                                                          │
│   - No import errors                                                        │
│   - No runtime exceptions                                                   │
│   - Code quality improved                                                   │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

🔄 WORKFLOW PIPELINE
═══════════════════════════════════════════════════════════════════════════════

User Action:
    └─> python main.py --target_dir "./sandbox/dataset_inconnu"

Flow:
    1. main.py receives target directory
    2. AUDITOR analyzes all Python files
       ├─ Discovers .py files
       ├─ Runs pylint
       └─ Creates audit plan
    
    3. FIXER applies corrections
       ├─ Reads audit plan
       ├─ Auto-fixes issues
       └─ Saves corrected files
    
    4. GENERATOR creates tests if needed
       ├─ Checks for tests/ directory
       ├─ Analyzes source modules
       └─ Generates test files
    
    5. JUDGE validates everything
       ├─ Executes pytest
       ├─ Collects results
       └─ Reports status

    6. Loop handling:
       - If tests pass: ✅ Success - Report generated
       - If tests fail: 🔄 Loop restarts with error feedback

═══════════════════════════════════════════════════════════════════════════════

📊 DATA FLOW
═══════════════════════════════════════════════════════════════════════════════

Input Files (Unknown Code)
         ↓
    AUDITOR Analysis
         ↓
    Issues Detected (Plan)
         ↓
    FIXER Corrections
         ↓
    Fixed Source Code
         ↓
    GENERATOR Tests
         ↓
    Test Suite Created
         ↓
    JUDGE Validation
         ↓
    ┌───────────────┐
    │  Tests Pass?  │
    └───────────────┘
         ↙         ↘
       YES          NO
        ↓            ↓
     SUCCESS    Loop + Feedback
        ↓            ↓
    Report      [RETRY CYCLE]

═══════════════════════════════════════════════════════════════════════════════

🛠️ KEY TOOLS & LIBRARIES
═══════════════════════════════════════════════════════════════════════════════

Core Framework:
  - Python 3.11+
  - ast (Python abstract syntax tree)
  - subprocess (for tool execution)

Code Analysis:
  - pylint (static code analysis)
  - PEP 8 compliance checking

Testing:
  - pytest (test execution)
  - Test discovery and execution

File Operations:
  - pathlib (cross-platform paths)
  - os (file system access)

Logging & Tracking:
  - json (experiment tracking)
  - Custom logging module

═══════════════════════════════════════════════════════════════════════════════

💾 INPUT/OUTPUT FORMATS
═══════════════════════════════════════════════════════════════════════════════

INPUT:
  ├── Python source files (.py)
  ├── Optionally: existing test files
  └── Config: target_dir parameter

OUTPUT:
  ├── Refactored source files (.py)
  ├── Generated test files (tests/*.py)
  ├── Audit reports (logs/experiment_data.json)
  ├── Validation results (logs/quota_usage.json)
  └── Console output with status updates

═══════════════════════════════════════════════════════════════════════════════

🎯 USE CASES
═══════════════════════════════════════════════════════════════════════════════

1. Code Quality Improvement
   - Automatically improve code style
   - Fix common Python issues
   - Add missing documentation

2. Legacy Code Refactoring
   - Analyze old Python projects
   - Apply modern best practices
   - Generate test coverage

3. Test Generation
   - Create test suites for untested code
   - Generate validation tests
   - Ensure code quality

4. Batch Processing
   - Process multiple projects
   - Standardize code across repos
   - Maintain consistent quality

═══════════════════════════════════════════════════════════════════════════════

📈 METRICS & TRACKING
═══════════════════════════════════════════════════════════════════════════════

Tracked Metrics:
  - Files analyzed
  - Issues detected
  - Fixes applied
  - Tests generated
  - Test pass/fail rate
  - API quota usage (if using external APIs)
  - Execution time
  - Error recovery cycles

═══════════════════════════════════════════════════════════════════════════════
"""
    
    return description


def generate_all_outputs():
    """Generate all project analysis and diagrams."""
    
    # Analyze project
    project_info = analyze_project_structure()
    
    # Generate descriptions
    print(generate_project_description())
    
    # Generate diagrams
    print("\n" + "="*80)
    print("MERMAID DIAGRAM 1: WORKFLOW PIPELINE")
    print("="*80)
    print(generate_mermaid_workflow())
    
    print("\n" + "="*80)
    print("MERMAID DIAGRAM 2: SYSTEM ARCHITECTURE")
    print("="*80)
    print(generate_mermaid_architecture())
    
    print("\n" + "="*80)
    print("MERMAID DIAGRAM 3: DATA FLOW")
    print("="*80)
    print(generate_data_flow_diagram())
    
    # Generate JSON summary
    print("\n" + "="*80)
    print("PROJECT STRUCTURE (JSON)")
    print("="*80)
    print(json.dumps(project_info, indent=2))
    
    # Instructions for visualization
    print("\n" + "="*80)
    print("📊 HOW TO VISUALIZE THE DIAGRAMS")
    print("="*80)
    print("""
1. Copy any of the Mermaid diagrams above

2. Paste into one of these online editors:
   - https://mermaid.live/
   - https://mermaid-js.github.io/mermaid-live-editor/

3. Or install mermaid-cli locally:
   npm install -g @mermaid-js/mermaid-cli
   mmdc -i diagram.mmd -o diagram.png

4. Or use in documentation:
   - GitHub: Paste in README.md with ```mermaid block
   - GitLab: Paste in markdown with ```mermaid block
   - Confluence: Use Mermaid macro
   - Notion: Paste and convert to image

═══════════════════════════════════════════════════════════════════════════════
""")


if __name__ == "__main__":
    generate_all_outputs()

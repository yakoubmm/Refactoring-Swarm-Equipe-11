import argparse
import sys
import os
import json
from dotenv import load_dotenv
from src.utils.logger import log_experiment, ActionType
from src.agents.auditor import Auditor
from src.agents.fixer import Fixer
from src.agents.judge import Judge

load_dotenv()

# ============================================================================
# ORCHESTRATOR - Main Entry Point
# Role: Coordinate all agents and manage the self-healing loop
# ============================================================================

class Orchestrator:
    """
    Main orchestrator for the multi-agent refactoring system.
    Coordinates Auditor → Fixer → Judge loop with self-healing capability.
    """
    
    def __init__(self, target_dir: str, max_iterations: int = 10):
        self.target_dir = target_dir
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.auditor = Auditor()
        self.fixer = Fixer()
        self.judge = Judge()
        self.execution_history = []
    
    def validate_setup(self) -> bool:
        """Validate that target directory exists and is accessible."""
        if not os.path.exists(self.target_dir):
            print(f"❌ Target directory '{self.target_dir}' not found.")
            return False
        
        if not os.path.isdir(self.target_dir):
            print(f"❌ '{self.target_dir}' is not a directory.")
            return False
        
        # Check if directory contains Python files
        python_files = [f for f in os.listdir(self.target_dir) if f.endswith('.py')]
        if not python_files:
            print(f"⚠️  No Python files found in '{self.target_dir}'")
        
        print(f"✅ Target directory validated: {self.target_dir}")
        return True
    
    def run_orchestration_loop(self) -> bool:
        """
        Run the main orchestration loop:
        1. Auditor analyzes code → produces plan
        2. Fixer applies corrections
        3. Judge validates via tests
        Repeats until success or max iterations reached.
        """
        print("\n" + "="*70)
        print("🚀 STARTING ORCHESTRATION LOOP")
        print("="*70 + "\n")
        
        for iteration in range(1, self.max_iterations + 1):
            self.current_iteration = iteration
            print(f"\n{'─'*70}")
            print(f"📍 ITERATION {iteration}/{self.max_iterations}")
            print(f"{'─'*70}\n")
            
            try:
                # Step 1: AUDITOR ANALYSIS
                print(f"🔍 [AUDITOR] Analyzing code in '{self.target_dir}'...")
                audit_result = self.auditor.analyze(self.target_dir)
                
                if not audit_result.get("success"):
                    print(f"❌ Auditor analysis failed: {audit_result.get('error')}")
                    log_experiment(
                        agent_name="Auditor",
                        model_used=audit_result.get("model", "unknown"),
                        action=ActionType.ANALYSIS,
                        details={
                            "input_prompt": f"Analyze: {self.target_dir}",
                            "output_response": str(audit_result),
                            "iteration": iteration
                        },
                        status="FAILURE"
                    )
                    continue
                
                refactoring_plan = audit_result.get("plan", {})
                print(f"✅ [AUDITOR] Plan generated: {len(refactoring_plan.get('files', {}))} files analyzed")
                
                # Agent logs its own LLM interaction - No duplicate logging here
                # The Auditor already logged via ActionType.ANALYSIS
                
                # Step 2: FIXER APPLIES CORRECTIONS
                print(f"\n🔧 [FIXER] Applying corrections based on audit plan...")
                fix_result = self.fixer.apply_fixes(self.target_dir, refactoring_plan)
                
                if not fix_result.get("success"):
                    print(f"❌ Fixer failed: {fix_result.get('error')}")
                    log_experiment(
                        agent_name="Fixer",
                        model_used=fix_result.get("model", "unknown"),
                        action=ActionType.FIX,
                        details={
                            "input_prompt": json.dumps(refactoring_plan),
                            "output_response": str(fix_result),
                            "iteration": iteration
                        },
                        status="FAILURE"
                    )
                    continue
                
                files_modified = fix_result.get("files_modified", 0)
                print(f"✅ [FIXER] Applied fixes to {files_modified} file(s)")
                
                # Agent logs its own LLM interaction - No duplicate logging here
                # The Fixer already logged via ActionType.FIX
                
                # Step 3: JUDGE VALIDATES VIA TESTS
                print(f"\n✔️  [JUDGE] Running validation tests...")
                judge_result = self.judge.validate(self.target_dir)
                
                tests_passed = judge_result.get("tests_passed", False)
                test_output = judge_result.get("test_output", "")
                
                if tests_passed:
                    print(f"✅ [JUDGE] ALL TESTS PASSED! 🎉")
                    
                    # Orchestrator logs only high-level success event
                    log_experiment(
                        agent_name="Orchestrator",
                        model_used="pytest",
                        action=ActionType.DEBUG,
                        details={
                            "input_prompt": f"Validate fixed code: {self.target_dir}",
                            "output_response": "All tests passed - mission complete",
                            "iteration": iteration,
                            "all_tests_passed": True
                        },
                        status="SUCCESS"
                    )
                    print("\n" + "="*70)
                    print("🏆 MISSION COMPLETE - All tests passed!")
                    print("="*70 + "\n")
                    return True
                else:
                    # Tests failed - log and continue loop
                    print(f"⚠️  [JUDGE] Tests failed. Errors:\n{test_output}")
                    
                    # Orchestrator logs only high-level failure event
                    log_experiment(
                        agent_name="Orchestrator",
                        model_used="pytest",
                        action=ActionType.DEBUG,
                        details={
                            "input_prompt": f"Validate fixed code: {self.target_dir}",
                            "output_response": test_output,
                            "iteration": iteration,
                            "all_tests_passed": False
                        },
                        status="FAILURE"
                    )
                    
                    # Send errors back to Auditor for next iteration
                    print(f"\n🔄 Loop will restart with error feedback...")
                    self.execution_history.append({
                        "iteration": iteration,
                        "status": "FAILED",
                        "test_errors": test_output
                    })
                    continue
            
            except Exception as e:
                print(f"\n❌ Unexpected error in iteration {iteration}: {str(e)}")
                log_experiment(
                    agent_name="Orchestrator",
                    model_used="unknown",
                    action=ActionType.DEBUG,
                    details={
                        "input_prompt": f"Orchestration iteration {iteration}",
                        "output_response": str(e),
                        "iteration": iteration
                    },
                    status="FAILURE"
                )
                continue
        
        # Max iterations reached without success
        print("\n" + "="*70)
        print(f"❌ MISSION FAILED - Max iterations ({self.max_iterations}) reached")
        print("="*70 + "\n")
        return False
    
    def run(self) -> int:
        """Main execution method. Returns 0 on success, 1 on failure."""
        print("\n🎯 ORCHESTRATOR INITIALIZATION")
        print(f"Target Directory: {self.target_dir}")
        print(f"Max Iterations: {self.max_iterations}\n")
        
        # Validate setup
        if not self.validate_setup():
            return 1
        
        # Run orchestration loop
        success = self.run_orchestration_loop()
        
        return 0 if success else 1


def main():
    """Entry point - parse arguments and launch orchestrator."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Autonomous Code Refactoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --target_dir "./sandbox"
  python main.py --target_dir "/path/to/code" --max_iterations 5
        """
    )
    
    parser.add_argument(
        "--target_dir",
        type=str,
        required=True,
        help="Path to the directory containing Python files to refactor"
    )
    
    parser.add_argument(
        "--max_iterations",
        type=int,
        default=10,
        help="Maximum number of orchestration loops (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Create and run orchestrator
    orchestrator = Orchestrator(
        target_dir=args.target_dir,
        max_iterations=args.max_iterations
    )
    
    exit_code = orchestrator.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
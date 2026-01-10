import subprocess
import sys
import json
from typing import Dict, Any


def run_pylint(file_path: str) -> Dict[str, str]:
    """
    Run pylint on a Python file and return its output and score.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pylint", file_path, "--score=y"],
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout + result.stderr

        score = None
        for line in output.splitlines():
            if "rated at" in line:
                score = line.split("rated at")[-1].strip()

        return {
            "success": result.returncode == 0,
            "score": score,
            "output": output
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "score": None,
            "output": "pylint timed out"
        }


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
                    "messages": [...]
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
                sys.executable, "-m", "pylint",
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
            try:
                pylint_output = json.loads(result.stdout)
                
                # Calculate overall score and aggregate data
                files_data = {}
                total_issues = len(pylint_output) if pylint_output else 0
                overall_score = 10.0  # Start at perfect score
                
                # Group messages by file
                for message in (pylint_output or []):
                    filepath = message.get("path", "unknown")
                    if filepath not in files_data:
                        files_data[filepath] = {
                            "issues_count": 0,
                            "messages": []
                        }
                    
                    files_data[filepath]["issues_count"] += 1
                    files_data[filepath]["messages"].append({
                        "line": message.get("line"),
                        "column": message.get("column"),
                        "type": message.get("type"),
                        "message": message.get("message"),
                        "symbol": message.get("symbol")
                    })
                
                # Estimate score based on issue types
                # (This is approximate; real pylint score comes from final_score if available)
                issue_counts = {
                    "fatal": 0,
                    "error": 0,
                    "warning": 0,
                    "refactor": 0,
                    "convention": 0
                }
                
                for message in (pylint_output or []):
                    msg_type = message.get("type", "warning").lower()
                    if msg_type in issue_counts:
                        issue_counts[msg_type] += 1
                
                # Deduct points based on issues (rough scoring)
                overall_score -= issue_counts.get("fatal", 0) * 2.0
                overall_score -= issue_counts.get("error", 0) * 1.5
                overall_score -= issue_counts.get("warning", 0) * 0.5
                overall_score -= issue_counts.get("refactor", 0) * 0.3
                overall_score -= issue_counts.get("convention", 0) * 0.1
                
                overall_score = max(0.0, min(10.0, overall_score))
                
                return {
                    "success": True,
                    "overall_score": round(overall_score, 2),
                    "files": files_data,
                    "total_issues": total_issues,
                    "issue_types": issue_counts
                }
            
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "success": False,
                    "overall_score": 0,
                    "files": {},
                    "total_issues": 0,
                    "error": "Failed to parse pylint JSON output"
                }
        else:
            # No output (possibly no issues found)
            return {
                "success": True,
                "overall_score": 10.0,
                "files": {},
                "total_issues": 0,
                "issue_types": {}
            }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "overall_score": 0,
            "files": {},
            "total_issues": 0,
            "error": "pylint timed out after 120 seconds"
        }
    
    except Exception as e:
        return {
            "success": False,
            "overall_score": 0,
            "files": {},
            "total_issues": 0,
            "error": f"Error running pylint: {str(e)}"
        }


def format_analysis_for_llm(pylint_analysis: Dict[str, Any]) -> str:
    """
    Format pylint analysis results into a human-readable report for LLM consumption.
    
    Args:
        pylint_analysis (Dict): Output from run_pylint_analysis()
        
    Returns:
        str: Formatted report text for LLM prompt
    """
    if not pylint_analysis.get("success"):
        return f"Static analysis failed: {pylint_analysis.get('error', 'Unknown error')}"
    
    report = f"""
PYLINT ANALYSIS REPORT
{'='*50}
Overall Score: {pylint_analysis.get('overall_score', 'N/A')}/10.0
Total Issues Found: {pylint_analysis.get('total_issues', 0)}

Issue Breakdown:
- Fatal Errors: {pylint_analysis.get('issue_types', {}).get('fatal', 0)}
- Regular Errors: {pylint_analysis.get('issue_types', {}).get('error', 0)}
- Warnings: {pylint_analysis.get('issue_types', {}).get('warning', 0)}
- Refactoring Suggestions: {pylint_analysis.get('issue_types', {}).get('refactor', 0)}
- Convention Violations: {pylint_analysis.get('issue_types', {}).get('convention', 0)}

Detailed Issues by File:
{'-'*50}
"""
    
    for filepath, file_data in pylint_analysis.get('files', {}).items():
        report += f"\n{filepath}:\n"
        report += f"  Issues: {file_data.get('issues_count', 0)}\n"
        
        # Show top 5 issues per file
        messages = file_data.get('messages', [])[:5]
        for msg in messages:
            report += f"  - Line {msg.get('line', '?')}: [{msg.get('type', 'unknown').upper()}] {msg.get('message', 'Unknown issue')} ({msg.get('symbol', '')})\n"
        
        if len(file_data.get('messages', [])) > 5:
            report += f"  ... and {len(file_data.get('messages', [])) - 5} more issues\n"
    
    report += f"\n{'='*50}\nRECOMMENDATION:\n"
    
    score = pylint_analysis.get('overall_score', 0)
    if score >= 8:
        report += "Code quality is good. Minor improvements possible.\n"
    elif score >= 6:
        report += "Code quality is acceptable. Several improvements needed.\n"
    elif score >= 4:
        report += "Code quality needs attention. Significant refactoring recommended.\n"
    else:
        report += "Code quality is poor. Major refactoring required.\n"
    
    return report

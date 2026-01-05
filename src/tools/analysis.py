"""
Static Code Analysis Tools - Pylint Integration
"""

import subprocess
import json
from typing import Dict, Any


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
            try:
                pylint_output = json.loads(result.stdout)
            except json.JSONDecodeError:
                pylint_output = []
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
        # Pylint: 10.0 is perfect, lower is worse
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

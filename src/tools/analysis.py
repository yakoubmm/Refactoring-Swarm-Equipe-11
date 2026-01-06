import subprocess
import sys
from typing import Dict

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

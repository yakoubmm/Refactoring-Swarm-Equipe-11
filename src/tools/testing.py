
import subprocess
import sys
from typing import Dict


def run_pytest(target_dir: str, timeout: int = 60) -> Dict[str, str]:
    """
    Run pytest on a target directory.

    Returns:
        {
            "success": bool,
            "output": str
        }
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", target_dir, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        output = result.stdout + result.stderr

        return {
            "success": result.returncode == 0,
            "output": output
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "pytest timed out"
        }

    except FileNotFoundError:
        return {
            "success": False,
            "output": "pytest not found. Install via: pip install pytest"
        }

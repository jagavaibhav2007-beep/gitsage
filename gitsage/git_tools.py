"""Git tools module: subprocess wrappers for git commands and diff security scanning."""

import re
import subprocess
from typing import List, Tuple

# Simple patterns to catch leaked tokens and hardcoded secrets
SECRET_PATTERNS = [
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API Key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Token"),
    (r"(?i)(api_key|secret|token|password)\s*=\s*['\"][^'\"]+['\"]", "Hardcoded Secret"),
]


def run_git(args: List[str]) -> Tuple[bool, str]:
    """Run any git command. Returns (success: bool, output_or_error: str)."""
    try:
        res = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if res.returncode == 0:
            return True, res.stdout.strip()
        return False, res.stderr.strip()
    except FileNotFoundError:
        return False, "Git is not installed or not found on system PATH."


def is_git_repo() -> bool:
    """Check if the current working directory is a git repository."""
    success, _ = run_git(["rev-parse", "--is-inside-work-tree"])
    return success


def get_staged_diff() -> str:
    """Get the diff of currently staged changes."""
    success, output = run_git(["diff", "--cached"])
    return output if success else ""


def get_staged_files() -> List[str]:
    """Get a list of staged file names."""
    success, output = run_git(["diff", "--cached", "--name-only"])
    if not success or not output:
        return []
    return output.splitlines()


def scan_for_secrets(diff_text: str, staged_files: List[str]) -> List[str]:
    """Scan staged files and diff content for accidental secret leaks."""
    warnings: List[str] = []

    # 1. Warn if sensitive files (.env, .pem, .key) are staged
    for filename in staged_files:
        if filename.startswith(".env") or filename.endswith((".pem", ".key")):
            warnings.append(f"Sensitive file staged: '{filename}'")

    # 2. Warn if newly added lines (+) in the diff match secret patterns
    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            for pattern, description in SECRET_PATTERNS:
                if re.search(pattern, line):
                    warnings.append(f"{description}: {line.strip()[:60]}...")
                    break

    return warnings


def commit_changes(message: str) -> Tuple[bool, str]:
    """Commit staged changes with the provided commit message."""
    return run_git(["commit", "-m", message])
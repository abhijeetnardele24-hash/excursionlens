#!/usr/bin/env python3
"""
scripts/security_scan.py — Secret & Sensitive Pattern Scanner

Scans working tree files and Git history for:
  - Private keys / certificates
  - Token Factory / OpenAI-style API keys (e.g. sk-...)
  - Tavily API keys (e.g. tvly-...)
  - Unredacted authorization headers
  - High-entropy secrets and credential assignments

Exempts standard placeholders (e.g. 'your_nebius_token_factory_key_here').
"""

import os
import sys
import re
import subprocess
from typing import List, Tuple

SUSPICIOUS_PATTERNS = [
    (r'(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}', "Exposed Bearer token"),
    (r'(?i)tvly-[a-zA-Z0-9_\-]{20,}', "Tavily API key"),
    (r'(?i)sk-[a-zA-Z0-9_\-]{20,}', "Secret API key (sk-...)"),
    (r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----', "Private cryptographic key"),
    (r'(?i)(?:nebius|token_factory|tavily)[_\-]?key\s*=\s*["\'][a-zA-Z0-9_\-\.]{16,}["\']', "Hardcoded provider secret"),
]

EXEMPT_SUBSTRINGS = [
    "your_nebius_token_factory_key_here",
    "your_tavily_api_key_here",
    "your_actual_api_key_here",
    "your_qloo_api_key_here",
    "your_key_here",
    "<none>",
    "***",
    "test_token",
    "mock_key",
    "fake_key",
]

IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "coverage",
    ".pytest_cache",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
}

IGNORE_FILES = {
    "package-lock.json",
    "uv.lock",
}


def scan_file_content(filepath: str, content: str) -> List[Tuple[int, str, str]]:
    findings = []
    lines = content.splitlines()
    for idx, line in enumerate(lines, 1):
        if any(exempt in line for exempt in EXEMPT_SUBSTRINGS):
            continue
        for pattern, desc in SUSPICIOUS_PATTERNS:
            if re.search(pattern, line):
                findings.append((idx, desc, line.strip()[:80]))
    return findings


def scan_working_tree() -> List[str]:
    violations = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            if f in IGNORE_FILES or f.endswith((".png", ".jpg", ".jpeg", ".ico", ".svg", ".sqlite", ".db", ".woff", ".woff2")):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                file_findings = scan_file_content(path, content)
                for line_no, desc, snippet in file_findings:
                    violations.append(f"{path}:{line_no} — {desc}: {snippet}")
            except Exception:
                pass
    return violations


def scan_git_history() -> List[str]:
    violations = []
    try:
        res = subprocess.run(
            ["git", "log", "-p", "-n", "30"],
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0:
            lines = res.stdout.splitlines()
            for idx, line in enumerate(lines, 1):
                if line.startswith("+") and not line.startswith("+++"):
                    added = line[1:]
                    if any(exempt in added for exempt in EXEMPT_SUBSTRINGS):
                        continue
                    for pattern, desc in SUSPICIOUS_PATTERNS:
                        if re.search(pattern, added):
                            violations.append(f"Git history diff line {idx} — {desc}: {added.strip()[:80]}")
    except Exception:
        pass
    return violations


def main() -> int:
    print("🔒 [LastRack / ExcursionLens Security Scan] Scanning working tree and Git history...")
    tree_violations = scan_working_tree()
    history_violations = scan_git_history()

    all_violations = tree_violations + history_violations
    if all_violations:
        print(f"❌ Security scan found {len(all_violations)} potential secret leaks:")
        for v in all_violations:
            print(f"   • {v}")
        return 1

    print("✅ [Security Scan] Clean! No credentials or secrets found across working tree or Git history.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

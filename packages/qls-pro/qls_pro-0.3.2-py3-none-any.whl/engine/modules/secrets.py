"""
SecretsScanner – detects leaked credentials and API keys.
"""

from pathlib import Path
import re
from typing import List, Dict, Any


class SecretsScanner:
    """
    Scan source files (.py, .js, .env, etc.) for hard-coded secrets.

    Parameters
    ----------
    first_hit_only : bool, default True
        If True, stop after the first secret type is found in a given file.
        If False, report every matching secret in that file.
    """

    name = "SecretsScanner"

    def __init__(self, first_hit_only: bool = True) -> None:
        self.first_hit_only = first_hit_only

    # ------------------------------------------------------------------
    # Regex patterns for common secrets
    # ------------------------------------------------------------------
    PATTERNS = {
        # 40-char AWS secret key
        "AWS Secret Key": re.compile(
            r"(?i)AWS_SECRET_ACCESS_KEY\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}"
        ),
        # 20-char AWS access-key ID
        "AWS Access Key": re.compile(r"AKIA[0-9A-Z]{16}"),
        # jwt_secret style (≥ 8 chars)
        "JWT Secret": re.compile(
            r"(?i)jwt[_-]?secret\s*[:=]\s*['\"][^'\"]{8,}"
        ),
        # Any PEM-formatted private-key block
        "Private Key Block": re.compile(
            r"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----[\s\S]*?-----END(?: [A-Z]+)? PRIVATE KEY-----",
            re.MULTILINE,
        ),
    }

    # ------------------------------------------------------------------
    def supported_types(self) -> List[str]:
        return ["file"]

    # ------------------------------------------------------------------
    def scan(self, target: Path) -> Dict[str, Any]:
        files = self._collect(target)
        leaks: List[Dict[str, str]] = []

        for fp in files:
            text = fp.read_text(errors="ignore")
            for label, regex in self.PATTERNS.items():
                for _ in regex.finditer(text):
                    leaks.append({"file": str(fp), "type": label})
                    if self.first_hit_only:
                        break
                if self.first_hit_only and leaks and leaks[-1]["file"] == str(fp):
                    # already recorded a leak for this file; skip remaining patterns
                    break

        return {
            "scanned_files": len(files),
            "secrets_found": len(leaks),
            "details": leaks or None,
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _collect(path: Path) -> List[Path]:
        """Gather files with interesting extensions."""
        if path.is_file():
            return [path]
        exts = {".py", ".js", ".ts", ".env", ".txt", ".json", ".yml"}
        return [p for p in path.rglob("*") if p.suffix.lower() in exts]
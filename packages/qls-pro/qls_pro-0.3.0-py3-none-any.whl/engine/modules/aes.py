"""
AESScanner – detects insecure AES usage (ECB mode, hard-coded key or IV).
"""

from pathlib import Path
import re
from typing import List, Dict, Any


class AESScanner:
    name = "AESScanner"

    # Regexes
    _ECB = re.compile(r"AES\.MODE_ECB")
    _HARD_KEY = re.compile(r"key\s*=\s*['\"][A-Za-z0-9+/=]{16,}['\"]")
    _HARD_IV = re.compile(r"(iv|IV)\s*=\s*['\"][A-Za-z0-9+/=]{8,}['\"]")

    def __init__(self, first_hit_only: bool = True) -> None:
        self.first_hit_only = first_hit_only

    # ------------------------------------------------------------------
    def supported_types(self) -> List[str]:
        return ["file"]

    # ------------------------------------------------------------------
    def scan(self, target: Path) -> Dict[str, Any]:
        files = self._gather(target)
        issues: List[Dict[str, str]] = []

        for fp in files:
            text = fp.read_text(errors="ignore")

            # pattern checks
            if self._ECB.search(text):
                issues.append({"file": str(fp), "issue": "AES ECB mode used"})
                if self.first_hit_only:
                    continue

            if self._HARD_KEY.search(text):
                issues.append({"file": str(fp), "issue": "Hard-coded AES key"})
                if self.first_hit_only:
                    continue

            if self._HARD_IV.search(text):
                issues.append({"file": str(fp), "issue": "Hard-coded IV"})
                # no need for continue here; we've reached end of patterns

        return {
            "scanned_files": len(files),
            "issues_found": len(issues),
            "details": issues or None,
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _gather(path: Path) -> List[Path]:
        if path.is_file():
            return [path]
        return [
            p
            for p in path.rglob("*")
            if p.suffix.lower() in {".py", ".js", ".ts"}
        ]
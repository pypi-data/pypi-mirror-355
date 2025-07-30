"""JWTScanner – detects hard‑coded JWT tokens & weak algorithms."""

from pathlib import Path
from typing import List, Dict, Any
import re, base64, json, datetime


class JWTScanner:
    name = "JWTScanner"

    # base64url token matcher: header.payload.signature (min 10 chars each seg)
    _JWT_RE = re.compile(r"ey[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}")


    WEAK_ALGS = {"none", "HS256", "HS384", "HS512"}

    # ----------------------------------------------------------
    def supported_types(self) -> List[str]:
        return ["file"]

    # ----------------------------------------------------------
    def scan(self, target: Path) -> Dict[str, Any]:
        files = self._collect(target)
        issues: List[Dict[str, str]] = []

        for fp in files:
            text = fp.read_text(errors="ignore")
            for m in self._JWT_RE.finditer(text):
                token = m.group(0)
                alg, exp_flag = self._analyze_jwt(token)
                if alg in self.WEAK_ALGS or exp_flag:
                    issues.append(
                        {
                            "file": str(fp),
                            "alg": alg,
                            "issue": (
                                "alg:none" if alg == "none" else (
                                    "symmetric alg (HS*)" if alg.startswith("HS") else "weak JWT"
                                )
                            ),
                        }
                    )
        return {
            "scanned_files": len(files),
            "jwt_issues": len(issues),
            "details": issues or None,
        }

    # ----------------------------------------------------------
    def _analyze_jwt(self, token: str):
        """Return (alg, exp_missing_or_far_future)"""
        header_b64 = token.split(".")[0]
        pad = "=" * (-len(header_b64) % 4)
        try:
            header_json = base64.urlsafe_b64decode(header_b64 + pad).decode()
            header = json.loads(header_json)
            alg = header.get("alg", "unknown")
        except Exception:
            alg = "unknown"
        # simplistic exp check (not used yet, but placeholder)
        return alg, False

    # ----------------------------------------------------------
    @staticmethod
    def _collect(path: Path) -> List[Path]:
        if path.is_file():
            return [path]
        exts = {".py", ".js", ".ts", ".env", ".txt", ".json", ".yml"}
        return [p for p in path.rglob("*") if p.suffix.lower() in exts]



from .tls import TLSScanner
from .aes import AESScanner
from .secrets import SecretsScanner

__all__ = [
    "TLSScanner",
    "AESScanner",
    "SecretsScanner",
]
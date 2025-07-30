"""
engine/remediator.py
--------------------
Rotate hard-coded AWS credentials that QLS flagged,
update the source .env file, and (optionally) disable
the leaked key in AWS IAM.

Usage (wired via qls CLI):
    qls rotate-keys reports/qls_20250613T0105.json          # dry-run
    qls rotate-keys reports/...json --execute --revoke      # do it
"""

from __future__ import annotations
from pathlib import Path
import json, re, os, boto3
from rich import print as rprint

AWS_KEY_RE = re.compile(r"AKIA[0-9A-Z]{16}")
AWS_SECRET_RE = re.compile(r"(?i)AWS_SECRET_ACCESS_KEY\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}")

class KeyRotator:
    def __init__(self, execute: bool = False, revoke: bool = False):
        self.execute = execute
        self.revoke = revoke
        self.iam = boto3.client("iam") if execute else None

    # ------------------------------------------------------------------
    def rotate_from_report(self, report_path: Path) -> None:
        report = json.loads(report_path.read_text())
        leaks = report["modules"].get("SecretsScanner", {}).get("details", [])
        if not leaks:
            rprint("[yellow]No secrets to rotate in this report.[/yellow]")
            return

        for leak in leaks:
            if leak["type"] != "AWS Secret Key":
                continue

            file_path = Path(leak["file"])
            if not file_path.exists():
                rprint(f"[red]File not found:[/red] {file_path}")
                continue

            text = file_path.read_text()
            m_id = AWS_KEY_RE.search(text)
            m_sec = AWS_SECRET_RE.search(text)
            if not (m_id and m_sec):
                rprint(f"[yellow]AWS key strings not found in {file_path}[/yellow]")
                continue

            old_id = m_id.group(0)
            rprint(f"\n[cyan]Rotating leaked AWS key in[/cyan] {file_path} → {old_id[:4]}…")

            if self.execute:
                new_id, new_sec = self._create_access_key()
                text = text.replace(old_id, new_id).replace(m_sec.group(0).split("=",1)[1].strip(), new_sec)
                file_path.write_text(text)
                rprint(f"  ✅ Wrote new key {new_id[:4]}… to {file_path}")

                if self.revoke:
                    self._revoke_key(old_id)
                    rprint("  🗑️  Old key disabled in IAM")
            else:
                rprint("  [yellow]Dry-run:[/yellow] would create new key and patch file.")

    # ------------------------------------------------------------------
    def _create_access_key(self) -> tuple[str, str]:
        resp = self.iam.create_access_key()
        return resp["AccessKey"]["AccessKeyId"], resp["AccessKey"]["SecretAccessKey"]

    def _revoke_key(self, key_id: str) -> None:
        self.iam.update_access_key(AccessKeyId=key_id, Status="Inactive")
"""Pretty console output + JSON persistence for QLS."""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

from rich import print as rprint
from rich import print_json
from rich.panel import Panel

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)


class Reporter:
    # ---------------------------------------------------------- #
    @staticmethod
    def pretty_print(result: dict) -> None:
        """Nicely formatted console output using Rich."""
        header = f"[bold cyan]QLS Report – {result['target']}[/bold cyan]"
        rprint(Panel.fit(header))
        print_json(data=result)

    # ---------------------------------------------------------- #
    @staticmethod
    def save_json(
        result: dict,
        *,
        path: Path | None = None,
        path_override: Path | None = None,
    ) -> Path:
        """
        Persist scan result as UTF-8 JSON.

        Parameters
        ----------
        result : dict
            The scan result.
        path : Path, optional
            Custom path to write. If omitted, auto-generates a timestamped name.
        path_override : Path, optional
            If provided, overrides `path` entirely – used by qls.py to save a
            deterministic `qls_last.json` for follow-up rotation commands.
        """
        if path_override is not None:
            path = path_override

        if path is None:
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            path = REPORT_DIR / f"qls_{ts}.json"

        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        rprint(f"[green]JSON report saved to {path}[/green]")
        return path
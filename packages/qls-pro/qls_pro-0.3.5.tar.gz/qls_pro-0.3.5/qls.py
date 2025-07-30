"""qls.py – command-line entry point for QLS."""

import sys, argparse
from pathlib import Path
from rich import print as rprint

from engine.engine import QuantivirusEngine
from engine.reporter import Reporter
from engine.modules import TLSScanner, AESScanner, SecretsScanner, JWTScanner
from engine.modules.hybrid_tls import HybridTLSTester
# remediator imported lazily

# -----------------------------------------------------------------
# Helper to assemble the engine with all available modules
# -----------------------------------------------------------------
def build_engine(first_hit_only: bool = True) -> QuantivirusEngine:
    eng = QuantivirusEngine()
    eng.register(TLSScanner())
    eng.register(AESScanner(first_hit_only=first_hit_only))
    eng.register(SecretsScanner(first_hit_only=first_hit_only))
    eng.register(JWTScanner())
    eng.register(HybridTLSTester())
    return eng


# -----------------------------------------------------------------
# CLI definitions
# -----------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="qls",
        description="QLS – Quantum Liability Scanner (Quantivirus Engine)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- TLS scan ------------------------------------------------
    tls_cmd = sub.add_parser("scan-tls", help="Scan a domain for TLS weaknesses")
    tls_cmd.add_argument("domain", help="domain (e.g. example.com)")
    tls_cmd.add_argument("--report", choices=["md", "pdf"],
                         help="Generate Markdown or PDF report file")

    # --- Code / repo scan ---------------------------------------
    code_cmd = sub.add_parser(
        "scan-code",
        help="Scan a file or directory for AES misuse, leaked secrets, and insecure JWTs",
    )
    code_cmd.add_argument("path", help="File or folder path to scan")
    code_cmd.add_argument("--all", action="store_true",
                          help="Report every secret/key/JWT found (not just the first per file)")
    code_cmd.add_argument("--report", choices=["md", "pdf"],
                          help="Generate Markdown or PDF report file")
    code_cmd.add_argument("--strict", action="store_true",
                          help="Exit code 1 if HIGH quantum risk or secret leak found")
    code_cmd.add_argument("--auto-rotate", action="store_true",
                          help="Automatically rotate leaked AWS keys after the scan")

    # --- Key rotation -------------------------------------------
    rot_cmd = sub.add_parser(
        "rotate-keys",
        help="Rotate leaked AWS keys listed in a QLS JSON report",
    )
    rot_cmd.add_argument("report", help="Path to JSON report from qls scan")
    rot_cmd.add_argument("--execute", action="store_true",
                         help="Actually create new keys and patch files (default = dry-run)")
    rot_cmd.add_argument("--revoke", action="store_true",
                         help="Disable the leaked AWS key after rotation")

    args = parser.parse_args()

    # ---------------------------- Route --------------------------
    if args.command == "rotate-keys":
        from engine.remediator import KeyRotator
        rot = KeyRotator(execute=args.execute, revoke=args.revoke)
        rot.rotate_from_report(Path(args.report))
        return

    # Build engine for scan commands
    engine = build_engine(first_hit_only=not getattr(args, "all", False))

    if args.command == "scan-tls":
        result = engine.scan(target=args.domain, scan_type="tls")
    elif args.command == "scan-code":
        result = engine.scan(target=Path(args.path), scan_type="file")
    else:
        parser.error("Unknown command")

    # ------------------- Inject fix-hints ------------------------
    from engine import recommend
    for mod in result["modules"].values():
        if isinstance(mod, dict) and mod.get("details"):
            for item in mod["details"]:
                label = item.get("issue") or item.get("type")
                item["fix"] = recommend.suggest(label)
    
    from engine import compliance
    item["controls"] = compliance.map_issue(label)


    # ---------------- AWS leak follow-up -------------------------
    leaks   = result["modules"].get("SecretsScanner", {}).get("details", [])
    aws_leaks = [l for l in leaks if l.get("type") == "AWS Secret Key"]
    if aws_leaks:
        last_report = Path("reports") / "qls_last.json"
        Reporter.save_json(result, path_override=last_report)

        if getattr(args, "auto_rotate", False):
            rprint("[cyan]Auto-rotating leaked AWS keys…[/cyan]")
            from engine.remediator import KeyRotator
            rot = KeyRotator(execute=True, revoke=True)
            rot.rotate_from_report(last_report)
        else:
            rprint(
                f"[yellow]❗ {len(aws_leaks)} AWS key(s) leaked.[/yellow] "
                f"Run [bold]qls rotate-keys {last_report} --execute --revoke[/bold] "
                "to rotate them now, or add [bold]--auto-rotate[/bold] to automate."
            )

    # -------------------- Strict-mode exit -----------------------
    exit_bad = False
    if getattr(args, "strict", False):
        if result["modules"].get("TLSScanner", {}).get("quantum_risk") == "HIGH":
            exit_bad = True
        if result["modules"].get("SecretsScanner", {}).get("secrets_found", 0) > 0:
            exit_bad = True
    if exit_bad:
        rprint("[red]Strict mode: blocking with exit code 1[/red]")
        Reporter.pretty_print(result)
        Reporter.save_json(result)
        sys.exit(1)

    # ----------------------- Output ------------------------------
    Reporter.pretty_print(result)
    Reporter.save_json(result)

    if getattr(args, "report", None):
        from engine.report_renderer import render_markdown, render_pdf
        md_path = render_markdown(result, Path("reports") / "qls_report.md")
        if args.report == "pdf":
            render_pdf(md_path)


if __name__ == "__main__":
    main()
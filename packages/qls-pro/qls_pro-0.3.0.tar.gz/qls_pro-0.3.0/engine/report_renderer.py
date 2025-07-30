"""
engine/report_renderer.py
-------------------------
Builds a branded Markdown report (and optional PDF) from a QLS scan
result dictionary.

• Always writes UTF-8 Markdown.
• Converts Markdown ➜ HTML ➜ PDF with WeasyPrint if available.
"""

from pathlib import Path
import datetime, textwrap
from rich import print as rprint
import markdown

LOGO_MD = "### **QLS – Quantum Liability Scanner**\n"

# ------------------------------ helpers -----------------------------

def _header(target: str) -> str:
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"{LOGO_MD}\n"
        f"**Scan Target:** `{target}`  \n"
        f"**Generated:** {ts}\n\n---\n"
    )

def _md_bullet_list(rows):
    out = []
    for row in rows:
        issue = row.get("issue") or row.get("type", "—")
        fix   = f"  💡 **Fix:** {row.get('fix')}" if row.get("fix") else ""
        out.append(f"* **{issue}** — `{row['file']}`{fix}")
    return "\n".join(out) + "\n\n"

# --------------------------- main builders --------------------------

def render_markdown(result: dict, out_path: Path) -> Path:
    """Write a Markdown file and return its Path."""
    md = _header(result["target"])
    mods = result["modules"]

    # TLS section
    if "TLSScanner" in mods:
        tls = mods["TLSScanner"]
        md += "### TLS Findings\n\n"
        if "error" in tls:
            md += f"> ⚠️ {tls['error']}\n\n"
        else:
            md += textwrap.dedent(
                f"""
                | Field | Value |
                |-------|-------|
                | **Issuer** | {tls['issuer']} |
                | **Subject** | {tls['subject']} |
                | **Public Key** | {tls['key_type']} {tls['key_size']}-bit |
                | **Signature** | {tls['signature_algo']} |
                | **Classical Issues** | {tls['classical_issues'] or '—'} |
                | **Quantum Risk** | **{tls['quantum_risk']}** |
                | **Quantum Breach ETA** | {tls['years_to_break']} |
                """
            )
        md += "\n\n---\n"
        
    # ---- Hybrid-TLS badge --------------------------------------
    if "HybridTLSTester" in mods:
        h = mods["HybridTLSTester"]
        status = "✅ Yes" if h.get("hybrid_supported") else "❌ No"
        md += "### Post-Quantum Hybrid Support\n\n"
        md += f"* **Supported:** {status}\n"
        md += f"* **Negotiated Group:** `{h.get('negotiated_group', 'unknown')}`\n\n---\n"
        
    # Code-scanner sections
    if "AESScanner" in mods:
        md += "### AES Issues\n\n" + _md_bullet_list(mods["AESScanner"]["details"] or [])
    if "SecretsScanner" in mods:
        md += "### Secret / Key Leaks\n\n" + _md_bullet_list(mods["SecretsScanner"]["details"] or [])
    if "JWTScanner" in mods:
        md += "### Insecure JWTs\n\n" + _md_bullet_list(mods["JWTScanner"]["details"] or [])

    out_path.write_text(md, encoding="utf-8")
    rprint(f"[green]Markdown report saved → {out_path}[/green]")
    return out_path


# --------------------------- PDF helper -----------------------------

_CSS = """
h1,h2,h3,h4{font-family:Arial,Helvetica,sans-serif;color:#0a4b78;margin:12px 0;}
table{border-collapse:collapse;width:100%;font-family:Arial,Helvetica,sans-serif;}
td,th{border:1px solid #ddd;padding:6px 8px;}
tr:nth-child(even){background:#f8f8f8;}
"""

def render_pdf(md_path: Path) -> Path:
    """Convert Markdown to PDF using WeasyPrint (if installed)."""
    try:
        from weasyprint import HTML, CSS as WP_CSS
    except ImportError:
        rprint("[yellow]WeasyPrint not installed; skipping PDF.[/yellow]")
        return md_path

    html_text = markdown.markdown(
        md_path.read_text(encoding="utf-8"),
        extensions=["tables"],
    )
    pdf_path = md_path.with_suffix(".pdf")
    HTML(string=html_text, base_url=".").write_pdf(pdf_path, stylesheets=[WP_CSS(string=_CSS)])

    if pdf_path.exists():
        rprint(f"[green]PDF report saved → {pdf_path}[/green]")
    else:
        rprint("[red]PDF generation failed.[/red]")
    return pdf_path
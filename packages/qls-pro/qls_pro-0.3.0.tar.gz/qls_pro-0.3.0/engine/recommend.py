"""
engine/recommend.py
-------------------
Maps each issue string to a short remediation hint.
"""

FIXES = {
    "AES ECB mode used":
        "Switch to AES-GCM or AES-CBC with random IVs.",
    "Hard-coded AES key":
        "Load keys from environment variables or a secrets manager.",
    "Hard-coded IV":
        "Generate IVs with os.urandom() every encryption operation.",
    "AWS Secret Key":
        "Rotate the key in AWS IAM and delete the leaked credential.",
    "AWS Access Key":
        "Deactivate leaked access key and create a new one.",
    "JWT Secret":
        "Move secret to env var or vault; rotate all live tokens.",
    "alg:none":
        "Disallow `alg:none`; use RS256/ES256 JWTs and verify algorithm.",
}

def suggest(issue: str) -> str:
    return FIXES.get(issue, "Refer to crypto-hardening guidelines.")
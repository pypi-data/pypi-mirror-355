"""
HybridTLSTester – checks if a server negotiates
a Kyber or other PQ group via OpenSSL 3.2+.
"""

import subprocess, re, shutil
from typing import List, Dict, Any

PQ_GROUPS = ("kyber768", "p256_kyber768", "kyber512", "dilithium3")

class HybridTLSTester:
    name = "HybridTLSTester"

    def supported_types(self) -> List[str]:
        return ["tls"]

    def scan(self, target: str) -> Dict[str, Any]:
        if not shutil.which("openssl"):
            return {"error": "OpenSSL CLI not found"}

        cmd = [
            "openssl", "s_client",
            "-groups", ":".join(PQ_GROUPS),
            "-connect", f"{target}:443",
            "-tls1_3",        # force TLS 1.3
            "-brief", "-servername", target
        ]
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=10, text=True)
        except subprocess.CalledProcessError as e:
            return {"error": f"OpenSSL failed ({e.returncode})"}
        except subprocess.TimeoutExpired:
            return {"error": "Handshake timed out"}

        match = re.search(r"Shared group: (\S+)", out)
        group  = match.group(1) if match else "unknown"
        hybrid = any(pg in group.lower() for pg in PQ_GROUPS)

        return {
            "hybrid_supported": hybrid,
            "negotiated_group": group,
        }
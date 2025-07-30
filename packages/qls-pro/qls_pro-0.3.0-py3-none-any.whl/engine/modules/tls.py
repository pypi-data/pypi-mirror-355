from typing import Dict, Any, List
import ssl, socket
from cryptography import x509
from cryptography.hazmat.backends import default_backend

class TLSScanner:
    name = "TLSScanner"

    # --- lookup: key-size ➜ quantum-break ETA --------------
    BREAK_ETAS = {
        256:  "2032 ±3 yrs",   # P-256 ECC
        2048: "2032 ±3 yrs",
        384:  "2034 ±3 yrs",   # P-384
        3072: "2034 ±3 yrs",
        4096: "2036 ±4 yrs",
        8192: ">2038",
    }

    # ------------------------------------------------------------------
    def supported_types(self) -> List[str]:
        return ["tls"]

    # ------------------------------------------------------------------
    def scan(self, target: str) -> Dict[str, Any]:
        """Scan TLS certificate of a domain and assess quantum/classical risk."""
        data: Dict[str, Any] = {}
        try:
            with socket.create_connection((target, 443), timeout=5) as sock:
                ctx = ssl.create_default_context()
                with ctx.wrap_socket(sock, server_hostname=target) as ssock:
                    der_cert = ssock.getpeercert(binary_form=True)
            cert = x509.load_der_x509_certificate(der_cert, default_backend())
        except Exception as exc:
            return {"error": f"TLS handshake failed: {exc}"}

        # --- basic fields -------------------------------------------------
        pubkey = cert.public_key()
        key_type = type(pubkey).__name__
        key_size = getattr(pubkey, "key_size", "unknown")
        sig_algo = cert.signature_algorithm_oid._name

        # --- classical issues --------------------------------------------
        classical_issues = []
        if key_type.startswith("RSA") and key_size != "unknown" and key_size < 2048:
            classical_issues.append("RSA key < 2048 bits (weak)")
        if "sha1" in sig_algo.lower() or "md5" in sig_algo.lower():
            classical_issues.append("Weak signature hash (SHA1/MD5)")

        # --- quantum risk heuristic --------------------------------------
        if key_type == "RSAPublicKey":
            qrisk = "HIGH" if key_size < 4096 else "MEDIUM"
        elif key_type == "ECPublicKey":
            qrisk = "HIGH"
        else:
            qrisk = "UNKNOWN"

        # --- years-to-break estimate -------------------------------------
        eta = self.BREAK_ETAS.get(key_size, ">2038")

        # --- assemble result ---------------------------------------------
        data.update(
            {
                "issuer": cert.issuer.rfc4514_string(),
                "subject": cert.subject.rfc4514_string(),
                "valid_from": cert.not_valid_before_utc.isoformat(),
                "valid_to": cert.not_valid_after_utc.isoformat(),
                "key_type": key_type,
                "key_size": key_size,
                "signature_algo": sig_algo,
                "classical_issues": classical_issues or None,
                "quantum_risk": qrisk,
                "years_to_break": eta,
            }
        )
        return data
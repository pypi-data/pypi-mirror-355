MAPPINGS = {
    "AWS Secret Key": ["SOC2 CC6.3", "ISO 27001 A.8.2.2"],
    "RSA key < 2048 bits": ["SOC2 CC7.1"],
    "Weak signature hash": ["SOC2 CC7.1"],
    "alg:none": ["SOC2 CC7.2"],
    "AES ECB mode used": ["SOC2 CC7.1"],
}
def map_issue(issue: str) -> list[str]:
    return MAPPINGS.get(issue, [])
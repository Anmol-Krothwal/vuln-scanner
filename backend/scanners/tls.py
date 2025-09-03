from urllib.parse import urlparse

def tls_summary(url: str):
    scheme = urlparse(url).scheme
    findings = []
    if scheme != "https":
        findings.append({
            "severity": "High",
            "title": "No HTTPS",
            "detail": "Target is not using HTTPS."
        })
    return {"category": "TLS", "findings": findings}

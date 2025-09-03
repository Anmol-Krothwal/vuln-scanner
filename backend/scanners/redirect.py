from urllib.parse import urlparse, parse_qs

RISKY_PARAMS = ["next", "redirect", "url", "dest", "target", "return", "returnUrl"]

def check_open_redirect(url: str):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    findings = []
    for p in RISKY_PARAMS:
        if p in qs:
            findings.append({
                "severity": "Medium",
                "title": "Possible open‑redirect parameter",
                "detail": f"Query parameter '{p}' present. Ensure server validates allowed domains/paths."
            })
    return {"category": "Open Redirect (heuristic)", "findings": findings}

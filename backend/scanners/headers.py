def check_headers(resp):
    h = resp.headers or {}
    findings = []

    required = [
        "content-security-policy",
        "strict-transport-security",
        "x-frame-options",
        "x-content-type-options",
        "referrer-policy",
        "permissions-policy"
    ]
    for hdr in required:
        if hdr not in h:
            findings.append({
                "severity": "Medium",
                "title": f"Missing {hdr}",
                "detail": f"Recommended to set {hdr}."
            })

    xcto = h.get("x-content-type-options", "")
    if xcto and "nosniff" not in xcto.lower():
        findings.append({
            "severity": "Low",
            "title": "X-Content-Type-Options not 'nosniff'",
            "detail": f"Value seen: {xcto}"
        })

    return {"category": "Security Headers", "findings": findings}

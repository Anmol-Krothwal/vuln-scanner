def check_cookies(resp):
    set_cookies = resp.headers.get("set-cookie", None)
    # requests may join multiple set-cookie in a single string; handle both cases
    if not set_cookies:
        cookies = []
    elif isinstance(set_cookies, list):
        cookies = set_cookies
    else:
        # split naive; good enough for demo
        cookies = [c.strip() for c in set_cookies.split(",") if "=" in c]

    findings = []
    for c in cookies:
        low = c.lower()
        if "secure" not in low:
            findings.append({"severity": "Medium", "title": "Cookie missing Secure", "detail": c})
        if "httponly" not in low:
            findings.append({"severity": "Medium", "title": "Cookie missing HttpOnly", "detail": c})
        if "samesite" not in low:
            findings.append({"severity": "Low", "title": "Cookie missing SameSite", "detail": c})

    return {"category": "Cookies", "findings": findings}

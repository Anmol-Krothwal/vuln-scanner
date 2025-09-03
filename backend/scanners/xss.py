import requests
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

def add_probe(url: str, param="q", payload="<xss-test>"):
    parts = list(urlparse(url))
    qs = dict(parse_qsl(parts[4], keep_blank_values=True))
    if param not in qs:
        qs[param] = payload
    parts[4] = urlencode(qs, doseq=True)
    return urlunparse(parts)

def check_basic_xss(url: str):
    test_url = add_probe(url)
    try:
        r = requests.get(test_url, timeout=8, allow_redirects=True)
        reflected = isinstance(r.text, str) and "<xss-test>" in r.text
        return {
            "category": "XSS (Reflected) – quick probe",
            "findings": [{
                "severity": "High",
                "title": "Potential reflected XSS",
                "detail": "Payload '<xss-test>' was reflected in response."
            }] if reflected else []
        }
    except Exception:
        return {
            "category": "XSS (Reflected) – quick probe",
            "findings": [{
                "severity": "Low",
                "title": "Probe inconclusive",
                "detail": "Target did not respond or blocked the probe."
            }]
        }

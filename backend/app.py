from flask import Flask, request, jsonify, make_response
import json

# Scanner modules
from scanners.headers import check_headers
from scanners.cookies import check_cookies
from scanners.xss import check_basic_xss
from scanners.redirect import check_open_redirect
from scanners.tls import tls_summary
from scanners.utils import fetch_url, risk_score

app = Flask(__name__)
app.url_map.strict_slashes = False  # avoid /scan <-> /scan/ redirects

# Allowed frontend origins (adjust if you use different host/port)
ALLOWED_ORIGINS = {
    "http://127.0.0.1:5500",
    "http://localhost:5500",
}

# ---- CORS helpers ----
def _corsify(resp):
    """Attach CORS headers to a response without causing redirects."""
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp

@app.after_request
def add_cors_headers(resp):
    # Add CORS headers to every response
    return _corsify(resp)

# ---- Health ----
@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

# ---- Main scan endpoint ----
@app.route("/scan", methods=["POST", "OPTIONS"])
def scan():
    # Handle preflight cleanly (should be rare if frontend uses text/plain)
    if request.method == "OPTIONS":
        return _corsify(make_response("", 204))

    # Accept JSON or text/plain bodies
    data = request.get_json(silent=True)
    if data is None:
        try:
            raw = request.get_data(as_text=True) or ""
            data = json.loads(raw) if raw else {}
        except Exception:
            data = {}

    url = (data.get("url") or "").strip()

    # Basic validation
    if not url:
        return jsonify({"error": "Missing 'url'"}), 400
    if not (url.startswith("http://") or url.startswith("https://")):
        return jsonify({"error": "URL must start with http:// or https://"}), 400

    # Fetch target (passive)
    resp, error = fetch_url(url)
    if error:
        return jsonify({"error": error}), 502

    # Run checks
    results = [
        check_headers(resp),
        check_cookies(resp),
        tls_summary(url),
        check_open_redirect(url),
        check_basic_xss(url),
    ]

    # Score & summarize
    all_findings = []
    for r in results:
        for f in r.get("findings", []):
            f["category"] = r.get("category", "")
            all_findings.append(f)

    payload = {
        "target": url,
        "score": risk_score(all_findings),
        "summary": {
            "high":   sum(1 for f in all_findings if f.get("severity") == "High"),
            "medium": sum(1 for f in all_findings if f.get("severity") == "Medium"),
            "low":    sum(1 for f in all_findings if f.get("severity") == "Low"),
        },
        "results": results
    }
    return jsonify(payload), 200

# ---- DEBUG: outbound egress check ----
@app.get("/debug/egress")
def debug_egress():
    import time, requests
    test_urls = [
        "https://httpbin.org/get",
        "https://example.com",
        "http://neverssl.com/"
    ]
    out = []
    for u in test_urls:
        t0 = time.time()
        try:
            r = requests.get(u, timeout=6)
            out.append({"url": u, "status": r.status_code, "ms": int((time.time()-t0)*1000)})
        except Exception as e:
            out.append({"url": u, "error": str(e), "ms": int((time.time()-t0)*1000)})
    return jsonify({"ok": True, "tests": out}), 200

# ---- DEBUG: local mock page (lets you demo without internet) ----
@app.get("/debug/mock")
def debug_mock():
    html = (
        "<!doctype html><html><body>"
        "<h1>Mock Page</h1>"
        "<p>Hello, this is a mock page served by the scanner backend.</p>"
        "<div><xss-test></xss-test></div>"
        "</body></html>"
    )
    resp = make_response(html, 200)
    # Deliberately weak cookie to trigger cookie findings
    resp.headers["Set-Cookie"] = "session=abc123; Path=/"
    # Intentionally missing security headers (so header checks flag them)
    return resp

if __name__ == "__main__":
    # Bind to 127.0.0.1 to avoid localhost/IPv6 redirect quirks
    app.run(host="127.0.0.1", port=8000)

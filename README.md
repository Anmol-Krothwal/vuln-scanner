# Web Vulnerability Scanner (Lite)

A fast, **web-based** passive scanner that checks:
- Security headers (CSP, HSTS, X-Frame-Options, Referrer-Policy, etc.)
- Cookie flags (Secure, HttpOnly, SameSite)
- TLS usage (HTTPS)
- Open-redirect **heuristics** (`next`, `redirect`, `returnUrl`, ...)
- Light **reflected XSS** probe on `q` parameter (`<xss-test>`) – **non-destructive**

> ⚠️ For educational use. Only scan systems you own or have permission to test.

## Stack
- Backend: Python **Flask**
- Frontend: Vanilla HTML/JS/CSS

## Quick Start
```bash
# 1) Backend
cd backend
python -m venv venv && venv\Scripts\activate   # on Windows
pip install -r ../requirements.txt
python app.py

# 2) Frontend
# Open frontend/index.html directly (or use Live Server / `python -m http.server` in /frontend)

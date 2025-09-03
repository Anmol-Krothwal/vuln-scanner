import os
import requests

DEFAULT_HEADERS = {
    "User-Agent": "VulnScannerLite/1.0 (+github.com/yourhandle)"
}

# Tunable timeouts
CONNECT_TIMEOUT = int(os.getenv("SCANNER_CONNECT_TIMEOUT", "6"))
READ_TIMEOUT    = int(os.getenv("SCANNER_READ_TIMEOUT", "12"))

# Optional corporate proxy support (set env vars if needed)
PROXIES = {
    "http":  os.getenv("HTTP_PROXY")  or os.getenv("http_proxy"),
    "https": os.getenv("HTTPS_PROXY") or os.getenv("https_proxy"),
}
PROXIES = {k: v for k, v in PROXIES.items() if v} or None

# Optional TLS verification skip (diagnostic only)
VERIFY_TLS = os.getenv("UNSAFE_SKIP_TLS_VERIFY", "0") != "1"

def fetch_url(url: str):
    try:
        resp = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            allow_redirects=True,
            proxies=PROXIES,
            verify=VERIFY_TLS,
        )
        resp.headers = {k.lower(): v for k, v in resp.headers.items()}
        return resp, None

    except requests.exceptions.Timeout:
        # Fallback: try a quick HEAD to confirm reachability, then a longer GET
        try:
            requests.head(
                url, headers=DEFAULT_HEADERS, timeout=5,
                allow_redirects=True, proxies=PROXIES, verify=VERIFY_TLS
            )
            resp = requests.get(
                url,
                headers=DEFAULT_HEADERS,
                timeout=(10, 20),     # longer on retry
                allow_redirects=True,
                proxies=PROXIES,
                verify=VERIFY_TLS,
                stream=True,          # reduce memory while reading
            )
            # Touch content lightly to ensure response is actually readable
            _ = next(resp.iter_content(chunk_size=1024), b"")
            resp.headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp, None
        except requests.exceptions.Timeout:
            return None, "Request to target timed out."
        except Exception as e:
            return None, f"Fetch error after HEAD: {e}"

    except requests.exceptions.SSLError:
        return None, "TLS/SSL error while connecting."
    except requests.exceptions.ConnectionError as e:
        return None, f"Connection error: {e}"
    except Exception as e:
        return None, f"Fetch error: {e}"

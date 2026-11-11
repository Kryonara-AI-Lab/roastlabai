# Sentinel Security Journal

## 2026-08-13 - Dynamic Session Keys & Blueprint Header Injection
**Vulnerability:** The Flask application used a static, hardcoded session `SECRET_KEY` in `app/__init__.py`, exposing it to cryptographic session tampering. Additionally, response headers lacked critical security configurations (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`), leaving the site susceptible to clickjacking and MIME-type sniffing.
**Learning:** Hardcoded keys are easy to commit and leak, especially when templates or rapid prototypes are cloned. Furthermore, standard Flask Blueprints do not automatically apply security headers unless specifically configured via lifecycle hooks.
**Prevention:** Always leverage environment lookup coupled with a high-entropy fallback using `secrets.token_hex(32)`. Ensure all responses run through an `@after_request` filter to systematically inject security headers.

## 2025-08-08 - Secure Session Configuration and Global Security Headers
**Vulnerability:**
1. Hardcoded development `SECRET_KEY` value in `app/__init__.py` which can expose application sessions to cryptographic tampering or hijacking if deployed to production without manual updates.
2. Missing critical HTTP security headers (`X-Frame-Options`, `X-Content-Type-Options`, and `Referrer-Policy`) globally which can expose the application to clickjacking, MIME-sniffing, and referrer leakages.

**Learning:**
1. Default templates or starter apps often come with placeholder secrets. When developers fail to replace these, session state can be cloned or manipulated. A secure fallback of generating a dynamic random key (like `secrets.token_hex(32)`) ensures safe operation even when the environment configuration is missing.
2. Security headers are easily forgotten during fast-paced feature development. Implementing them globally via a Blueprint or Flask Application `@after_request` filter ensures that every new page, route, or endpoint is protected by default.

**Prevention:**
1. Always resolve session security keys dynamically using environment checks combined with secure runtime fallback generators (`os.environ.get('SECRET_KEY') or secrets.token_hex(32)`).
2. Utilize global response filters/hooks to automatically append defensive headers to all requests without relying on route-by-route manual specification.

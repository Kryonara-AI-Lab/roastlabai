## 2026-08-06 - Securing Flask Session Keys and Enforcing Security Headers

**Vulnerability:** A hardcoded Flask session `SECRET_KEY` was found in `app/__init__.py`. Flask uses this key to cryptographically sign session cookies. A hardcoded secret allows anyone to decode and forge session cookies, which can bypass authentication entirely. Additionally, HTTP security headers (`X-Frame-Options`, `X-Content-Type-Options`, and `Referrer-Policy`) were missing, exposing the application to clickjacking, MIME sniffing, and referrer leaks.

**Learning:** The secret key was defined as a literal string `roastlab_secret_key_change_this_immediately` for ease of local development, but committed to version control. This is a common security pitfall during prototyping. Security headers were omitted during the initial setup of the blueprint routes.

**Prevention:** Always load session secret keys dynamically from environment variables (`os.environ`) with a cryptographically secure random backup fallback (e.g., `secrets.token_hex(32)`) in production environments. Enforce critical HTTP security headers globally on all blueprint responses via a global filter hook like Flask's `@bp.after_request`.

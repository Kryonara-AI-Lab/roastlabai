# Sentinel Security Journal

This journal records critical security learnings and unique codebase vulnerability insights encountered during our defensive audits.

## 2026-08-04 - Hardcoded Default Session SECRET_KEY
**Vulnerability:** The Flask application was initialized with a hardcoded static `SECRET_KEY` ('roastlab_secret_key_change_this_immediately'). Since Flask relies on client-side session cookies cryptographically signed by the secret key, anyone with knowledge of this key can craft forged session cookies to log in as any user.
**Learning:** Default keys are often left unchanged in production deployments, presenting a massive high-severity privilege escalation and authorization bypass risk.
**Prevention:** Always implement a secure-by-default runtime fallback. If `os.environ` does not specify a secret key, dynamically generate a secure random 32-byte hex token via `secrets.token_hex(32)`.

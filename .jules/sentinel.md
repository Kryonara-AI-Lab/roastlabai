# Sentinel's Journal

## 2026-03-05 - Insecure Hardcoded Flask Secret Key
**Vulnerability:** The Flask application used a static, hardcoded session SECRET_KEY (`roastlab_secret_key_change_this_immediately`), exposing the application to session cookie tampering and forgery.
**Learning:** Hardcoding secrets is easy during development but leads to severe vulnerabilities if deployed. Session validation relies entirely on the secrecy of this key.
**Prevention:** Always lookup keys dynamically from environment variables and provide a secure, cryptographically random fallback using `secrets.token_hex(32)`.

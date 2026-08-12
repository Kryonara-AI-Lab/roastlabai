# Sentinel's Journal: Critical Learnings

This journal contains entries for critical security learnings discovered in the RoastLab AI codebase.

## 2025-02-18 - [Dynamic Session Secrets & Global Security Headers]
**Vulnerability:** A hardcoded `SECRET_KEY` was configured in the Flask application, putting session data integrity and cryptographic verification at risk. Furthermore, global security headers such as `X-Frame-Options`, `X-Content-Type-Options`, and `Referrer-Policy` were entirely missing from application responses, exposing the application to clickjacking, MIME-sniffing, and potentially leaky HTTP referrers.
**Learning:** Hardcoding application secrets is a severe anti-pattern that leads to compromised user sessions when the code is publicly or semi-publicly visible. Simultaneously, omission of essential security headers lowers defense-in-depth levels and leaves client-side rendering vulnerability vectors undefended.
**Prevention:** Always load session secret keys dynamically from environment variables using a cryptographically secure fallback (e.g., `secrets.token_hex(32)`) so that secrets are never checked in. Enforce strict session cookie attributes (`HttpOnly`, `SameSite=Lax`, and `Secure` where appropriate) and configure an `@after_request` filter to set global security headers on all responses dynamically.

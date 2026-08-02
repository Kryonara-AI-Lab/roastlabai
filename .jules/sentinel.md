# Sentinel Security Journal

This journal records critical security learnings and unique codebase vulnerability insights encountered during our defensive audits.

## 2026-06-15 - Hardcoded Default Session SECRET_KEY
**Vulnerability:** The Flask application was initialized with a hardcoded static `SECRET_KEY` ('roastlab_secret_key_change_this_immediately'). Since Flask relies on client-side session cookies cryptographically signed by the secret key, anyone with knowledge of this key can craft forged session cookies to log in as any user.
**Learning:** Default keys are often left unchanged in production deployments, presenting a massive high-severity privilege escalation and authorization bypass risk.
**Prevention:** Always implement a secure-by-default runtime fallback. If `os.environ` does not specify a secret key, dynamically generate a secure random 32-byte hex token via `secrets.token_hex(32)`.

## 2026-06-15 - Script-Context Template Injection and JS Crash
**Vulnerability:** Embedding Jinja2 template variables directly inside JavaScript `<script>` contexts using raw string double quotes (e.g., `headline: "{{ roast_result.headline }}"`) can cause XSS or critical client-side execution crashes if the interpolated values contain unescaped quotes or newlines.
**Learning:** Jinja's default HTML autoescaping is insufficient for JavaScript contexts, as quotes, newlines, and other special characters require different escaping schemes to remain syntactically valid in JS.
**Prevention:** Avoid manually wrapping template variables in JS quotes. Instead, use Jinja's built-in `| tojson` filter (and `| safe` when needed inside scripts) to natively output safely escaped JSON representations of objects, lists, and strings.

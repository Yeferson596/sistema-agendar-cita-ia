import json
import re
from fastapi import Request

# patterns and replacements
PATTERNS = [
    (re.compile(r"\b\d{7,8}-[\dkK]\b"), '[REDACTED_RUT]'),
    (re.compile(r"\b\d{13,19}\b"), '[REDACTED_CARD]'),
]

# These fields must not be redacted because they are required for auth and registration.
EXEMPT_FIELDS = {'email', 'password', 'id_token', 'display_name'}


def redact(obj, key: str | None = None):
    if isinstance(obj, str):
        if key in EXEMPT_FIELDS:
            return obj
        s = obj
        for pat, rep in PATTERNS:
            s = pat.sub(rep, s)
        # redact emails only in unstructured text fields, not auth fields
        if key not in EXEMPT_FIELDS:
            s = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", '[REDACTED_EMAIL]', s)
        return s
    if isinstance(obj, dict):
        return {k: redact(v, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(x, key) for x in obj]
    return obj


async def sanitizer_middleware(request: Request, call_next):
    try:
        raw = await request.body()
        if not raw:
            return await call_next(request)
        body = raw.decode('utf-8', errors='ignore')
        try:
            json_body = await request.json()
        except Exception:
            return await call_next(request)
        sanitized = redact(json_body)
        request._body = json.dumps(sanitized, ensure_ascii=False).encode('utf-8')
    except Exception:
        pass
    return await call_next(request)

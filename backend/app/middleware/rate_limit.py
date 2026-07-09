import time
from fastapi import Request, HTTPException

# very small in-memory rate limiter: 10 req / 60s per IP
# NOTE: OPTIONS requests are preflight CORS checks and should not count here.
STORE: dict = {}
LIMIT = 10
WINDOW = 60


async def rate_limit_middleware(request: Request, call_next):
    if request.method == 'OPTIONS':
        return await call_next(request)

    client = request.client.host if request.client else 'anon'
    now = int(time.time())
    window_start = now - WINDOW
    hits = STORE.get(client, [])
    # remove old
    hits = [t for t in hits if t >= window_start]
    if len(hits) >= LIMIT:
        raise HTTPException(status_code=429, detail='rate limit exceeded')
    hits.append(now)
    STORE[client] = hits
    return await call_next(request)

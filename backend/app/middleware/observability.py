from time import perf_counter
from fastapi import Request
from app.observability import metrics as obs_metrics
from app.observability.logger import log_event


async def observability_middleware(request: Request, call_next):
    t0 = perf_counter()
    response = await call_next(request)
    latency_ms = (perf_counter() - t0) * 1000
    # record
    try:
        obs_metrics.record_call(latency_ms)
    except Exception:
        pass
    # keep small payload for logs
    log_event('INFO', request.url.path, {
        'method': request.method,
        'latency_ms': round(latency_ms, 2),
        'status': response.status_code,
        'session_id': request.headers.get('X-Session-Id', 'anon')
    })
    return response

from fastapi import APIRouter, Depends
from app.observability.metrics import metrics
from app.deps import require_admin
from typing import List

router = APIRouter(prefix='/metrics', tags=['observability'])


def percentile(arr: List[float], p: float) -> float:
    if not arr:
        return 0.0
    a = sorted(arr)
    k = (len(a)-1) * (p/100.0)
    f = int(k)
    c = min(f+1, len(a)-1)
    if f == c:
        return a[int(k)]
    d0 = a[f] * (c - k)
    d1 = a[c] * (k - f)
    return d0 + d1


@router.get('/', dependencies=[Depends(require_admin)])
async def get_metrics():
    lats = metrics.latencies_ms or [0]
    return {
        'precision_rate': round(metrics.precision_rate, 2),
        'fallback_rate': round(metrics.fallback_rate, 2),
        'total_calls': metrics.total_calls,
        'errors': metrics.errors,
        'latency': {
            'p50': round(float(percentile(lats, 50)), 1),
            'p90': round(float(percentile(lats, 90)), 1),
            'p99': round(float(percentile(lats, 99)), 1),
        }
    }

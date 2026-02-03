"""Prometheus metrics for GrocyScan."""

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

# ==================== Scan Metrics ====================

SCANS_TOTAL = Counter(
    "grocyscan_scans_total",
    "Total number of barcode scans",
    ["status", "barcode_type", "input_method"],
)

SCAN_DURATION = Histogram(
    "grocyscan_scan_duration_seconds",
    "Duration of scan operations",
    ["barcode_type"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ==================== Lookup Metrics ====================

LOOKUP_TOTAL = Counter(
    "grocyscan_lookup_total",
    "Total number of barcode lookups",
    ["provider", "status"],
)

LOOKUP_DURATION = Histogram(
    "grocyscan_lookup_duration_seconds",
    "Duration of lookup operations",
    ["provider"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

LOOKUP_CACHE_TOTAL = Counter(
    "grocyscan_lookup_cache_total",
    "Lookup cache hits and misses",
    ["result"],  # hit, miss
)

# ==================== Grocy Metrics ====================

GROCY_OPERATIONS_TOTAL = Counter(
    "grocyscan_grocy_operations_total",
    "Total Grocy API operations",
    ["operation", "status"],
)

GROCY_DURATION = Histogram(
    "grocyscan_grocy_duration_seconds",
    "Duration of Grocy API operations",
    ["operation"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ==================== LLM Metrics ====================

LLM_OPERATIONS_TOTAL = Counter(
    "grocyscan_llm_operations_total",
    "Total LLM operations",
    ["operation", "status"],
)

LLM_DURATION = Histogram(
    "grocyscan_llm_duration_seconds",
    "Duration of LLM operations",
    ["operation"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

LLM_TOKENS = Counter(
    "grocyscan_llm_tokens_total",
    "Total LLM tokens used",
    ["type"],  # input, output
)

# ==================== Job Queue Metrics ====================

JOB_QUEUE_SIZE = Gauge(
    "grocyscan_job_queue_size",
    "Current job queue size",
    ["status"],
)

JOBS_TOTAL = Counter(
    "grocyscan_jobs_total",
    "Total jobs processed",
    ["job_type", "status"],
)

JOB_DURATION = Histogram(
    "grocyscan_job_duration_seconds",
    "Duration of job execution",
    ["job_type"],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0],
)

# ==================== System Metrics ====================

ACTIVE_SESSIONS = Gauge(
    "grocyscan_active_sessions",
    "Number of active user sessions",
)


def record_scan(
    status: str,
    barcode_type: str,
    input_method: str,
    duration_seconds: float,
) -> None:
    """Record a scan operation.

    Args:
        status: Scan result status (found, not_found, error)
        barcode_type: Type of barcode (EAN-13, UPC-A, etc.)
        input_method: How barcode was entered (camera, scanner, manual)
        duration_seconds: Time taken for the scan
    """
    SCANS_TOTAL.labels(
        status=status,
        barcode_type=barcode_type,
        input_method=input_method,
    ).inc()
    SCAN_DURATION.labels(barcode_type=barcode_type).observe(duration_seconds)


def record_lookup(
    provider: str,
    status: str,
    duration_seconds: float,
    cache_hit: bool = False,
) -> None:
    """Record a lookup operation.

    Args:
        provider: Lookup provider name
        status: Result status (found, not_found, error)
        duration_seconds: Time taken for the lookup
        cache_hit: Whether result was from cache
    """
    LOOKUP_TOTAL.labels(provider=provider, status=status).inc()
    LOOKUP_DURATION.labels(provider=provider).observe(duration_seconds)
    LOOKUP_CACHE_TOTAL.labels(result="hit" if cache_hit else "miss").inc()


def record_grocy_operation(
    operation: str,
    status: str,
    duration_seconds: float,
) -> None:
    """Record a Grocy API operation.

    Args:
        operation: Operation type (add_stock, create_product, etc.)
        status: Result status (success, error)
        duration_seconds: Time taken for the operation
    """
    GROCY_OPERATIONS_TOTAL.labels(operation=operation, status=status).inc()
    GROCY_DURATION.labels(operation=operation).observe(duration_seconds)


def record_llm_operation(
    operation: str,
    status: str,
    duration_seconds: float,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> None:
    """Record an LLM operation.

    Args:
        operation: Operation type (optimize, merge)
        status: Result status (success, error)
        duration_seconds: Time taken for the operation
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    """
    LLM_OPERATIONS_TOTAL.labels(operation=operation, status=status).inc()
    LLM_DURATION.labels(operation=operation).observe(duration_seconds)
    if input_tokens:
        LLM_TOKENS.labels(type="input").inc(input_tokens)
    if output_tokens:
        LLM_TOKENS.labels(type="output").inc(output_tokens)


def update_job_queue_metrics(stats: dict[str, int]) -> None:
    """Update job queue size metrics.

    Args:
        stats: Job counts by status
    """
    for status, count in stats.items():
        JOB_QUEUE_SIZE.labels(status=status).set(count)


def record_job(
    job_type: str,
    status: str,
    duration_seconds: float | None = None,
) -> None:
    """Record a job completion.

    Args:
        job_type: Type of job
        status: Result status (completed, failed)
        duration_seconds: Time taken for the job
    """
    JOBS_TOTAL.labels(job_type=job_type, status=status).inc()
    if duration_seconds is not None:
        JOB_DURATION.labels(job_type=job_type).observe(duration_seconds)


async def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics endpoint.

    Args:
        request: Incoming request

    Returns:
        Response: Prometheus metrics in text format
    """
    return Response(
        content=generate_latest(),
        media_type="text/plain",
    )

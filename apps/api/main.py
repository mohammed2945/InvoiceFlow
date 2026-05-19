import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from apps.api.db import init_db
from apps.api.routes import customers, dashboard, invoices, payments, plans, usage_events
from packages.observability.logging import configure_logging, get_logger, log_event
from packages.observability.metrics import increment, timing

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="InvoiceFlow", version="0.1.0")

app.include_router(customers.router)
app.include_router(plans.router)
app.include_router(usage_events.router)
app.include_router(invoices.router)
app.include_router(payments.router)
app.include_router(dashboard.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    start = time.perf_counter()
    route = request.url.path
    increment("invoice.api.request.count", extra_tags=[f"route:{route}", f"method:{request.method}"])
    try:
        response = await call_next(request)
    except Exception as exc:
        increment(
            "invoice.api.request.error",
            extra_tags=[f"route:{route}", f"method:{request.method}"],
        )
        log_event(
            logger,
            "error",
            "api_request_failed",
            route=route,
            method=request.method,
            error=str(exc),
        )
        raise

    elapsed_ms = (time.perf_counter() - start) * 1000
    timing(
        "invoice.api.request.latency_ms",
        elapsed_ms,
        extra_tags=[f"route:{route}", f"method:{request.method}"],
    )

    if response.status_code >= 500:
        increment(
            "invoice.api.request.error",
            extra_tags=[
                f"route:{route}",
                f"method:{request.method}",
                f"status_code:{response.status_code}",
            ],
        )
        log_event(
            logger,
            "error",
            "api_request_failed",
            route=route,
            method=request.method,
            status_code=response.status_code,
        )
    else:
        log_event(
            logger,
            "info",
            "api_request_completed",
            route=route,
            method=request.method,
            status_code=response.status_code,
            latency_ms=round(elapsed_ms, 2),
        )

    return response


@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})

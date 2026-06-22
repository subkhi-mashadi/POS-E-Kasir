from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
from app.core.config import settings
from app.api.v1 import auth, transactions, products, stock, customers, reports, branches
from app.api.v1 import promotions, suppliers

app = FastAPI(
    title="KasirPro API",
    version="1.0.0",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=None,
)

# Sentry (optional — only init if DSN provided)
if settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# In-memory rate limiter (replace with Redis-backed in prod)
_rate_buckets: dict = defaultdict(list)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60
    _rate_buckets[client_ip] = [t for t in _rate_buckets[client_ip] if now - t < window]
    if len(_rate_buckets[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
        return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
    _rate_buckets[client_ip].append(now)
    response = await call_next(request)
    return response

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

app.include_router(auth.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(stock.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(branches.router, prefix="/api/v1")
app.include_router(promotions.router, prefix="/api/v1")
app.include_router(suppliers.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "env": settings.ENVIRONMENT}

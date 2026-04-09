from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.models.database import init_db
from app.routes.auth      import router as auth_router
from app.routes.users     import router as users_router
from app.routes.records   import router as records_router
from app.routes.dashboard import router as dashboard_router

# ── Rate limiter ───────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["100/15minutes"])

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Finance Dashboard API",
    description="Finance Data Processing and Access Control Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database init ──────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    init_db()

# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    from datetime import datetime
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth_router,      prefix="/api")
app.include_router(users_router,     prefix="/api")
app.include_router(records_router,   prefix="/api")
app.include_router(dashboard_router, prefix="/api")

# ── 404 handler ────────────────────────────────────────────────────────────────
@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": f"Route {request.method} {request.url.path} not found"}
    )

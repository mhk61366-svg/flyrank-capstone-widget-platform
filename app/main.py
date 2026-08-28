from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.config import ALLOWED_ORIGINS
from app.routes import widgets, submissions, widget_public
from app.services.rate_limit import limiter
from slowapi.middleware import SlowAPIMiddleware

app = FastAPI(title="Embedable Widget & Lead-Capture Platform")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(widgets.router)
app.include_router(submissions.router)
app.include_router(widget_public.router)



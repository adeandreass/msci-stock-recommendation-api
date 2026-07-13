from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    dashboard,
    investor_profiles,
    portfolio,
    stocks,
    system
)


app = FastAPI(
    title=settings.app_name,
    description=(
        "API untuk menampilkan forecast saham "
        "dan rekomendasi Mean-Variance Portfolio Optimization."
    ),
    version=settings.app_version
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"]
)

app.include_router(system.router)

app.include_router(
    dashboard.router,
    prefix=settings.api_prefix
)

app.include_router(
    portfolio.router,
    prefix=settings.api_prefix
)

app.include_router(
    stocks.router,
    prefix=settings.api_prefix
)

app.include_router(
    investor_profiles.router,
    prefix=settings.api_prefix
)
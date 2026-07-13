from fastapi import APIRouter

from app.services.json_repository import repository


router = APIRouter(
    tags=["System"]
)


@router.get("/")
def root():
    return {
        "message": "MSCI Indonesia Stock Recommendation API aktif.",
        "documentation": "/docs"
    }


@router.get("/health")
def health_check():
    return repository.get_health()
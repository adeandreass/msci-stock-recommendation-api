from fastapi import APIRouter

from app.services.json_repository import repository


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("")
def get_dashboard():
    return repository.get_dashboard()
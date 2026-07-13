from fastapi import APIRouter

from app.services.json_repository import repository


router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"]
)


@router.get("")
def get_portfolio():
    return repository.get_portfolio()
from fastapi import APIRouter, Query

from app.services.json_repository import repository


router = APIRouter(
    prefix="/stocks",
    tags=["Stocks"]
)


@router.get("")
def get_stocks():
    return repository.get_stocks()


@router.get("/{ticker}/forecast")
def get_stock_forecast(
    ticker: str,
    limit: int | None = Query(
        default=None,
        ge=1,
        le=1000
    )
):
    return repository.get_stock_forecast(
        ticker=ticker,
        limit=limit
    )


@router.get("/{ticker}")
def get_stock_detail(ticker: str):
    return repository.get_stock(
        ticker=ticker
    )
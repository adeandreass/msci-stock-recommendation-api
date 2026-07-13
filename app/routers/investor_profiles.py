from fastapi import APIRouter, Query

from app.services.json_repository import repository


router = APIRouter(
    prefix="/investor-profiles",
    tags=["Investor Profiles"]
)


@router.get("")
def get_investor_profiles():
    return repository.get_investor_profiles()


@router.get("/{profile_key}/allocation")
def get_profile_allocation(
    profile_key: str,
    capital: int = Query(
        ...,
        gt=0,
        le=1_000_000_000,
        description="Nominal modal investasi dalam Rupiah."
    )
):
    return repository.get_profile_allocation(
        profile_key=profile_key,
        capital=capital
    )


@router.get("/{profile_key}")
def get_investor_profile(profile_key: str):
    return repository.get_investor_profile(
        profile_key
    )
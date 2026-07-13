import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings


class JsonDataRepository:
    """
    Service untuk membaca JSON hasil Google Colab.
    """

    DATA_FILES = {
        "dashboard": "dashboard_summary.json",
        "portfolio": "portfolio_recommendation.json",
        "forecast": "forecast_daily.json",
        "risk_profiles": "risk_profile_portfolios.json"
    }

    PROFILE_ALIASES = {
        "conservative": "conservative",
        "konservatif": "conservative",
        "low_risk": "conservative",

        "moderate": "moderate",
        "moderat": "moderate",
        "balanced": "moderate",

        "aggressive": "aggressive",
        "agresif": "aggressive",
        "high_risk": "aggressive"
    }

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def _get_file_path(self, file_key: str) -> Path:
        return self.data_dir / self.DATA_FILES[file_key]

    def _load_json(self, file_key: str) -> dict[str, Any]:
        file_path = self._get_file_path(file_key)

        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    f"File data '{file_path.name}' belum tersedia. "
                    "Pastikan JSON hasil Google Colab sudah dipindahkan ke folder data."
                )
            )

        try:
            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:
                payload = json.load(file)

        except json.JSONDecodeError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"File '{file_path.name}' tidak valid sebagai JSON: {error}"
                )
            )

        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Struktur '{file_path.name}' harus berbentuk object JSON."
                )
            )

        return payload

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def normalize_ticker(ticker: str) -> str:
        normalized = ticker.strip().upper()

        if normalized and not normalized.endswith(".JK"):
            normalized = f"{normalized}.JK"

        return normalized

    def normalize_profile_key(self, profile_key: str) -> str:
        normalized = (
            profile_key.strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        return self.PROFILE_ALIASES.get(
            normalized,
            normalized
        )

    def get_health(self) -> dict[str, Any]:
        file_status = {}

        for _, file_name in self.DATA_FILES.items():
            file_path = self.data_dir / file_name

            file_status[file_name] = {
                "available": file_path.exists(),
                "size_bytes": (
                    file_path.stat().st_size
                    if file_path.exists()
                    else 0
                )
            }

        all_files_ready = all(
            item["available"]
            for item in file_status.values()
        )

        return {
            "status": "ok" if all_files_ready else "degraded",
            "service": "msci-stock-recommendation-api",
            "data_ready": all_files_ready,
            "files": file_status
        }

    def get_dashboard(self) -> dict[str, Any]:
        return self._load_json("dashboard")

    def get_portfolio(self) -> dict[str, Any]:
        return self._load_json("portfolio")

    def get_forecast_payload(self) -> dict[str, Any]:
        return self._load_json("forecast")

    def get_risk_profile_payload(self) -> dict[str, Any]:
        return self._load_json("risk_profiles")

    def get_stock_records(self) -> list[dict[str, Any]]:
        dashboard_payload = self.get_dashboard()

        stock_records = dashboard_payload.get(
            "asset_summary",
            []
        )

        if not isinstance(stock_records, list):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="asset_summary pada dashboard_summary.json tidak valid."
            )

        return stock_records

    def get_stocks(self) -> dict[str, Any]:
        dashboard_payload = self.get_dashboard()

        stock_records = sorted(
            self.get_stock_records(),
            key=lambda item: (
                -self._to_float(
                    item.get("Weight_Percent", 0)
                ),
                str(item.get("Ticker", ""))
            )
        )

        return {
            "metadata": dashboard_payload.get("metadata", {}),
            "total_records": len(stock_records),
            "stocks": stock_records
        }

    def get_stock(self, ticker: str) -> dict[str, Any]:
        normalized_ticker = self.normalize_ticker(ticker)

        for stock in self.get_stock_records():
            stock_ticker = str(
                stock.get("Ticker", "")
            ).upper()

            if stock_ticker == normalized_ticker:
                return {
                    "ticker": normalized_ticker,
                    "stock": stock
                }

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker '{normalized_ticker}' tidak ditemukan."
        )

    def get_stock_forecast(
        self,
        ticker: str,
        limit: int | None = None
    ) -> dict[str, Any]:
        normalized_ticker = self.normalize_ticker(ticker)

        forecast_payload = self.get_forecast_payload()

        forecast_records = forecast_payload.get(
            "forecast_data",
            []
        )

        if not isinstance(forecast_records, list):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="forecast_data pada forecast_daily.json tidak valid."
            )

        ticker_forecast = [
            row
            for row in forecast_records
            if str(row.get("Ticker", "")).upper()
            == normalized_ticker
        ]

        if len(ticker_forecast) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Forecast untuk ticker '{normalized_ticker}' "
                    "tidak ditemukan."
                )
            )

        ticker_forecast = sorted(
            ticker_forecast,
            key=lambda item: str(
                item.get("Forecast_Date", "")
            )
        )

        total_records = len(ticker_forecast)

        if limit is not None:
            ticker_forecast = ticker_forecast[:limit]

        return {
            "ticker": normalized_ticker,
            "metadata": forecast_payload.get("metadata", {}),
            "total_records": total_records,
            "returned_records": len(ticker_forecast),
            "forecast": ticker_forecast
        }

    def get_investor_profiles(self) -> dict[str, Any]:
        payload = self.get_risk_profile_payload()

        profiles = payload.get("profiles", [])

        if not isinstance(profiles, list):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="profiles pada risk_profile_portfolios.json tidak valid."
            )

        summaries = []

        for profile in profiles:
            summary = {
                key: value
                for key, value in profile.items()
                if key != "holdings"
            }

            summaries.append(summary)

        return {
            "metadata": payload.get("metadata", {}),
            "total_profiles": len(summaries),
            "profiles": summaries
        }

    def get_investor_profile(
        self,
        profile_key: str
    ) -> dict[str, Any]:
        normalized_key = self.normalize_profile_key(
            profile_key
        )

        payload = self.get_risk_profile_payload()

        profiles = payload.get("profiles", [])

        for profile in profiles:
            if profile.get("profile_key") == normalized_key:
                return {
                    "metadata": payload.get("metadata", {}),
                    "profile": profile
                }

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Profil investor '{profile_key}' tidak ditemukan. "
                "Gunakan conservative, moderate, atau aggressive."
            )
        )

    def get_profile_allocation(
        self,
        profile_key: str,
        capital: int
    ) -> dict[str, Any]:
        profile_payload = self.get_investor_profile(
            profile_key
        )

        profile = profile_payload["profile"]

        holdings = profile.get("holdings", [])

        if len(holdings) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Portofolio profil belum memiliki saham aktif."
            )

        raw_weights = [
            self._to_float(
                holding.get("Weight", 0)
            )
            for holding in holdings
        ]

        total_weight = sum(raw_weights)

        if total_weight <= 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Total bobot portofolio tidak valid."
            )

        allocation_rows = []

        for holding, weight in zip(
            holdings,
            raw_weights
        ):
            normalized_weight = weight / total_weight

            allocation_rows.append({
                "Ticker": holding.get("Ticker"),
                "Weight": normalized_weight,
                "Weight_Percent": normalized_weight * 100,
                "Allocation_IDR": int(
                    round(capital * normalized_weight)
                ),
                "Forecast_Horizon_Return_Percent": holding.get(
                    "Forecast_Horizon_Return_Percent"
                ),
                "Historical_Annualized_Volatility_Percent": holding.get(
                    "Historical_Annualized_Volatility_Percent"
                )
            })

        allocated_total = sum(
            row["Allocation_IDR"]
            for row in allocation_rows
        )

        difference = capital - allocated_total

        if difference != 0:
            allocation_rows[0]["Allocation_IDR"] += difference

        return {
            "metadata": profile_payload["metadata"],
            "profile_key": profile.get("profile_key"),
            "profile_label": profile.get("profile_label"),
            "strategy": profile.get("strategy"),
            "strategy_label": profile.get("strategy_label"),
            "input_capital_idr": capital,
            "total_allocation_idr": sum(
                row["Allocation_IDR"]
                for row in allocation_rows
            ),
            "portfolio_metrics": profile.get(
                "portfolio_metrics",
                {}
            ),
            "allocations": allocation_rows
        }


repository = JsonDataRepository(
    data_dir=settings.data_dir
)
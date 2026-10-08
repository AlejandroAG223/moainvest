"""Controlador de la app "CAPM": retorno esperado anual por activo, por
sector (los datos de la tabla llegan desde la API)."""
from __future__ import annotations

from flask import Blueprint, render_template

from app.capm import analysis
from app.core.navigation import get_app

bp = Blueprint(
    "capm",
    __name__,
    url_prefix="/app/capm",
    template_folder="templates",
    static_folder="static",
)


@bp.get("/")
def index():
    return render_template(
        "capm/index.html",
        active_app=get_app("capm"),
        sectors=list(analysis.SECTORS.keys()),
        sector_icons=analysis.SECTOR_ICONS,
        years=analysis.available_years(),
        all_years=analysis.ALL_YEARS,
        markets=analysis.MARKET_TICKERS,
        risk_free_ticker=analysis.RISK_FREE_TICKER,
    )

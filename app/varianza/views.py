"""Controlador de la app "Análisis de Varianza": histórico de precios de un
ticker y histogramas de volatilidad mensual (los datos llegan desde la API)."""
from __future__ import annotations

from flask import Blueprint, render_template

from app.core.navigation import get_app
from app.varianza.api import MAX_VOLATILITY_TICKERS

bp = Blueprint(
    "varianza",
    __name__,
    url_prefix="/app/analisis-varianza",
    template_folder="templates",
    static_folder="static",
)

# Chips de sugerencia del formulario de volatilidad.
SUGGESTED_TICKERS = ("AAPL", "MSFT", "NVDA", "GOOG", "AMZN", "SPY")


@bp.get("/")
def index():
    return render_template(
        "varianza/index.html",
        active_app=get_app("analisis-varianza"),
        max_tickers=MAX_VOLATILITY_TICKERS,
        suggested_tickers=SUGGESTED_TICKERS,
    )

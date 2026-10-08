"""API de la app "CAPM": tabla de retornos esperados por sector (JSON)."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.capm import analysis

bp = Blueprint("capm_api", __name__, url_prefix="/api")


@bp.get("/capm-table")
def capm_table():
    """Tabla de CAPM (beta, retorno esperado anual, tasa libre de riesgo y
    "desde") de un sector, para un año y un proxy de mercado.

    ?sector=Oil %26 Gas&year=2020&market=SPY (``year`` también acepta "Todos")
    """
    sector = request.args.get("sector", "")
    market = request.args.get("market", "")
    year_param = request.args.get("year", analysis.ALL_YEARS)

    if sector not in analysis.SECTORS:
        return jsonify({"error": "sector inválido"}), 400
    if market not in analysis.MARKET_TICKERS.values():
        return jsonify({"error": "market inválido"}), 400

    if year_param == analysis.ALL_YEARS:
        year: int | str = analysis.ALL_YEARS
    else:
        try:
            year = int(year_param)
        except ValueError:
            return jsonify({"error": "year inválido"}), 400
        if year not in analysis.available_years():
            return jsonify({"error": "year inválido"}), 400

    table = analysis.build_sector_capm_table(sector, year, market)

    rows = [
        {
            "ticker": ticker,
            "beta": row["Beta"],
            "expected_return": row[analysis.EXPECTED_RETURN_COL],
            "risk_free_rate": row["Tasa libre de riesgo"],
            "since": row["Desde"].isoformat(),
        }
        for ticker, row in table.to_dict(orient="index").items()
    ]

    return jsonify({"rows": rows, "risk_free_ticker": analysis.RISK_FREE_TICKER})

"""API del Graficador: catálogo de indicadores técnicos y su cálculo con TA-Lib."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.core import market_data
from app.core.api import ALLOWED_INTERVALS, ALLOWED_RANGES
from app.graficador import indicators
from app.graficador.views import TICKER_RE

bp = Blueprint("graficador_api", __name__, url_prefix="/api/graficador")


@bp.get("/indicators")
def indicator_catalog():
    """Indicadores disponibles: parámetros, salidas, categoría y paleta."""
    return jsonify(indicators.catalog())


@bp.get("/<ticker>/indicators")
def compute_indicators(ticker: str):
    """Calcula uno o varios indicadores sobre las velas de ``ticker``.

    ?range=6mo&interval=1d&ind=sma:20&ind=macd:12,26,9

    Devuelve ``{"time": [...], "indicators": [{"spec", "outputs": {clave: [...]}}]}``
    con los valores alineados con ``time`` (``null`` mientras el indicador se
    calienta). Los indicadores se calculan sobre más historia que la visible
    para que una SMA(200) ya tenga valor en la primera vela del gráfico.
    """
    ticker = ticker.strip().upper()
    range_ = request.args.get("range", "6mo")
    interval = request.args.get("interval", "1d")
    specs = request.args.getlist("ind")

    if not TICKER_RE.match(ticker):
        return jsonify({"error": f"«{ticker[:20]}» no es un ticker válido"}), 400
    if range_ not in ALLOWED_RANGES or interval not in ALLOWED_INTERVALS:
        return jsonify({"error": "range o interval inválidos"}), 400
    if not specs:
        return jsonify({"error": "Indica al menos un indicador (ind=sma:20)"}), 400
    if len(specs) > indicators.MAX_INDICATORS:
        return jsonify({"error": f"Máximo {indicators.MAX_INDICATORS} indicadores a la vez"}), 400

    try:
        for spec in specs:
            indicators.parse_spec(spec)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    candles = market_data.get_candles(ticker, range_, interval)
    if not candles:
        return jsonify(indicators.compute_series([], specs))

    warm = indicators.warmup_range(range_, interval)
    history = candles if warm == range_ else market_data.get_candles(ticker, warm, interval)
    return jsonify(indicators.compute_series(history or candles, specs, since=candles[0]["time"]))

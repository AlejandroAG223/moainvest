"""API de la app "QUANT STATS": gráficas PNG de quantstats para cualquier ticker."""
from __future__ import annotations

from flask import Blueprint, Response, jsonify, request

from app.quant_stats import quant

bp = Blueprint("quant_stats_api", __name__, url_prefix="/api")

QUANT_PERIODS = {"1y", "2y", "5y", "max"}


@bp.get("/quant/<ticker>/drawdown.png")
def quant_drawdown(ticker: str):
    """Serie de drawdown (PNG) calculada con quantstats. ?period=2y"""
    period = request.args.get("period", "2y")
    if period not in QUANT_PERIODS:
        return jsonify({"error": "period inválido"}), 400
    return Response(quant.render_drawdown_chart(ticker.upper(), period), mimetype="image/png")


@bp.get("/quant/<ticker>/monthly-heatmap.png")
def quant_monthly_heatmap(ticker: str):
    """Heatmap (PNG) de retornos mensuales calculados con quantstats. ?period=2y"""
    period = request.args.get("period", "2y")
    if period not in QUANT_PERIODS:
        return jsonify({"error": "period inválido"}), 400
    return Response(quant.render_monthly_heatmap(ticker.upper(), period), mimetype="image/png")


@bp.get("/quant/<ticker>/earnings.png")
def quant_earnings(ticker: str):
    """Comparación (PNG) de los últimos reportes de resultados. ?count=4"""
    count = request.args.get("count", 4, type=int)
    if count is None or not 2 <= count <= 8:
        return jsonify({"error": "count debe estar entre 2 y 8"}), 400
    return Response(quant.render_earnings_chart(ticker.upper(), count), mimetype="image/png")


@bp.get("/quant/<ticker>/plot/<slug>.png")
def quant_plot(ticker: str, slug: str):
    """Gráfica nativa (PNG) de ``quantstats.plots``. ?period=2y&benchmark=SPY&window=126"""
    ticker = quant.normalize_ticker(ticker)
    if ticker is None:
        return jsonify({"error": "ticker inválido"}), 400
    if quant.get_plot(slug) is None:
        return jsonify({"error": "gráfica desconocida"}), 404
    period = request.args.get("period", "2y")
    if period not in QUANT_PERIODS:
        return jsonify({"error": "period inválido"}), 400
    benchmark = request.args.get("benchmark") or None
    if benchmark is not None:
        benchmark = quant.normalize_ticker(benchmark)
        if benchmark is None:
            return jsonify({"error": "benchmark inválido"}), 400
    window = request.args.get("window", type=int)
    if "window" in request.args and window not in quant.ROLLING_WINDOWS:
        return jsonify({"error": "window inválido"}), 400
    png_bytes = quant.render_qs_plot(ticker, period, slug, benchmark=benchmark, window=window)
    return Response(png_bytes, mimetype="image/png")


@bp.get("/quant/<ticker>/montecarlo.png")
def quant_montecarlo(ticker: str):
    """Simulación Monte Carlo (PNG) de ``quantstats.stats.montecarlo``.
    ?period=2y&sims=1000&bust=-20&goal=50 (bust y goal en %)"""
    ticker = quant.normalize_ticker(ticker)
    if ticker is None:
        return jsonify({"error": "ticker inválido"}), 400
    period = request.args.get("period", "2y")
    if period not in QUANT_PERIODS:
        return jsonify({"error": "period inválido"}), 400
    sims = request.args.get("sims", quant.DEFAULT_MONTECARLO_SIMS, type=int)
    if sims not in quant.MONTECARLO_SIMS:
        return jsonify({"error": "sims inválido"}), 400
    bust = request.args.get("bust", quant.DEFAULT_BUST * 100, type=float)
    goal = request.args.get("goal", quant.DEFAULT_GOAL * 100, type=float)
    if bust is None or not -99 <= bust <= -1 or goal is None or not 1 <= goal <= 2000:
        return jsonify({"error": "bust debe estar entre -99 y -1 y goal entre 1 y 2000"}), 400
    png_bytes = quant.render_montecarlo_chart(ticker, period, sims, bust / 100, goal / 100)
    return Response(png_bytes, mimetype="image/png")

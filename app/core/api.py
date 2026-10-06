"""API JSON común: watchlists, precios y velas (Yahoo Finance) y email de prueba.

La consumen el JavaScript del sitio MOAINVEST y las demás apps.
"""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.core import market_data
from app.core.email import EmailError, send_email
from app.core.watchlists import WATCHLISTS, get_watchlist

bp = Blueprint("core_api", __name__, url_prefix="/api")

ALLOWED_INTERVALS = {"1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"}
ALLOWED_RANGES = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"}


@bp.get("/watchlists")
def watchlists():
    """Registro de watchlists (slug, nombre, icono y símbolos) para el front-end."""
    return jsonify(
        [
            {
                "slug": w.slug,
                "name": w.name,
                "icon": w.icon,
                "symbols": [{"ticker": s.ticker, "name": s.display_name} for s in w.symbols],
            }
            for w in WATCHLISTS
        ]
    )


@bp.get("/quote/<ticker>")
def quote(ticker: str):
    return jsonify(market_data.get_quote(ticker).to_dict())


@bp.get("/candles/<ticker>")
def candles(ticker: str):
    range_ = request.args.get("range", "6mo")
    interval = request.args.get("interval", "1d")
    if range_ not in ALLOWED_RANGES or interval not in ALLOWED_INTERVALS:
        return jsonify({"error": "range o interval inválidos"}), 400
    return jsonify(market_data.get_candles(ticker, range_, interval))


@bp.get("/watchlist/<slug>/quotes")
def watchlist_quotes(slug: str):
    """Precios de todos los símbolos de una watchlist, para pintar el sidebar."""
    watchlist = get_watchlist(slug)
    if watchlist is None:
        return jsonify({"error": "watchlist no encontrada"}), 404
    quotes = {s.ticker: market_data.get_quote(s.ticker).to_dict() for s in watchlist.symbols}
    return jsonify(quotes)


@bp.post("/email/send")
def send_email_route():
    """Envía un email de prueba vía Resend.

    Body JSON: {"to": "destino@ejemplo.com", "subject": "...", "html": "..."}
    (``subject`` y ``html`` son opcionales, para probar rápido con solo ``to``).
    """
    data = request.get_json(silent=True) or {}
    to = data.get("to")
    if not to:
        return jsonify({"error": "Indica el destinatario en 'to'"}), 400

    subject = data.get("subject") or f"Prueba de {current_app.config['SITE_NAME']}"
    html = data.get("html") or f"<p>Este es un email de prueba enviado desde {current_app.config['SITE_NAME']}.</p>"

    try:
        email_id = send_email(to, subject, html)
    except EmailError as exc:
        return jsonify({"error": str(exc)}), 502

    return jsonify({"id": email_id}), 200

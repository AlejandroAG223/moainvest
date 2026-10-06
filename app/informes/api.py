"""API de la app "Informes": vista previa y envío por email del informe de mercado."""
from __future__ import annotations

from flask import Blueprint, Response, jsonify, request

from app.core.email import EmailError, send_email
from app.informes import report

bp = Blueprint("informes_api", __name__, url_prefix="/api")


@bp.post("/email/send-assets-report")
def send_assets_report():
    """Genera el informe de activos y lo envía por email vía Resend.

    Body JSON: {"to": "destino@ejemplo.com", "watchlists": ["overview"]}
    (``watchlists`` es opcional; por defecto se incluyen todas).
    """
    data = request.get_json(silent=True) or {}
    to = data.get("to")
    if not to:
        return jsonify({"error": "Indica el destinatario en 'to'"}), 400

    try:
        market_report = report.build_market_report(_parse_slugs(data.get("watchlists")))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

    try:
        email_id = send_email(to, market_report.subject, market_report.html, attachments=market_report.attachments)
    except EmailError as exc:
        return jsonify({"error": str(exc)}), 502

    return jsonify({"id": email_id, "subject": market_report.subject}), 200


def _parse_slugs(raw: str | list[str] | None) -> list[str] | None:
    if isinstance(raw, str):
        raw = raw.split(",")
    slugs = [s.strip() for s in raw or [] if s.strip()]
    return slugs or None


@bp.get("/report/preview")
def report_preview():
    """Vista previa en el navegador del informe HTML que se enviaría por email.

    ?watchlists=overview,gaming-multimedia (opcional; por defecto, todas)
    """
    try:
        market_report = report.build_market_report(_parse_slugs(request.args.get("watchlists")))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    # En el navegador no existen los adjuntos ``cid:``: se sirve la versión
    # con los gráficos embebidos.
    return Response(market_report.preview_html, mimetype="text/html")


@bp.post("/report/send")
def report_send():
    """Genera el informe de mercado y lo envía por email vía Resend.

    Body JSON: {"to": "destino@ejemplo.com", "watchlists": ["overview"]}
    (``watchlists`` es opcional; por defecto se incluyen todas).
    """
    data = request.get_json(silent=True) or {}
    to = data.get("to")
    if not to:
        return jsonify({"error": "Indica el destinatario en 'to'"}), 400

    try:
        email_id = report.send_market_report(to, _parse_slugs(data.get("watchlists")))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except EmailError as exc:
        return jsonify({"error": str(exc)}), 502

    return jsonify({"id": email_id}), 200

"""Modelo del informe de mercado: resumen HTML de las watchlists listo para email.

Reúne las cotizaciones de ``market_data`` para los símbolos registrados en
``watchlists`` y las renderiza con una plantilla Jinja2 pensada para clientes
de correo (tablas y estilos en línea). Cada watchlist lleva además un gráfico
PNG (``report_charts``): en el email viaja como imagen adjunta en línea
(``cid:``) y en la vista previa del navegador, embebido en base64. Como el resto de modelos, no depende
de Flask: usa Jinja2 directamente, así que puede llamarse desde un script o
una tarea programada sin contexto de aplicación.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models import market_data, report_charts
from app.models.email import send_email
from app.models.market_data import Quote
from app.models.watchlists import WATCHLISTS, Symbol, Watchlist, get_watchlist
from config import Config

TOP_MOVERS = 3

_env = Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parent.parent / "views" / "emails"),
    autoescape=select_autoescape(["html"]),
)


@dataclass(slots=True)
class ReportRow:
    """Una fila del informe: el símbolo de la watchlist y su cotización."""

    symbol: Symbol
    quote: Quote


@dataclass(slots=True)
class ReportChart:
    """Gráfico PNG de una sección, referenciable en el email por su Content-ID."""

    content_id: str
    filename: str
    png: bytes

    @property
    def data_uri(self) -> str:
        return "data:image/png;base64," + base64.b64encode(self.png).decode("ascii")

    def to_attachment(self) -> dict:
        """Adjunto en línea en el formato que espera Resend."""
        return {
            "filename": self.filename,
            "content": base64.b64encode(self.png).decode("ascii"),
            "content_type": "image/png",
            "content_id": self.content_id,
        }


@dataclass(slots=True)
class ReportSection:
    watchlist: Watchlist
    rows: list[ReportRow]
    chart: ReportChart | None = None


@dataclass(slots=True)
class MarketReport:
    """Informe listo para enviar.

    ``html`` es el cuerpo del email (los gráficos apuntan a ``cid:`` y viajan
    en ``attachments``); ``preview_html`` es el mismo informe con los
    gráficos embebidos, para verlo en el navegador.
    """

    subject: str
    html: str
    generated_at: datetime
    sections: list[ReportSection]
    preview_html: str = ""
    charts: list[ReportChart] = field(default_factory=list)

    @property
    def attachments(self) -> list[dict]:
        return [chart.to_attachment() for chart in self.charts]


def _fetch_quote(ticker: str) -> Quote:
    """Como ``market_data.get_quote`` pero sin romper el informe si un símbolo falla."""
    try:
        return market_data.get_quote(ticker)
    except Exception:
        return Quote(symbol=ticker, name=ticker, price=None, previous_close=None, change=None, change_percent=None)


def _resolve_watchlists(slugs: list[str] | None) -> list[Watchlist]:
    if not slugs:
        return list(WATCHLISTS)
    watchlists = []
    for slug in slugs:
        watchlist = get_watchlist(slug)
        if watchlist is None:
            raise ValueError(f"Watchlist no encontrada: {slug}")
        watchlists.append(watchlist)
    return watchlists


def _format_price(value: float | None) -> str:
    return "—" if value is None else f"{value:,.2f}"


def _format_change(value: float | None, suffix: str = "") -> str:
    return "—" if value is None else f"{value:+,.2f}{suffix}"


_env.filters["price"] = _format_price
_env.filters["change"] = _format_change


def _build_chart(watchlist: Watchlist) -> ReportChart | None:
    """Gráfico de la watchlist; el informe se envía igual si no se puede generar."""
    try:
        png = report_charts.render_watchlist_performance(watchlist)
    except Exception:
        return None
    if png is None:
        return None
    return ReportChart(content_id=f"chart-{watchlist.slug}", filename=f"grafico-{watchlist.slug}.png", png=png)


def build_market_report(slugs: list[str] | None = None) -> MarketReport:
    """Obtiene las cotizaciones y construye el informe HTML.

    ``slugs`` limita el informe a esas watchlists (por defecto, todas). Lanza
    ``ValueError`` si algún slug no existe.
    """
    watchlists = _resolve_watchlists(slugs)
    generated_at = datetime.now(timezone.utc)

    sections = [
        ReportSection(
            watchlist=watchlist,
            rows=[ReportRow(symbol=s, quote=_fetch_quote(s.ticker)) for s in watchlist.symbols],
            chart=_build_chart(watchlist),
        )
        for watchlist in watchlists
    ]

    # Un mismo ticker puede aparecer en varias watchlists (p. ej. SONY): en el
    # resumen global se cuenta una sola vez.
    unique_rows = list({row.symbol.ticker: row for section in sections for row in section.rows}.values())
    with_change = sorted(
        (row for row in unique_rows if row.quote.change_percent is not None),
        key=lambda row: row.quote.change_percent,
        reverse=True,
    )
    gainers = [row for row in with_change if row.quote.change_percent > 0][:TOP_MOVERS]
    losers = [row for row in reversed(with_change) if row.quote.change_percent < 0][:TOP_MOVERS]

    summary = {
        "total": len(unique_rows),
        "up": sum(1 for row in with_change if row.quote.change_percent > 0),
        "down": sum(1 for row in with_change if row.quote.change_percent < 0),
        "unavailable": len(unique_rows) - len(with_change),
    }

    subject = f"{Config.SITE_NAME} · Informe de mercado · {generated_at:%d/%m/%Y}"
    template = _env.get_template("market_report.html")
    context = dict(
        subject=subject,
        site_name=Config.SITE_NAME,
        generated_at=generated_at,
        sections=sections,
        summary=summary,
        gainers=gainers,
        losers=losers,
    )
    html = template.render(**context, chart_src=lambda chart: f"cid:{chart.content_id}")
    preview_html = template.render(**context, chart_src=lambda chart: chart.data_uri)
    return MarketReport(
        subject=subject,
        html=html,
        generated_at=generated_at,
        sections=sections,
        preview_html=preview_html,
        charts=[section.chart for section in sections if section.chart is not None],
    )


def send_market_report(to: str | list[str], slugs: list[str] | None = None) -> str:
    """Construye el informe y lo envía por email. Devuelve el id del envío de Resend."""
    report = build_market_report(slugs)
    return send_email(to, report.subject, report.html, attachments=report.attachments)

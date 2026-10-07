"""Gráficos del informe de mercado: rendimiento reciente de cada watchlist.

Genera un PNG por watchlist con la variación acumulada (%) de cada símbolo
desde el inicio del periodo. Se usa porcentaje y no precio porque en una
misma watchlist conviven escalas muy distintas (p. ej. el Dow Jones y el
EUR/USD). Como ``report``, no depende de Flask.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone

import matplotlib

matplotlib.use("Agg")  # backend sin display: obligatorio en un servidor

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from app.core import market_data
from app.core.charts import DOWN, INK, MPL_RC, MUTED, PALETTE, UP
from app.core.watchlists import Watchlist

CHART_RANGE = "1mo"
CHART_INTERVAL = "1d"

# Colores de marca comunes (core.charts): las series siguen PALETTE (rojo,
# negro, grises) y el tema claro sale de MPL_RC. Encima, unos ajustes propios
# del gráfico pequeño del email. Se aplican con rc_context, así que no se
# hereda ni se modifica el estado global de matplotlib.
_STYLE = {
    **MPL_RC,
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.labelcolor": MUTED,
    "grid.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
}


def _fetch_closes(ticker: str) -> list[tuple[datetime, float]]:
    """Cierres del periodo del gráfico; lista vacía si Yahoo Finance falla."""
    try:
        candles = market_data.get_candles(ticker, CHART_RANGE, CHART_INTERVAL)
    except Exception:
        return []
    return [(datetime.fromtimestamp(c["time"], tz=timezone.utc), c["close"]) for c in candles]


def render_watchlist_performance(watchlist: Watchlist) -> bytes | None:
    """PNG con la variación acumulada de cada símbolo de ``watchlist`` en el
    último mes. Devuelve ``None`` si ningún símbolo tiene datos suficientes.
    """
    series = []
    for symbol in watchlist.symbols:
        closes = _fetch_closes(symbol.ticker)
        if len(closes) < 2 or not closes[0][1]:
            continue
        base = closes[0][1]
        series.append((symbol.display_name, [d for d, _ in closes], [(c / base - 1) * 100 for _, c in closes]))

    if not series:
        return None

    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(6.4, 3.3), dpi=150)
        try:
            for i, (name, dates, pct) in enumerate(series):
                color = PALETTE[i % len(PALETTE)]
                # La segunda mitad de PALETTE repite tonos parecidos (rojos,
                # grises): va discontinua para distinguirla en la leyenda.
                linestyle = "-" if i % len(PALETTE) < 3 else (0, (4, 1.5))
                ax.plot(
                    dates, pct, color=color, linewidth=1.6, linestyle=linestyle, label=f"{name}  {pct[-1]:+.1f}%"
                )
                # El punto final marca con UP/DOWN si el mes acaba en positivo o no.
                ax.scatter(dates[-1], pct[-1], color=UP if pct[-1] >= 0 else DOWN, s=14, zorder=3)

            ax.axhline(0, color=MUTED, linewidth=0.8, linestyle="--")
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0f}%"))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
            ax.set_title(
                f"{watchlist.name} · variación en el último mes",
                loc="left",
                fontsize=10,
                fontweight="bold",
                color=INK,
            )
            ax.legend(
                loc="upper left",
                bbox_to_anchor=(1.01, 1),
                frameon=False,
                fontsize=8,
                labelcolor=INK,
                handlelength=2,
            )
            fig.tight_layout()

            buffer = io.BytesIO()
            fig.savefig(buffer, format="png")
            return buffer.getvalue()
        finally:
            plt.close(fig)

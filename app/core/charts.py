"""Paleta y estilo comunes de las gráficas que se generan en el servidor
(matplotlib/seaborn), con los colores de la marca MOAINVEST: blancos, rojos y
negros, igual que core/static/css/style.css y el sitio rojo."""
from __future__ import annotations

from cycler import cycler

BRAND = "#c8102e"
BRAND_DEEP = "#8f1025"
BRAND_BRIGHT = "#ff5a6e"
INK = "#171717"
MUTED = "#6b6b6b"
LINE = "#e6e4df"
PAPER = "#ffffff"
UP = "#0f8a5f"
DOWN = BRAND

# Orden de las series: rojo de marca, negro y grises/rojos secundarios.
PALETTE = [BRAND, INK, MUTED, BRAND_DEEP, BRAND_BRIGHT, "#a3a3a3"]

# rcParams de matplotlib para un tema claro coherente con la app: fondo blanco,
# texto negro, rejilla suave. Úsalo con ``matplotlib.rcParams.update(MPL_RC)``
# o ``with matplotlib.rc_context(MPL_RC):``; con seaborn,
# ``sns.set_theme(style="whitegrid", rc=MPL_RC)``.
MPL_RC = {
    "figure.facecolor": PAPER,
    "axes.facecolor": PAPER,
    "savefig.facecolor": PAPER,
    "axes.edgecolor": LINE,
    "axes.labelcolor": INK,
    "axes.titlecolor": INK,
    "axes.titleweight": "semibold",
    "axes.grid": True,
    "grid.color": LINE,
    "grid.linewidth": 0.8,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "text.color": INK,
    "legend.frameon": False,
    "axes.prop_cycle": cycler(color=PALETTE),
}

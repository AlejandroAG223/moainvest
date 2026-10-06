"""Blueprint de "core": no tiene páginas propias.

Aporta a las demás apps el layout con sidebar (``core/base.html``), el sidebar,
los iconos (``core/icons.html``), los estáticos comunes (``core.static``) y las
variables globales de las plantillas.
"""
from __future__ import annotations

from flask import Blueprint, current_app

from app.core.navigation import APPS

bp = Blueprint(
    "core",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/core",
)


@bp.app_context_processor
def inject_globals() -> dict:
    return {
        # Entradas del sidebar (core/sidebar.html).
        "apps": APPS,
        # Nombre de la marca para títulos y sidebar (ver Config.SITE_NAME).
        "site_name": current_app.config["SITE_NAME"],
    }

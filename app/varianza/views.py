"""Controlador de la app "Análisis de Varianza".

De momento es una página en blanco (placeholder); el contenido real se
añadirá más adelante.
"""
from __future__ import annotations

from flask import Blueprint, render_template

from app.core.navigation import get_app

bp = Blueprint(
    "varianza",
    __name__,
    url_prefix="/app/analisis-varianza",
    template_folder="templates",
    static_folder="static",
)


@bp.get("/")
def index():
    return render_template("varianza/index.html", active_app=get_app("analisis-varianza"))

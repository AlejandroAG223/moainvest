"""Application factory.

Este es el punto de ensamblaje del patrón MVC: crea la app Flask, le aplica
la configuración y registra los controladores (blueprints). Los modelos y
las vistas no se importan aquí directamente, solo a través de los
controladores, para mantener las capas desacopladas.
"""
from __future__ import annotations

from flask import Flask

from config import Config

# Versión del binario de Tailwind con la que se compila static/moainvest/moainvest.css.
TAILWINDCSS_VERSION = "v4.3.3"


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(
        __name__,
        template_folder="views",  # nombramos "views" (no "templates") para reflejar el MVC
        static_folder="static",
    )
    app.config.from_object(config_class)

    register_blueprints(app)
    register_context_processors(app)
    register_commands(app)

    return app


def register_blueprints(app: Flask) -> None:
    """Registra cada controlador.

    Añadir una nueva app de primer nivel (otra entrada en el sidebar) implica:
    registrar su entrada en ``app.models.apps.APPS`` y su blueprint aquí.
    """
    from app.controllers.api import bp as api_bp
    from app.controllers.informes import bp as informes_bp
    from app.controllers.moainvest import bp as moainvest_bp
    from app.controllers.quant_stats import bp as quant_stats_bp
    from app.controllers.varianza import bp as varianza_bp

    app.register_blueprint(varianza_bp)
    app.register_blueprint(quant_stats_bp)
    app.register_blueprint(informes_bp)
    app.register_blueprint(moainvest_bp)
    app.register_blueprint(api_bp)


def register_context_processors(app: Flask) -> None:
    from app.models.apps import APPS

    @app.context_processor
    def inject_apps() -> dict:
        # Disponible en todas las plantillas (el sidebar se incluye en base.html).
        return {"apps": APPS}

    @app.context_processor
    def inject_site_name() -> dict:
        # Nombre de la marca para títulos y sidebar (ver Config.SITE_NAME).
        return {"site_name": app.config["SITE_NAME"]}


def register_commands(app: Flask) -> None:
    import click

    @app.cli.command("cloudinary-upload")
    def cloudinary_upload() -> None:
        """Sube a Cloudinary las imágenes de la página de Informes."""
        from app.models.media import MediaError, upload_informes_images

        try:
            urls = upload_informes_images()
        except MediaError as exc:
            raise click.ClickException(str(exc)) from exc
        for url in urls:
            click.echo(url)

    @app.cli.command("build-css")
    @click.option("--watch", is_flag=True, help="Recompila al cambiar las plantillas o el JS.")
    def build_css(watch: bool) -> None:
        """Compila el CSS de Tailwind del sitio MOAINVEST (sin Node).

        Usa el binario standalone de Tailwind que instala ``pytailwindcss``
        (dependencia de desarrollo de uv) en la versión fijada abajo.
        """
        import os
        import shutil
        import subprocess
        from pathlib import Path

        binary = shutil.which("tailwindcss")
        if binary is None:
            raise click.ClickException("No se encuentra tailwindcss: ejecuta `uv sync` (instala pytailwindcss).")
        static = Path(app.static_folder) / "moainvest"
        args = [binary, "-i", str(static / "src" / "moainvest.css"), "-o", str(static / "moainvest.css")]
        args.append("--watch" if watch else "--minify")
        env = {**os.environ, "TAILWINDCSS_VERSION": TAILWINDCSS_VERSION}
        raise SystemExit(subprocess.run(args, env=env, check=False).returncode)

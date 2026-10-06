"""Comandos de ``flask`` de la app "Informes"."""
from __future__ import annotations

import click
from flask import Flask


def register(app: Flask) -> None:
    @app.cli.command("cloudinary-upload")
    def cloudinary_upload() -> None:
        """Sube a Cloudinary las imágenes de la página de Informes."""
        from app.informes.media import MediaError, upload_informes_images

        try:
            urls = upload_informes_images()
        except MediaError as exc:
            raise click.ClickException(str(exc)) from exc
        for url in urls:
            click.echo(url)

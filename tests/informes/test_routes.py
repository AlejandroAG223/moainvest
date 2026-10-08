"""Rutas de la app "Informes" (página y API de vista previa y envío)."""
from app.core.watchlists import WATCHLISTS
from tests.factories import fake_quote


def test_api_report_preview_returns_html(client, monkeypatch):
    monkeypatch.setattr("app.informes.report.market_data.get_quote", fake_quote)
    response = client.get("/api/report/preview?watchlists=overview")
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"Informe de mercado" in response.data
    assert b"MoaiInvest" in response.data
    # En el navegador no hay adjuntos: los gráficos van embebidos.
    assert b'src="data:image/png;base64,' in response.data
    assert b"cid:" not in response.data


def test_api_report_preview_unknown_watchlist_is_404(client):
    assert client.get("/api/report/preview?watchlists=no-existe").status_code == 404


def test_api_report_send_requires_to(client):
    assert client.post("/api/report/send", json={}).status_code == 400


def test_api_report_send_returns_id(client, monkeypatch):
    calls = []

    def _send(to, slugs):
        calls.append((to, slugs))
        return "email-456"

    monkeypatch.setattr("app.informes.api.report.send_market_report", _send)
    response = client.post("/api/report/send", json={"to": "test@example.com", "watchlists": ["overview"]})
    assert response.status_code == 200
    assert response.get_json() == {"id": "email-456"}
    assert calls == [("test@example.com", ["overview"])]


def test_api_send_assets_report_requires_to(client):
    assert client.post("/api/email/send-assets-report", json={}).status_code == 400


def test_api_send_assets_report_unknown_watchlist_is_404(client):
    response = client.post(
        "/api/email/send-assets-report", json={"to": "test@example.com", "watchlists": ["no-existe"]}
    )
    assert response.status_code == 404


def test_api_send_assets_report_sends_report_html(client, monkeypatch):
    sent = {}

    def _send(to, subject, html, attachments=None):
        sent.update(to=to, subject=subject, html=html, attachments=attachments)
        return "email-789"

    monkeypatch.setattr("app.informes.report.market_data.get_quote", fake_quote)
    monkeypatch.setattr("app.informes.api.send_email", _send)
    response = client.post(
        "/api/email/send-assets-report", json={"to": "test@example.com", "watchlists": ["overview"]}
    )
    assert response.status_code == 200
    assert response.get_json()["id"] == "email-789"
    assert sent["to"] == "test@example.com"
    assert sent["subject"].startswith("MoaiInvest · Informe de mercado")
    assert "Resumen" in sent["html"]
    # El gráfico de la watchlist viaja como imagen en línea referenciada por cid.
    assert 'src="cid:chart-overview"' in sent["html"]
    assert [a["content_id"] for a in sent["attachments"]] == ["chart-overview"]


def test_api_send_assets_report_reports_provider_errors(client, monkeypatch):
    from app.core.email import EmailError

    def _raise(to, subject, html, attachments=None):
        raise EmailError("Falta RESEND_API_KEY en el .env")

    monkeypatch.setattr("app.informes.report.market_data.get_quote", fake_quote)
    monkeypatch.setattr("app.informes.api.send_email", _raise)
    response = client.post("/api/email/send-assets-report", json={"to": "test@example.com"})
    assert response.status_code == 502
    assert "error" in response.get_json()


def test_informes_page_has_preview_and_send_buttons(client):
    response = client.get("/app/informes/")
    assert response.status_code == 200
    assert b'id="preview-btn"' in response.data
    assert b'id="send-btn"' in response.data
    for watchlist in WATCHLISTS:
        assert f'value="{watchlist.slug}"'.encode() in response.data


def test_informes_page_has_background_fx_layers(client):
    response = client.get("/app/informes/")
    for scene in ("charts", "stats", "sports"):
        # Video en bucle si existe static/video/informes-<escena>.mp4; si no, canvas.
        assert f"fx-layer--{scene}".encode() in response.data
        assert (
            f"video/informes-{scene}.mp4".encode() in response.data
            or f'data-fx-scene="{scene}"'.encode() in response.data
        )
    assert b'aria-hidden="true"' in response.data


def test_informes_page_uses_local_images_without_cloudinary(client, monkeypatch):
    from config import Config

    monkeypatch.setattr(Config, "CLOUDINARY_URL", "")
    response = client.get("/app/informes/")
    assert b"/static/img/informes/charts.jpg" in response.data
    assert b"res.cloudinary.com" not in response.data


def test_informes_page_uses_cloudinary_images_when_configured(client, monkeypatch):
    from config import Config

    monkeypatch.setattr(Config, "CLOUDINARY_URL", "cloudinary://123456:secreto@demo")
    response = client.get("/app/informes/")
    assert b"https://res.cloudinary.com/demo/image/upload/" in response.data
    assert b"f_auto" in response.data and b"q_auto" in response.data
    assert b"srcset=" in response.data


def test_informes_page_uses_inline_svg_icons_instead_of_emojis(client):
    response = client.get("/app/informes/")
    html = response.data.decode()
    content = html[html.index('id="informes-page"'):]
    # Iconos de línea inline que heredan el color y son decorativos.
    for name in ("file-text", "layers", "chart-column", "smartphone", "gamepad", "eye", "send", "mail"):
        assert f"ui-icon--{name}" in content
    for svg in content.split("<svg")[1:]:
        tag = svg[: svg.index(">")]
        assert 'stroke="currentColor"' in tag
        assert 'aria-hidden="true"' in tag
    # Ningún emoji de watchlist dentro del contenido de la página.
    for watchlist in WATCHLISTS:
        assert watchlist.icon not in content


def test_informes_page_uses_brand_layout(client):
    html = client.get("/app/informes/").data
    for marker in (b'class="informes-hero', b'class="informes-eyebrow"', b"informes-btn", b'id="informes-preview-empty"'):
        assert marker in html
    # Pasos del flujo, como en /informe del sitio rojo.
    for step in ("01 · Watchlists incluidas", "02 · Revisa", "03 · Envía por correo"):
        assert step.encode() in html


def test_report_preview_uses_brand_colors(client, monkeypatch):
    monkeypatch.setattr("app.informes.report.market_data.get_quote", fake_quote)
    html = client.get("/api/report/preview?watchlists=overview").data
    assert b"background:#171717" in html  # cabecera negra
    assert b"#c8102e" in html  # rojo de marca
    # Nada de la paleta azul anterior.
    for old in (b"#2962ff", b"#131722", b"#f0f3fa", b"#089981", b"#f23645"):
        assert old not in html

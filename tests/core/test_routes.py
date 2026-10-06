"""Rutas de "core": API común (precios, velas, watchlists, email) y layout con sidebar."""
import re

import pytest

from app.core.watchlists import WATCHLISTS
from tests.factories import fake_quote


def test_pages_show_site_name(client, app):
    site_name = app.config["SITE_NAME"]
    assert site_name == "MoaiInvest"
    page = client.get("/analisis-varianza/").get_data(as_text=True)
    assert f"· {site_name}</title>" in page
    assert f'<span class="sidebar__title">{site_name}</span>' in page
    assert "Market Dashboard" not in page


def test_api_quote(client, monkeypatch):
    monkeypatch.setattr("app.core.api.market_data.get_quote", fake_quote)
    response = client.get("/api/quote/AAPL")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["symbol"] == "AAPL"
    assert payload["is_up"] is True


def test_api_watchlists_lists_registry(client):
    response = client.get("/api/watchlists")
    assert response.status_code == 200
    payload = response.get_json()
    assert [w["slug"] for w in payload] == [w.slug for w in WATCHLISTS]
    first = WATCHLISTS[0]
    assert payload[0]["symbols"][0] == {"ticker": first.symbols[0].ticker, "name": first.symbols[0].display_name}


def test_api_candles_rejects_bad_params(client):
    response = client.get("/api/candles/AAPL?range=bogus&interval=1d")
    assert response.status_code == 400


def test_api_email_send_requires_to(client):
    response = client.post("/api/email/send", json={})
    assert response.status_code == 400


def test_api_email_send_returns_id(client, monkeypatch):
    monkeypatch.setattr(
        "app.core.api.send_email",
        lambda to, subject, html: "email-123",
    )
    response = client.post("/api/email/send", json={"to": "test@example.com"})
    assert response.status_code == 200
    assert response.get_json() == {"id": "email-123"}


def test_api_email_send_default_subject_uses_site_name(client, monkeypatch):
    sent = {}
    monkeypatch.setattr(
        "app.core.api.send_email",
        lambda to, subject, html: sent.update(subject=subject, html=html) or "email-123",
    )
    client.post("/api/email/send", json={"to": "test@example.com"})
    assert sent["subject"] == "Prueba de MoaiInvest"
    assert "MoaiInvest" in sent["html"]


def test_api_email_send_reports_provider_errors(client, monkeypatch):
    from app.core.email import EmailError

    def _raise(to, subject, html):
        raise EmailError("Falta RESEND_API_KEY en el .env")

    monkeypatch.setattr("app.core.api.send_email", _raise)
    response = client.post("/api/email/send", json={"to": "test@example.com"})
    assert response.status_code == 502
    assert "error" in response.get_json()


def _sidebar_link_names(html: str) -> list[str]:
    """Textos de los enlaces del sidebar: apps y subsecciones."""
    pattern = r'<span class="sidebar__(?:app|section)-name">([^<]*)</span>'
    return re.findall(pattern, html.split('<aside class="sidebar"', 1)[1].split("</aside>", 1)[0])


@pytest.mark.parametrize("url", ["/quant-stats/fundamentales", "/analisis-varianza/"])
def test_sidebar_links_use_sentence_case(client, fake_uec, url):
    names = _sidebar_link_names(client.get(url).data.decode())
    assert "Quant stats" in names and "Análisis de varianza" in names
    if url.startswith("/quant-stats"):
        assert {"Gráficas y fundamentales estadísticos", "Revisión analítica"} <= set(names)
    for name in names:
        assert name == name[:1].upper() + name[1:].lower(), name

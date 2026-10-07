"""Rutas de la app "Análisis de Varianza" (página y API de volatilidad)."""



def test_varianza_page_is_reachable(client):
    response = client.get("/app/analisis-varianza/")
    assert response.status_code == 200
    assert "Análisis de varianza · MoaiInvest".encode() in response.data
    assert b'id="ticker-input"' in response.data
    assert b'id="download-csv-btn"' in response.data


def test_varianza_page_has_brand_header_and_ticker_chips(client):
    html = client.get("/app/analisis-varianza/").data
    assert b'class="varianza-hero"' in html
    assert b'class="varianza-eyebrow"' in html
    assert b'class="varianza-accent"' in html
    # Campo de tickers con chips, límite de la API y sugerencias.
    assert b'id="tickers-chips"' in html
    assert b'id="tickers-input"' in html
    assert b'data-max-tickers="6"' in html
    assert b'data-ticker="AAPL"' in html


def test_api_volatility_chart_requires_tickers(client):
    response = client.get("/api/volatility-chart")
    assert response.status_code == 400


def test_api_volatility_chart_rejects_too_many_tickers(client):
    tickers = ",".join(f"T{i}" for i in range(10))
    response = client.get(f"/api/volatility-chart?tickers={tickers}")
    assert response.status_code == 400


def test_api_volatility_chart_returns_png(client, monkeypatch):
    monkeypatch.setattr(
        "app.varianza.api.analysis.render_volatility_histograms",
        lambda tickers, period: b"fake-png-bytes",
    )
    response = client.get("/api/volatility-chart?tickers=AAPL,MSFT")
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert response.data == b"fake-png-bytes"

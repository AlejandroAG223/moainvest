"""Rutas de la app "CAPM" (página y API de retornos esperados)."""
import datetime
from urllib.parse import quote

import pandas as pd

from app.capm import analysis


def test_capm_page_is_reachable(client):
    response = client.get("/app/capm/")
    assert response.status_code == 200
    assert "Retornos esperados (CAPM) · MoaiInvest".encode() in response.data
    assert b'id="capm-form"' in response.data
    assert b'id="sector-select"' in response.data


def test_capm_page_has_brand_header_and_sector_options(client):
    html = client.get("/app/capm/").data
    assert b'class="varianza-hero"' in html
    assert b'class="varianza-eyebrow"' in html
    assert b'class="varianza-accent"' in html
    for sector in analysis.SECTORS:
        # Jinja escapa "&" como entidad HTML (p. ej. "Oil &amp; Gas").
        assert sector.replace("&", "&amp;").encode() in html
    for market_label in analysis.MARKET_TICKERS:
        assert market_label.replace("&", "&amp;").encode() in html


def test_api_capm_table_rejects_invalid_sector(client):
    response = client.get("/api/capm-table?sector=Inexistente&market=SPY&year=2020")
    assert response.status_code == 400


def test_api_capm_table_rejects_invalid_market(client):
    sector = quote(next(iter(analysis.SECTORS)))
    response = client.get(f"/api/capm-table?sector={sector}&market=^GSPC&year=2020")
    assert response.status_code == 400


def test_api_capm_table_rejects_invalid_year(client):
    sector = quote(next(iter(analysis.SECTORS)))
    response = client.get(f"/api/capm-table?sector={sector}&market=SPY&year=1492")
    assert response.status_code == 400


def test_api_capm_table_returns_expected_json(client, monkeypatch):
    fake_table = pd.DataFrame(
        {
            "Beta": [1.2],
            analysis.EXPECTED_RETURN_COL: [0.085],
            "Tasa libre de riesgo": [0.04],
            "Desde": [datetime.date(2020, 1, 2)],
        },
        index=["XOM"],
    )
    monkeypatch.setattr(
        "app.capm.api.analysis.build_sector_capm_table",
        lambda sector, year, market: fake_table,
    )

    sector = quote(next(iter(analysis.SECTORS)))
    market = next(iter(analysis.MARKET_TICKERS.values()))
    response = client.get(f"/api/capm-table?sector={sector}&market={market}&year=2020")

    assert response.status_code == 200
    assert response.get_json() == {
        "rows": [
            {
                "ticker": "XOM",
                "beta": 1.2,
                "expected_return": 0.085,
                "risk_free_rate": 0.04,
                "since": "2020-01-02",
            }
        ],
        "risk_free_ticker": "^IRX",
    }


def test_api_capm_table_accepts_all_years(client, monkeypatch):
    fake_table = pd.DataFrame(
        columns=["Beta", analysis.EXPECTED_RETURN_COL, "Tasa libre de riesgo", "Desde"]
    )
    monkeypatch.setattr(
        "app.capm.api.analysis.build_sector_capm_table",
        lambda sector, year, market: fake_table,
    )

    sector = quote(next(iter(analysis.SECTORS)))
    market = next(iter(analysis.MARKET_TICKERS.values()))
    response = client.get(f"/api/capm-table?sector={sector}&market={market}&year={analysis.ALL_YEARS}")

    assert response.status_code == 200
    assert response.get_json() == {"rows": [], "risk_free_ticker": "^IRX"}

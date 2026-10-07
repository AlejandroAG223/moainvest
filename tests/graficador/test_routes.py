"""Rutas de la app "Graficador" y el contrato de datos que consume su JS."""
import re
from pathlib import Path

import pandas as pd
import pytest

from app.core import market_data
from app.core.api import ALLOWED_INTERVALS, ALLOWED_RANGES
from app.core.navigation import APPS
from app.core.watchlists import default_watchlist
from app.graficador.views import CHART_RANGES

ROOT = Path(__file__).resolve().parents[2]


def test_page_with_ticker(client):
    response = client.get("/app/graficador/?ticker=aapl")
    assert response.status_code == 200
    assert b'data-ticker="AAPL"' in response.data
    assert b'id="graficador-chart"' in response.data
    assert b'id="graficador-legend"' in response.data
    assert b"graficador.js" in response.data
    assert "Graficador · MoaiInvest".encode() in response.data
    # Selector de rangos y de tipo de serie.
    for label in ("1D", "5D", "1M", "6M", "1A", "5A", "Todo"):
        assert f">{label}</button>".encode() in response.data
    for series_type in ("candles", "line", "area"):
        assert f'data-series-type="{series_type}"'.encode() in response.data


def test_page_defaults_to_first_symbol_of_default_watchlist(client):
    ticker = default_watchlist().symbols[0].ticker
    response = client.get("/app/graficador/")
    assert response.status_code == 200
    assert f'data-ticker="{ticker}"'.encode() in response.data


@pytest.mark.parametrize("ticker", ["<script>", "AAPL MSFT", "X" * 21])
def test_invalid_ticker_shows_error(client, ticker):
    response = client.get("/app/graficador/", query_string={"ticker": ticker})
    assert response.status_code == 400
    assert b'id="graficador-error"' in response.data
    assert "no es un ticker válido".encode() in response.data
    assert b'data-ticker=""' in response.data
    assert b"graficador.js" not in response.data


def test_invalid_ticker_is_escaped(client):
    response = client.get("/app/graficador/", query_string={"ticker": "<script>"})
    assert b"<SCRIPT>" not in response.data
    assert b"&lt;SCRIPT&gt;" in response.data


def test_sidebar_marks_graficador_as_active(client):
    page = client.get("/app/graficador/").get_data(as_text=True)
    assert re.search(r'sidebar__app is-active">\s*<a class="sidebar__app-header" href="/app/graficador/"', page)


def test_graficador_replaces_graficas_in_sidebar():
    endpoints = [a.endpoint for a in APPS]
    assert "graficador.index" in endpoints
    assert "moainvest.graficas" not in endpoints


def test_chart_ranges_are_accepted_by_candles_api():
    for r in CHART_RANGES:
        assert r["range"] in ALLOWED_RANGES and r["interval"] in ALLOWED_INTERVALS


def test_candles_api_includes_volume(client, monkeypatch):
    market_data._cache.clear()
    index = pd.date_range("2026-01-01", periods=3, freq="D", tz="UTC")
    history = pd.DataFrame(
        {"Open": [1.0, 2.0, 3.0], "High": [2.0, 3.0, 4.0], "Low": [0.5, 1.5, 2.5], "Close": [1.5, 2.5, 3.5], "Volume": [10, 20, 30]},
        index=index,
    )

    class FakeTicker:
        def __init__(self, ticker):
            self.ticker = ticker

        def history(self, period, interval):
            return history

    monkeypatch.setattr("app.core.market_data.yf.Ticker", FakeTicker)
    response = client.get("/api/candles/AAPL?range=1mo&interval=1h")
    assert response.status_code == 200
    candles = response.get_json()
    assert [c["volume"] for c in candles] == [10, 20, 30]
    assert set(candles[0]) == {"time", "open", "high", "low", "close", "volume"}


def test_vendored_lightweight_charts_is_v5_and_js_uses_v5_api():
    vendor = ROOT / "app/core/static/js/vendor/lightweight-charts.standalone.production.js"
    assert "Lightweight Charts™ v5." in vendor.read_text(encoding="utf-8")[:300]
    v4_calls = re.compile(r"\.(addCandlestickSeries|addLineSeries|addAreaSeries|addHistogramSeries|addBarSeries|addBaselineSeries|setMarkers)\(")
    for js in (ROOT / "app").rglob("*.js"):
        if "vendor" in js.parts:
            continue
        assert not v4_calls.search(js.read_text(encoding="utf-8")), js

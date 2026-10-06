from datetime import datetime, timedelta, timezone

import pytest

from app import create_app
from config import TestingConfig


@pytest.fixture()
def app():
    return create_app(TestingConfig)


@pytest.fixture()
def client(app):
    return app.test_client()


def fake_closes(ticker):
    """Cierres deterministas (sube o baja según el ticker) para los gráficos del informe."""
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    step = 1 if len(ticker) % 2 else -1
    return [(start + timedelta(days=i), 100.0 + step * i) for i in range(20)]


@pytest.fixture(autouse=True)
def no_network_report_charts(monkeypatch):
    # El informe genera un gráfico por watchlist: en los tests nunca se
    # descarga nada de Yahoo Finance.
    monkeypatch.setattr("app.informes.report_charts._fetch_closes", fake_closes)


@pytest.fixture
def fake_uec(monkeypatch):
    from tests.quant_stats.test_quant import _fake_candles, _fake_earnings

    # El benchmark necesita datos distintos: quantstats cachea resampleos por contenido.
    monkeypatch.setattr(
        "app.quant_stats.quant.market_data.get_candles",
        lambda ticker, **k: _fake_candles(400 if ticker != "UEC" else 420),
    )
    monkeypatch.setattr("app.quant_stats.quant.market_data.get_earnings", lambda *a, **k: _fake_earnings())
    monkeypatch.setattr("app.quant_stats.quant.market_data.get_display_name", lambda ticker: f"Nombre {ticker}")

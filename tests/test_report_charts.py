from datetime import datetime, timedelta, timezone

from app.models import report_charts
from app.models.watchlists import get_watchlist

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# Referencia a la función real, tomada antes de que el fixture autouse del
# conftest la sustituya por datos falsos.
REAL_FETCH_CLOSES = report_charts._fetch_closes


def _closes(n=10):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [(start + timedelta(days=i), 50.0 + i) for i in range(n)]


def test_render_watchlist_performance_returns_png():
    png = report_charts.render_watchlist_performance(get_watchlist("overview"))
    assert png is not None and png.startswith(PNG_SIGNATURE)


def test_render_watchlist_performance_without_data_returns_none(monkeypatch):
    monkeypatch.setattr("app.models.report_charts._fetch_closes", lambda ticker: [])
    assert report_charts.render_watchlist_performance(get_watchlist("overview")) is None


def test_render_watchlist_performance_skips_symbols_without_data(monkeypatch):
    monkeypatch.setattr("app.models.report_charts._fetch_closes", lambda t: _closes() if t == "AAPL" else [])
    png = report_charts.render_watchlist_performance(get_watchlist("consumer-electronics"))
    assert png is not None and png.startswith(PNG_SIGNATURE)


def test_fetch_closes_converts_candles(monkeypatch):
    candles = [{"time": 1767225600, "close": 10.0}, {"time": 1767312000, "close": 11.0}]
    monkeypatch.setattr("app.models.report_charts.market_data.get_candles", lambda *a, **k: candles)
    closes = REAL_FETCH_CLOSES("AAPL")
    assert [c for _, c in closes] == [10.0, 11.0]
    assert closes[0][0] == datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_fetch_closes_tolerates_provider_errors(monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("yahoo caído")

    monkeypatch.setattr("app.models.report_charts.market_data.get_candles", _boom)
    assert REAL_FETCH_CLOSES("AAPL") == []

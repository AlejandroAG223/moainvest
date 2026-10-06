import base64

import pytest

from app.informes import report
from app.core.market_data import Quote
from app.core.watchlists import WATCHLISTS

CHANGES = {"AAPL": 2.5, "SONY": -1.2, "MSFT": 0.8}


def _fake_quote(ticker):
    pct = CHANGES.get(ticker)
    if pct is None:
        return Quote(ticker, ticker, None, None, None, None)
    return Quote(ticker, ticker, 100.0, 100.0, pct, pct, currency="USD")


@pytest.fixture(autouse=True)
def fake_quotes(monkeypatch):
    monkeypatch.setattr("app.informes.report.market_data.get_quote", _fake_quote)


def test_build_market_report_includes_all_watchlists_by_default():
    market_report = report.build_market_report()
    assert [s.watchlist.slug for s in market_report.sections] == [w.slug for w in WATCHLISTS]
    assert market_report.subject.startswith("MoaiInvest · Informe de mercado")
    assert "MoaiInvest" in market_report.html
    for watchlist in WATCHLISTS:
        assert watchlist.name in market_report.html


def test_build_market_report_formats_changes_and_missing_data():
    html = report.build_market_report(["consumer-electronics"]).html
    assert "+2.50%" in html
    assert "-1.20%" in html
    assert "—" in html  # símbolos sin datos (p. ej. HPQ)
    assert "sin datos disponibles" in html


def test_build_market_report_filters_and_validates_slugs():
    market_report = report.build_market_report(["gaming-multimedia"])
    assert [s.watchlist.slug for s in market_report.sections] == ["gaming-multimedia"]
    with pytest.raises(ValueError):
        report.build_market_report(["no-existe"])


def test_build_market_report_survives_failing_quote(monkeypatch):
    def _boom(ticker):
        raise RuntimeError("yahoo caído")

    monkeypatch.setattr("app.informes.report.market_data.get_quote", _boom)
    market_report = report.build_market_report(["overview"])
    assert all(row.quote.price is None for row in market_report.sections[0].rows)


def test_build_market_report_escapes_html(monkeypatch):
    monkeypatch.setattr(
        "app.informes.report.market_data.get_quote",
        lambda t: Quote(t, t, 1.0, 1.0, 0.0, 0.0, currency="<b>X</b>"),
    )
    html = report.build_market_report(["overview"]).html
    assert "<b>X</b>" not in html
    assert "&lt;b&gt;X&lt;/b&gt;" in html


def test_send_market_report_sends_built_html(monkeypatch):
    sent = {}

    def _send(to, subject, html, attachments=None):
        sent.update(to=to, subject=subject, html=html, attachments=attachments)
        return "email-1"

    monkeypatch.setattr("app.informes.report.send_email", _send)
    assert report.send_market_report("a@example.com", ["overview"]) == "email-1"
    assert sent["to"] == "a@example.com"
    assert sent["subject"].startswith("MoaiInvest · Informe de mercado")
    assert "<html" in sent["html"]
    assert [a["filename"] for a in sent["attachments"]] == ["grafico-overview.png"]


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def test_build_market_report_adds_one_chart_per_watchlist():
    market_report = report.build_market_report(["overview", "gaming-multimedia"])
    assert [c.content_id for c in market_report.charts] == ["chart-overview", "chart-gaming-multimedia"]
    assert all(c.png.startswith(PNG_SIGNATURE) for c in market_report.charts)
    assert 'src="cid:chart-overview"' in market_report.html
    assert "data:image/png;base64," not in market_report.html
    assert 'src="data:image/png;base64,' in market_report.preview_html
    assert "cid:" not in market_report.preview_html


def test_report_attachments_use_resend_inline_format():
    attachment = report.build_market_report(["overview"]).attachments[0]
    assert attachment["content_id"] == "chart-overview"
    assert attachment["filename"] == "grafico-overview.png"
    assert attachment["content_type"] == "image/png"
    assert base64.b64decode(attachment["content"]).startswith(PNG_SIGNATURE)


def test_build_market_report_survives_chart_errors(monkeypatch):
    def _boom(watchlist):
        raise RuntimeError("matplotlib roto")

    monkeypatch.setattr("app.informes.report.report_charts.render_watchlist_performance", _boom)
    market_report = report.build_market_report(["overview"])
    assert market_report.charts == []
    assert "cid:" not in market_report.html
    assert "S&amp;P 500" in market_report.html

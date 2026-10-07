import datetime

from app.varianza import analysis


def _fake_candles():
    """~2 meses de precios diarios sintéticos (sin llamar a Yahoo Finance)."""
    candles = []
    price = 100.0
    date = datetime.datetime(2024, 1, 1)
    for i in range(60):
        date += datetime.timedelta(days=1)
        if date.weekday() >= 5:  # fin de semana: sin sesión
            continue
        price *= 1 + (0.01 if i % 2 == 0 else -0.008)
        candles.append(
            {
                "time": int(date.timestamp()),
                "open": price,
                "high": price * 1.01,
                "low": price * 0.99,
                "close": price,
                "volume": 1000,
            }
        )
    return candles


def test_monthly_volatility_groups_by_year_month(monkeypatch):
    monkeypatch.setattr(analysis.market_data, "get_candles", lambda *a, **k: _fake_candles())
    volatility = analysis.monthly_volatility("FAKE")
    assert not volatility.empty
    assert volatility.index.is_unique
    assert all(v >= 0 for v in volatility.values)


def test_monthly_volatility_empty_when_no_candles(monkeypatch):
    monkeypatch.setattr(analysis.market_data, "get_candles", lambda *a, **k: [])
    assert analysis.monthly_volatility("FAKE").empty


def test_render_volatility_histograms_returns_png_bytes(monkeypatch):
    monkeypatch.setattr(analysis.market_data, "get_candles", lambda *a, **k: _fake_candles())
    png_bytes = analysis.render_volatility_histograms(["FAKE", "OTRO"])
    assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")


def test_render_volatility_histograms_uses_core_palette_without_global_theme(monkeypatch):
    import matplotlib
    from matplotlib.colors import to_hex

    from app.core.charts import PALETTE, PAPER

    monkeypatch.setattr(analysis.market_data, "get_candles", lambda *a, **k: _fake_candles())
    figures = []
    real_close = analysis.plt.close
    monkeypatch.setattr(analysis.plt, "close", lambda fig: (figures.append(fig), real_close(fig)))
    before = dict(matplotlib.rcParams)

    analysis.render_volatility_histograms(["FAKE", "OTRO"])

    fig = figures[0]
    assert to_hex(fig.get_facecolor()) == PAPER
    for i, ax in enumerate(fig.axes[:2]):
        assert to_hex(ax.get_facecolor()) == PAPER
        assert {to_hex(p.get_facecolor(), keep_alpha=False) for p in ax.patches} == {PALETTE[i]}
    # El tema se aplica con rc_context: el estado global queda como estaba.
    assert dict(matplotlib.rcParams) == before

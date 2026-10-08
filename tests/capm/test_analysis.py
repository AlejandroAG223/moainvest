import numpy as np
import pandas as pd
import pytest

from app.capm import analysis

TODAY = pd.Timestamp("2026-09-30")


def make_prices(returns: pd.Series, start: float = 100.0) -> pd.Series:
    """Serie de precios cuyo pct_change reproduce exactamente `returns`."""
    return start * (1 + returns).cumprod()


def make_candles(index: pd.DatetimeIndex, closes) -> list[dict]:
    """Imita la salida de ``market_data.get_candles`` a partir de una serie de
    cierres (sin huecos: cada fecha del índice tiene una vela)."""
    candles = []
    for date, close in zip(index, closes):
        if close is None or (isinstance(close, float) and np.isnan(close)):
            continue
        candles.append(
            {
                "time": int(pd.Timestamp(date).timestamp()),
                "open": close,
                "high": close,
                "low": close,
                "close": close,
                "volume": 1000,
            }
        )
    return candles


@pytest.fixture
def market_returns() -> pd.Series:
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2024-01-01", periods=500)
    return pd.Series(rng.normal(0.0005, 0.01, len(dates)), index=dates)


def annualized_market_return(returns: pd.Series) -> float:
    """E(R_m) como lo anualiza capm_return con compounding=True y frequency=252."""
    return (1 + returns).prod() ** (252 / returns.count()) - 1


# --- constantes -----------------------------------------------------------


def test_market_tickers_are_invertible_etfs_not_raw_indices():
    for ticker in analysis.MARKET_TICKERS.values():
        assert not ticker.startswith("^")


def test_risk_free_ticker_is_13_week_treasury_bill():
    assert analysis.RISK_FREE_TICKER == "^IRX"


def test_every_sector_has_an_icon():
    assert set(analysis.SECTOR_ICONS) == set(analysis.SECTORS)


# --- años y períodos --------------------------------------------------------


def test_first_year_is_earliest_sector_start():
    expected = min(pd.Timestamp(s["start"]).year for s in analysis.SECTORS.values())
    assert analysis.first_year() == expected


def test_available_years_starts_with_all_and_goes_newest_to_oldest():
    years = analysis.available_years(TODAY)
    assert years[0] == analysis.ALL_YEARS
    assert years[1:] == list(range(2026, analysis.first_year() - 1, -1))


def test_capm_period_for_a_year_covers_the_whole_year_with_exclusive_end():
    start, end = analysis.capm_period(2020)
    assert start == pd.Timestamp("2020-01-01")
    assert end == pd.Timestamp("2021-01-01")


def test_capm_period_year_filter_includes_december_31st():
    start, end = analysis.capm_period(2020)
    dec_31 = pd.Timestamp("2020-12-31")
    jan_1_next = pd.Timestamp("2021-01-01")
    assert start <= dec_31 < end
    assert not (start <= jan_1_next < end)


def test_capm_period_for_all_years_goes_from_first_year_through_today():
    start, end = analysis.capm_period(analysis.ALL_YEARS, TODAY)
    assert start == pd.Timestamp(f"{analysis.first_year()}-01-01")
    assert end == pd.Timestamp("2026-10-01")


# --- build_capm_expected_returns --------------------------------------------


def test_capm_matches_formula_with_known_beta(market_returns):
    prices = pd.DataFrame(
        {
            "DOBLE": make_prices(2 * market_returns),
            "MITAD": make_prices(0.5 * market_returns),
        }
    )
    market = make_prices(market_returns).to_frame("SPY")
    risk_free = pd.Series(0.03, index=market.index)

    capm = analysis.build_capm_expected_returns(prices, market, risk_free)

    mkt = annualized_market_return(market_returns.iloc[1:])
    assert capm.loc["DOBLE", "Beta"] == pytest.approx(2.0)
    assert capm.loc["MITAD", "Beta"] == pytest.approx(0.5)
    assert capm.loc["DOBLE", analysis.EXPECTED_RETURN_COL] == pytest.approx(0.03 + 2.0 * (mkt - 0.03))
    assert capm.loc["MITAD", analysis.EXPECTED_RETURN_COL] == pytest.approx(0.03 + 0.5 * (mkt - 0.03))


def test_capm_asset_identical_to_market_returns_market_return(market_returns):
    market = make_prices(market_returns).to_frame("SPY")
    prices = pd.DataFrame({"CLON": market["SPY"]})
    risk_free = pd.Series(0.02, index=market.index)

    capm = analysis.build_capm_expected_returns(prices, market, risk_free)

    assert capm.loc["CLON", "Beta"] == pytest.approx(1.0)
    assert capm.loc["CLON", analysis.EXPECTED_RETURN_COL] == pytest.approx(
        annualized_market_return(market_returns.iloc[1:])
    )


def test_capm_is_sorted_by_expected_return_descending(market_returns):
    prices = pd.DataFrame(
        {
            "BAJA": make_prices(0.3 * market_returns),
            "ALTA": make_prices(1.8 * market_returns),
            "MEDIA": make_prices(1.0 * market_returns),
        }
    )
    market = make_prices(market_returns).to_frame("SPY")
    # Prima de mercado positiva para que más beta implique más retorno esperado.
    risk_free = pd.Series(-1.0, index=market.index)

    capm = analysis.build_capm_expected_returns(prices, market, risk_free)

    assert list(capm.index) == ["ALTA", "MEDIA", "BAJA"]
    assert capm[analysis.EXPECTED_RETURN_COL].is_monotonic_decreasing


def test_capm_output_columns(market_returns):
    prices = make_prices(market_returns).to_frame("XOM")
    market = make_prices(market_returns).to_frame("SPY")
    risk_free = pd.Series(0.01, index=market.index)

    capm = analysis.build_capm_expected_returns(prices, market, risk_free)

    assert list(capm.columns) == ["Beta", analysis.EXPECTED_RETURN_COL, "Tasa libre de riesgo", "Desde"]


def test_capm_late_listing_asset_beta_is_not_biased(market_returns):
    """Un activo que empieza a cotizar a mitad del período (como PECO) debe
    medir su beta solo contra el mercado de su propia ventana, no contra la
    varianza de todo el rango (que puede incluir un tramo mucho más volátil
    anterior a que el activo existiera).

    Esta es la prueba de regresión del bug real: si ``build_capm_expected_returns``
    llamara a ``capm_return`` una sola vez con todos los activos juntos (en vez
    de recortar el mercado por activo), la beta de "NUEVO" saldría sesgada
    hacia abajo por la varianza de la primera mitad volátil del mercado.
    """
    # Primera mitad del mercado muy volátil (tipo COVID), segunda mitad tranquila.
    half = len(market_returns) // 2
    market_returns = market_returns.copy()
    market_returns.iloc[:half] *= 5

    late = make_prices(1.5 * market_returns.iloc[half:])
    prices = pd.DataFrame(
        {
            "VIEJO": make_prices(market_returns),
            "NUEVO": late.reindex(market_returns.index),
        }
    )
    market = make_prices(market_returns).to_frame("SPY")
    risk_free = pd.Series(0.02, index=market.index)

    capm = analysis.build_capm_expected_returns(prices, market, risk_free)

    assert capm.loc["NUEVO", "Beta"] == pytest.approx(1.5)
    assert capm.loc["NUEVO", "Desde"] == market_returns.index[half].date()
    assert capm.loc["VIEJO", "Desde"] == market_returns.index[0].date()


def test_capm_risk_free_is_mean_over_each_asset_window(market_returns):
    half = len(market_returns) // 2
    late = make_prices(market_returns.iloc[half:])
    prices = pd.DataFrame(
        {
            "VIEJO": make_prices(market_returns),
            "NUEVO": late.reindex(market_returns.index),
        }
    )
    market = make_prices(market_returns).to_frame("SPY")
    # Tasa del 0% en la primera mitad y del 5% en la segunda.
    risk_free = pd.Series(
        [0.0] * half + [0.05] * (len(market_returns) - half), index=market.index
    )

    capm = analysis.build_capm_expected_returns(prices, market, risk_free)

    assert capm.loc["NUEVO", "Tasa libre de riesgo"] == pytest.approx(0.05)
    assert capm.loc["VIEJO", "Tasa libre de riesgo"] == pytest.approx(risk_free.mean())


def test_capm_skips_assets_without_data_in_the_window(market_returns):
    """Un activo sin ninguna vela en el período filtrado (p. ej. se eligió un
    año anterior a su salida a bolsa) se omite en vez de romper la tabla."""
    prices = pd.DataFrame(
        {
            "CON_DATOS": make_prices(market_returns),
            "SIN_DATOS": pd.Series(np.nan, index=market_returns.index),
        }
    )
    market = make_prices(market_returns).to_frame("SPY")
    risk_free = pd.Series(0.02, index=market.index)

    capm = analysis.build_capm_expected_returns(prices, market, risk_free)

    assert list(capm.index) == ["CON_DATOS"]


# --- load_prices_with_market -------------------------------------------------


def test_load_prices_with_market_converts_risk_free_from_percent_to_decimal(monkeypatch):
    dates = pd.bdate_range("2024-02-01", periods=2)

    def fake_get_candles(ticker, range_="max", interval="1d"):
        closes = {"CVX": [10.0, 11.0], "QQQ": [20.0, 21.0], "^IRX": [4.03, 5.25]}[ticker]
        return make_candles(dates, closes)

    monkeypatch.setattr(analysis.market_data, "get_candles", fake_get_candles)

    _, _, risk_free = analysis.load_prices_with_market(["CVX"], "QQQ")

    assert risk_free.tolist() == pytest.approx([0.0403, 0.0525])


def test_load_prices_with_market_keeps_only_market_trading_days(monkeypatch):
    """Las cripto cotizan los fines de semana; esos días se descartan para no
    generar retornos de mercado artificiales en 0."""
    all_dates = pd.date_range("2024-03-01", periods=4, freq="D")  # vie, sáb, dom, lun
    market_dates = [all_dates[0], all_dates[3]]  # el proxy (ETF) solo opera vie y lun

    def fake_get_candles(ticker, range_="max", interval="1d"):
        if ticker == "BTC-USD":
            return make_candles(all_dates, [100.0, 101.0, 102.0, 103.0])
        if ticker == "DIA":
            return make_candles(market_dates, [50.0, 51.0])
        if ticker == "^IRX":
            return make_candles(market_dates, [5.0, 5.0])
        raise AssertionError(f"ticker inesperado: {ticker}")

    monkeypatch.setattr(analysis.market_data, "get_candles", fake_get_candles)

    prices, market, risk_free = analysis.load_prices_with_market(["BTC-USD"], "DIA")

    expected_dates = [pd.Timestamp("2024-03-01"), pd.Timestamp("2024-03-04")]
    assert list(prices.index) == expected_dates
    assert list(market.index) == expected_dates
    assert list(risk_free.index) == expected_dates
    assert prices["BTC-USD"].tolist() == [100.0, 103.0]
    assert list(market.columns) == ["DIA"]


def test_load_prices_with_market_forward_fills_gaps_without_backfilling(monkeypatch):
    dates = pd.bdate_range("2024-04-01", periods=4)
    peco_dates = [dates[1], dates[3]]  # todavía no cotizaba el primer ni el tercer día

    def fake_get_candles(ticker, range_="max", interval="1d"):
        if ticker == "PECO":
            return make_candles(peco_dates, [20.0, 22.0])
        if ticker == "IWM":
            return make_candles(dates, [1.0, 2.0, 3.0, 4.0])
        if ticker == "^IRX":
            return make_candles(dates, [5.0, 5.0, 5.0, 5.0])
        raise AssertionError(f"ticker inesperado: {ticker}")

    monkeypatch.setattr(analysis.market_data, "get_candles", fake_get_candles)

    prices, _, _ = analysis.load_prices_with_market(["PECO"], "IWM")

    # El hueco del medio se arrastra (ffill), pero el inicio no se rellena
    # hacia atrás: eso inventaría precios antes de que el activo existiera.
    assert pd.isna(prices["PECO"].iloc[0])
    assert prices["PECO"].iloc[1:].tolist() == [20.0, 20.0, 22.0]


# --- build_sector_capm_table --------------------------------------------------


def test_build_sector_capm_table_filters_by_year(monkeypatch):
    dates_2020 = pd.bdate_range("2020-01-01", periods=5)
    dates_2021 = pd.bdate_range("2021-01-04", periods=5)
    all_dates = dates_2020.append(dates_2021)

    def fake_get_candles(ticker, range_="max", interval="1d"):
        if ticker == "XOM":
            return make_candles(all_dates, list(range(100, 100 + len(all_dates))))
        if ticker == "SPY":
            return make_candles(all_dates, list(range(200, 200 + len(all_dates))))
        if ticker == "^IRX":
            return make_candles(all_dates, [1.0] * len(all_dates))
        raise AssertionError(f"ticker inesperado: {ticker}")

    monkeypatch.setattr(analysis.market_data, "get_candles", fake_get_candles)
    monkeypatch.setitem(analysis.SECTORS, "Prueba", {"stocks": ["XOM"], "start": "2020-01-01"})

    table = analysis.build_sector_capm_table("Prueba", 2020, "SPY")

    assert table.loc["XOM", "Desde"] == dates_2020[0].date()


def test_build_sector_capm_table_is_empty_outside_available_range(monkeypatch):
    dates = pd.bdate_range("2021-01-04", periods=5)

    def fake_get_candles(ticker, range_="max", interval="1d"):
        return make_candles(dates, [100.0] * len(dates))

    monkeypatch.setattr(analysis.market_data, "get_candles", fake_get_candles)
    monkeypatch.setitem(analysis.SECTORS, "Prueba", {"stocks": ["XOM"], "start": "2020-01-01"})

    table = analysis.build_sector_capm_table("Prueba", 2020, "SPY")

    assert table.empty

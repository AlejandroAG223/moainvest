"""Modelo de análisis del CAPM: retorno esperado anual por activo.

Para cada activo de un sector calcula su beta y su retorno esperado anual
según el CAPM (``R_i = R_f + β_i (E(R_m) − R_f)``) con
``pypfopt.expected_returns.capm_return``. Reutiliza los precios ya
descargados/cacheados por ``market_data`` (igual que ``app.varianza.analysis``),
en vez de llamar a ``yfinance`` directamente.

Detalles que no hay que romper (ver también los tests de este módulo):

- La tasa libre de riesgo es real, no inventada: se descarga ``^IRX``
  (rendimiento anual de la letra del Tesoro de EE. UU. a 13 semanas, viene en
  % y se convierte a decimales) y a cada activo se le asigna el promedio de
  ``^IRX`` en SU PROPIO período.
- Los precios se recortan a los días en que cotiza el proxy del mercado (un
  ETF, no un índice puro): si no, los activos que cotizan 7 días por semana
  (cripto) generarían retornos de mercado artificiales en 0 los fines de
  semana. Se hace ``ffill`` pero no ``bfill``: no se inventan precios antes
  de que un activo empezara a cotizar.
- ``capm_return`` se llama POR ACTIVO, con el mercado y la tasa libre de
  riesgo recortados a las fechas en que ESE activo cotiza (``.dropna()``).
  Llamarla una sola vez con todos los activos juntos sesga la beta de los que
  empezaron a cotizar más tarde (p. ej. un REIT que cotiza desde 2021): su
  covarianza se mediría solo en su período, pero dividida por la varianza del
  mercado de todo el rango (que puede incluir una caída fuerte anterior).
- Todo es anual: precios diarios + ``frequency=252`` y ``risk_free_rate``
  anual, para que ambos términos de la fórmula estén en la misma unidad.
- El selector de año filtra con pandas un histórico largo ya descargado
  (``market_data.get_candles`` no acepta fechas start/end, solo
  ``period``/``range_``), igual que ``app.varianza.analysis.monthly_volatility``:
  se pide un rango largo y se recorta por fecha después.
"""
from __future__ import annotations

import pandas as pd
from pypfopt.expected_returns import capm_return

from app.core import market_data

# Sectores (grupos de tickers) disponibles para el análisis de CAPM. No es lo
# mismo que ``app.core.watchlists.WATCHLISTS`` (sirve al sidebar de precios):
# esta lista es propia del CAPM. "start" es el primer año con datos
# confiables del sector: con ventanas más cortas (p. ej. menos de un año) la
# beta medida queda sesgada por falta de datos.
SECTORS: dict[str, dict[str, object]] = {
    "Oil & Gas": {
        "stocks": ["BP", "CVX", "EC", "SHEL", "SU", "TTE", "XOM"],
        "start": "2020-01-01",
    },
    "Real Estate": {
        "stocks": [
            "ADC", "AKR", "BRX", "EPRT", "FCPT", "KIM", "KRG", "MAC", "NNN",
            "O", "PECO", "REG", "UE",
        ],
        "start": "2020-01-01",
    },
    "Criptomonedas": {
        "stocks": ["BTC-USD", "DOGE-USD", "ZEC-USD"],
        "start": "2020-01-01",
    },
}

SECTOR_ICONS = {
    "Oil & Gas": "🛢️",
    "Real Estate": "🏢",
    "Criptomonedas": "🪙",
}

# Proxies del mercado para el CAPM: ETFs líquidos que replican índices
# amplios (invertibles, a diferencia de un índice puro como ``^GSPC``).
MARKET_TICKERS = {
    "S&P 500 (SPY)": "SPY",
    "Nasdaq 100 (QQQ)": "QQQ",
    "Dow Jones (DIA)": "DIA",
    "Small Caps (IWM)": "IWM",
}

# Rendimiento anual (en %) de la letra del Tesoro de EE. UU. a 13 semanas: la
# referencia estándar de tasa libre de riesgo para el CAPM.
RISK_FREE_TICKER = "^IRX"

ALL_YEARS = "Todos"

EXPECTED_RETURN_COL = "Retorno esperado anual (CAPM)"

# Rango pedido a ``market_data.get_candles`` para cubrir desde el primer año
# disponible de cualquier sector hasta hoy: "max" en vez de calcular un número
# de años, porque el rango se filtra después con pandas (ver ``capm_period``).
PRICE_HISTORY_RANGE = "max"


def first_year() -> int:
    """Primer año con datos según el inicio más temprano de los sectores."""
    return min(pd.Timestamp(sector["start"]).year for sector in SECTORS.values())


def available_years(today: pd.Timestamp | None = None) -> list[int | str]:
    """Opciones del selector de año: "Todos" y luego del año actual al primero."""
    current_year = (today or pd.Timestamp.today()).year
    return [ALL_YEARS, *range(current_year, first_year() - 1, -1)]


def capm_period(year: int | str, today: pd.Timestamp | None = None) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Rango [inicio, fin exclusivo) para filtrar por fecha el histórico ya
    descargado. El fin es exclusivo: para incluir el 31 de diciembre de un
    año se filtra hasta el 1 de enero del año siguiente.
    """
    if year == ALL_YEARS:
        end = (today or pd.Timestamp.today()).normalize() + pd.Timedelta(days=1)
        return pd.Timestamp(f"{first_year()}-01-01"), end
    return pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{int(year) + 1}-01-01")


def _close_series(ticker: str, range_: str = PRICE_HISTORY_RANGE) -> pd.Series:
    """Serie de precios de cierre de ``ticker``, indexada por fecha
    (normalizada a medianoche, para poder alinearla con la de otros tickers).
    """
    candles = market_data.get_candles(ticker, range_=range_, interval="1d")
    if not candles:
        return pd.Series(dtype=float, name=ticker)

    df = pd.DataFrame(candles)
    df["date"] = pd.to_datetime(df["time"], unit="s").dt.normalize()
    series = df.set_index("date")["close"].sort_index()
    series.name = ticker
    return series


def load_prices_with_market(
    tickers: list[str], market_ticker: str, range_: str = PRICE_HISTORY_RANGE
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Precios de los activos, del mercado y la tasa libre de riesgo, alineados
    a los días hábiles del mercado.

    Alinear al calendario del proxy de mercado evita que los activos que
    cotizan 7 días por semana (cripto) generen retornos de mercado
    artificiales en 0 los fines de semana. La tasa libre de riesgo se
    devuelve anual y en decimales (``^IRX`` viene en %).
    """
    columns = {ticker: _close_series(ticker, range_) for ticker in tickers}
    market_series = _close_series(market_ticker, range_)
    risk_free_series = _close_series(RISK_FREE_TICKER, range_) / 100

    data = pd.DataFrame({**columns, market_ticker: market_series, RISK_FREE_TICKER: risk_free_series})
    data = data.loc[data[market_ticker].notna()].ffill()

    prices = data[tickers]
    market_prices = data[[market_ticker]]
    risk_free = data[RISK_FREE_TICKER]
    return prices, market_prices, risk_free


def build_capm_expected_returns(
    prices: pd.DataFrame, market_prices: pd.DataFrame, risk_free: pd.Series
) -> pd.DataFrame:
    """Retorno esperado anual por activo según el CAPM: R_i = R_f + β_i (E(R_m) - R_f).

    Se estima activo por activo, recortando el mercado a las fechas en que
    cada uno cotiza: con una sola llamada, un activo que salió a bolsa más
    tarde tendría su covarianza medida en su período pero dividida por la
    varianza del mercado de todo el rango, lo que sesga su beta.

    La tasa libre de riesgo de cada activo es el promedio de ``^IRX`` en esa
    misma ventana: anual, como E(R_m), que ``capm_return`` anualiza con
    ``frequency=252``.
    """
    rows = {}
    for ticker in prices.columns:
        asset = prices[[ticker]].dropna()
        if asset.empty:
            # El activo no tiene precios en el período elegido (p. ej. un año
            # anterior a su salida a bolsa): no se puede estimar su beta.
            continue
        market = market_prices.loc[asset.index]
        risk_free_rate = risk_free.loc[asset.index].mean()
        expected = capm_return(
            asset,
            market_prices=market,
            risk_free_rate=risk_free_rate,
            frequency=252,
        )
        asset_returns = asset[ticker].pct_change().dropna()
        market_returns = market.iloc[:, 0].pct_change().dropna()
        rows[ticker] = {
            "Beta": asset_returns.cov(market_returns) / market_returns.var(),
            EXPECTED_RETURN_COL: expected[ticker],
            "Tasa libre de riesgo": risk_free_rate,
            "Desde": asset.index[0].date(),
        }

    capm = pd.DataFrame.from_dict(rows, orient="index")
    if capm.empty:
        return pd.DataFrame(columns=["Beta", EXPECTED_RETURN_COL, "Tasa libre de riesgo", "Desde"])
    return capm.sort_values(EXPECTED_RETURN_COL, ascending=False)


def build_sector_capm_table(
    sector_name: str, year: int | str, market_ticker: str, today: pd.Timestamp | None = None
) -> pd.DataFrame:
    """Tabla de CAPM (beta, retorno esperado, tasa libre de riesgo y "desde")
    de todos los activos de ``sector_name``, para el ``year`` elegido (o
    ``ALL_YEARS``) y con ``market_ticker`` como proxy del mercado.
    """
    tickers = SECTORS[sector_name]["stocks"]
    prices, market_prices, risk_free = load_prices_with_market(tickers, market_ticker)

    start, end = capm_period(year, today)
    mask = (prices.index >= start) & (prices.index < end)
    prices = prices.loc[mask]
    market_prices = market_prices.loc[mask]
    risk_free = risk_free.loc[mask]

    if prices.empty:
        return pd.DataFrame(columns=["Beta", EXPECTED_RETURN_COL, "Tasa libre de riesgo", "Desde"])

    return build_capm_expected_returns(prices, market_prices, risk_free)

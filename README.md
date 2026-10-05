# MoaiInvest

Panel de precios en vivo, estilo TradingView, construido solo con **Flask**
(arquitectura **MVC**) y **UV** para la gestión del proyecto/dependencias
(sin Node). El sitio principal, **MOAINVEST** (Resumen, Gráficas e Informe),
se sirve en la raíz con su diseño rojo.
Descarga los precios de **Yahoo Finance** (vía `yfinance`) y los dibuja con
[lightweight-charts](https://github.com/tradingview/lightweight-charts), la
propia librería open-source de gráficos de TradingView.

![sidebar](https://img.shields.io/badge/UI-sidebar%20izquierdo-2962ff)

## Arquitectura

```
config.py               # Configuración (variables de entorno)
run.py                   # Punto de entrada: `uv run run.py`
app/
  __init__.py            # Application factory: create_app()
  models/                # MODEL: acceso a datos, sin Flask
    apps.py                 # Registro de "apps" de primer nivel del sidebar
    watchlists.py            # Registro de watchlists (Resumen, Gráficas, Informe)
    market_data.py            # Descarga + caché de precios/velas (yfinance)
    analysis.py                # Volatilidad mensual + histogramas (seaborn)
    report.py                   # Informe HTML de cotizaciones para enviar por email
    media.py                     # Imágenes optimizadas vía Cloudinary (f_auto,q_auto)
    quant.py                    # quantstats: stats, Monte Carlo, plots, reports y earnings
  controllers/            # CONTROLLER: blueprints de Flask
    moainvest.py              # Sitio MOAINVEST: "/", "/graficas/..." e "/informe"
    varianza.py                 # App "Análisis de Varianza" (placeholder)
    quant_stats.py               # App "QUANT STATS" (quantstats, cualquier activo)
    api.py                       # API JSON que consume el JavaScript
  views/                   # VIEW: plantillas Jinja2
    moainvest/                # Plantillas del sitio MOAINVEST (diseño rojo)
    base.html                 # Layout con el sidebar (Varianza, Quant stats, Informes)
    varianza.html               # Página en blanco de Análisis de Varianza
    quant_fundamentales.html     # QUANT STATS: stats + Monte Carlo, plots, reports
    quant_revision.html          # QUANT STATS: benchmark, períodos y earnings
    partials/sidebar.html
    partials/quant_asset_form.html  # Selector de activo y período de QUANT STATS
  static/
    moainvest/moainvest.css   # CSS de Tailwind compilado (fuente en moainvest/src/)
    moainvest/moainvest.js    # Precios en vivo, sparklines, velas, informe y menú
    css/style.css
    js/app.js                 # Colapsar el sidebar de las páginas con base.html
    js/vendor/lightweight-charts.standalone.production.js
tests/                   # pytest (modelos + rutas, con datos simulados)
```

- **Model**: `app/models/market_data.py` es el único lugar que habla con
  `yfinance`; expone `Quote` (precio actual) y velas OHLC ya cacheadas.
  `app/models/apps.py` registra las secciones de primer nivel del sidebar
  y `app/models/watchlists.py` las watchlists del sitio MOAINVEST.
- **View**: plantillas Jinja2 en `app/views` (sí, la carpeta se llama
  `views` y no `templates`, configurado explícitamente en la app factory).
- **Controller**: un blueprint por app (`moainvest`, `varianza`, `quant_stats`,
  `informes`) más
  `api`, que sirve JSON al frontend (para refrescar precios sin recargar
  la página).

## Cómo extenderla

El sidebar tiene dos niveles:

1. **Apps** (`app/models/apps.py`): las secciones de primer nivel, cada
   una con su propio blueprint. Para añadir una nueva (por ejemplo
   "Backtesting"):

   ```python
   App(slug="backtesting", name="Backtesting", icon="🧪", endpoint="backtesting.index", kind="blank"),
   ```

   y crear `app/controllers/backtesting.py` con un blueprint que renderice
   su propia plantilla, registrado en `app/__init__.py`. Con `kind="blank"`
   no hace falta tocar el sidebar: solo aparece el enlace.

2. **Watchlists** (`app/models/watchlists.py`): las listas de tickers que
   usan las Gráficas y el Informe de MOAINVEST. Para añadir una nueva (por
   ejemplo "Bancos"):

   ```python
   Watchlist(
       slug="bancos",
       name="Bancos",
       icon="🏦",
       symbols=(
           Symbol("JPM", "JPMorgan"),
           Symbol("BAC", "Bank of America"),
       ),
   ),
   ```

   No hace falta tocar plantillas, controladores ni JavaScript: la nueva
   watchlist aparece automáticamente en Gráficas, con su propia ruta
   `/graficas/bancos` y su propio endpoint `/api/watchlist/bancos/quotes`,
   y en el Informe.

### Análisis de Varianza

Además de la tabla de precios, esta app calcula la **volatilidad mensual
anualizada** (desviación estándar de los retornos diarios dentro de cada
mes calendario, multiplicada por `sqrt(252)`) de uno o varios tickers y
muestra, por cada uno, un histograma con la distribución de esas
volatilidades a lo largo del período elegido. El histograma se genera en
el servidor con **seaborn/matplotlib** (`app/models/analysis.py`) y se
sirve como PNG desde `GET /api/volatility-chart?tickers=AAPL,MSFT&period=5y`.

### Informe de mercado por email

`app/models/report.py` obtiene las cotizaciones de las watchlists, construye
un informe HTML (resumen de subidas/bajadas, mayores movimientos y una tabla
por watchlist) con la plantilla `app/views/emails/market_report.html` y lo
envía vía Resend:

```python
from app.models.report import build_market_report, send_market_report

report = build_market_report(["overview"])   # .subject y .html listos para enviar
send_market_report("destino@ejemplo.com")      # todas las watchlists
```

También por HTTP: `GET /api/report/preview?watchlists=overview` para verlo
en el navegador y `POST /api/email/send-assets-report` con
`{"to": "destino@ejemplo.com", "watchlists": ["overview"]}` para enviarlo
(`watchlists` es opcional).

Desde la app, el apartado **📨 Informes** (`/informes/`) permite elegir las
watchlists, ver el informe con "Ver informe" y enviarlo con "Enviar por correo".

### Imágenes con Cloudinary

Los fondos de la página de Informes llevan una imagen servida desde
[Cloudinary](https://cloudinary.com) con `f_auto,q_auto` (AVIF/WebP/JPEG y
calidad elegidos por Cloudinary para cada navegador) y un `srcset` de 640,
1280 y 1920 px. La lógica vive en `app/models/media.py`.

1. Copia tu URL de API desde la [consola de Cloudinary](https://console.cloudinary.com/settings/api-keys)
   y ponla en el `.env`: `CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>`.
2. Sube las imágenes (una sola vez, o cada vez que cambies las de
   `app/static/img/informes/`): `uv run flask --app run cloudinary-upload`.

Sin `CLOUDINARY_URL`, la página usa las copias locales de `app/static/img/informes/`.

### QUANT STATS

Análisis cuantitativo con [quantstats](https://github.com/ranaroussi/quantstats)
de **cualquier activo de Yahoo Finance** (`?ticker=AAPL`, `^GSPC`, `BTC-USD`...;
UEC por defecto) en `/quant-stats/`, sobre los retornos diarios del período
elegido (1, 2 o 5 años, o todo). Tiene dos subsecciones en el sidebar que no
se solapan:

- **Gráficas y fundamentales estadísticos** (`/quant-stats/fundamentales`):
  el activo por sí solo, según los 3 módulos principales de quantstats.
  - **stats**: 5 métricas de resumen y 26 más agrupadas (rendimiento, riesgo,
    ajustado por riesgo y operativa diaria), más la **simulación Monte Carlo**
    (`qs.stats.montecarlo`) con número de simulaciones y umbrales de bust y
    goal configurables. Al barajar retornos el resultado final no cambia, así
    que goal siempre es 0% o 100%; bust y los drawdowns son lo informativo.
  - **plots**: 14 gráficas nativas de `qs.plots`.
  - **reports**: tearsheet HTML de `qs.reports.html` (abrir o descargar).
- **Revisión analítica** (`/quant-stats/revision`): todo lo comparativo.
  - **Activo vs. benchmark** (cualquier ticker): gráficas superpuestas, beta
    móvil, todas las métricas lado a lado y tearsheet con benchmark.
  - **Período vs. período**: la misma gráfica en dos períodos, lado a lado.
  - **Reporte vs. reporte**: últimos 4 earnings (EPS estimado vs. reportado,
    días, variación de EPS y de precio entre reportes).

La API sirve las gráficas para cualquier ticker:
`GET /api/quant/<ticker>/plot/<gráfica>.png?period=2y&benchmark=SPY&window=126`,
`GET /api/quant/<ticker>/montecarlo.png?period=2y&sims=1000&bust=-20&goal=50`,
`GET /api/quant/<ticker>/earnings.png?count=4` y las versiones propias de
`drawdown.png` y `monthly-heatmap.png`.

### Nombres del sidebar

Los textos de los enlaces del sidebar (apps de `apps.py`, sus `sections` y las
watchlists de `watchlists.py`) se escriben en formato frase: primera letra en
mayúscula y el resto en minúscula ("Quant stats", "Análisis de varianza"). Se
escriben así en su origen, sin `text-transform`; `tests/test_apps.py` lo
comprueba.

### Iconos de Informes

La página de Informes usa iconos de línea (trazados de
[Lucide](https://lucide.dev), licencia ISC) como SVG inline desde el macro
`app/views/partials/icons.html`, sin CDN ni dependencias:

```jinja
{% import "partials/icons.html" as icons %}
{{ icons.icon("send") }}                      {# decorativo: aria-hidden #}
{{ icons.icon("eye", label="Ver") }}          {# con significado: role="img" #}
```

Heredan el color del texto (`stroke="currentColor"`) y miden `1em` (clase
`.ui-icon`). Para añadir uno, anexa su trazado al diccionario `_paths`; el
icono de cada watchlist se elige por slug en `watchlist_icons` (las que no
estén usan `list`).

### Nombre de la marca

El nombre visible de la app (**MoaiInvest**) vive en un único sitio:
`Config.SITE_NAME` en `config.py`. Un context processor lo inyecta en todas
las plantillas como `site_name` (títulos de página y sidebar) y
`app/models/report.py` lo usa en el asunto y la cabecera del informe por
email. Para renombrar la app basta con cambiar esa línea. El `name` de
`pyproject.toml` (`market-dashboard`) y el prefijo de Cloudinary son
identificadores técnicos y no se muestran al usuario.

### Sitio MOAINVEST

El sitio principal, con el diseño rojo de MOAINVEST, se sirve en la raíz:

| Ruta | Contenido |
|---|---|
| `/` | **Resumen**: watchlist «Resumen» con precios en vivo y la línea del último mes |
| `/graficas/<watchlist>/<ticker>` | **Gráficas**: velas, rangos de 1D a Todo y precios del resto de la watchlist (`/graficas` y `/graficas/<watchlist>` redirigen al primer símbolo) |
| `/informe` | **Informe**: elegir watchlists, vista previa y envío por correo |

Cualquier ruta inexistente muestra el 404 con este mismo diseño. Análisis de
varianza, Quant stats e Informes siguen en sus rutas, con el layout de sidebar,
y su enlace «Gráficas» lleva a `/graficas`.

- Controlador `app/controllers/moainvest.py` y plantillas en `app/views/moainvest/`.
- `app/static/moainvest/moainvest.js` (sin framework) refresca los precios
  cada 15 s y dibuja sparklines, el gráfico de velas y el informe, usando la
  API JSON `/api/...`.
- El CSS es Tailwind v4, pero **sin Node**: el compilado
  `app/static/moainvest/moainvest.css` se commitea, y para regenerarlo tras
  cambiar clases en las plantillas o en el JS se usa el binario standalone de
  Tailwind que instala uv (dependencia de desarrollo `pytailwindcss`):

  ```bash
  uv run flask --app run build-css          # o --watch mientras desarrollas
  ```

## Puesta en marcha

Requiere [uv](https://docs.astral.sh/uv/) y Python 3.12+.

```bash
uv sync                 # instala dependencias (y crea el .venv)
cp .env.example .env    # opcional: ajustar TTLs de caché, etc.
uv run run.py           # http://localhost:5000
```

## Tests

```bash
uv run pytest
```

## Notas

- Los precios se cachean en memoria (`QUOTE_CACHE_TTL` / `CANDLE_CACHE_TTL`
  en `.env`) para no saturar Yahoo Finance; ajusta los valores según lo
  necesites.
- El servidor de desarrollo de Flask no es apto para producción; para
  desplegar, sirve `app` (la factory `create_app()`) con Gunicorn/uWSGI
  detrás de un proxy.

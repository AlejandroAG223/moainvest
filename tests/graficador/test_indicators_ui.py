"""Interfaz de indicadores del Graficador: contratos entre la plantilla y el JS.

El JS no se ejecuta en pytest, así que aquí se comprueban las cosas que se
rompen en silencio: ids que el JS busca en el HTML, nombres que graficador.js
expone a graficador-indicators.js y la sintaxis de ambos ficheros.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

STATIC = Path(__file__).resolve().parents[2] / "app" / "graficador" / "static"
CHART_JS = STATIC / "graficador.js"
INDICATORS_JS = STATIC / "graficador-indicators.js"


def page(client, url="/app/graficador/?ticker=AAPL"):
    return client.get(url).get_data(as_text=True)


def test_page_has_indicators_button_and_dialogs(client):
    html = page(client)
    assert 'id="graficador-indicators-btn"' in html and "Indicadores" in html
    assert 'id="gind-picker"' in html and 'id="gind-settings"' in html
    assert 'id="gind-search"' in html and 'id="gind-list"' in html
    # El botón apunta al diálogo que abre.
    assert 'aria-controls="gind-picker"' in html
    assert "TA-Lib" in html


def test_page_exposes_the_indicator_api_urls_to_the_js(client):
    html = page(client)
    assert 'data-indicators-url="/api/graficador/indicators"' in html
    assert 'data-compute-url="/api/graficador/__T__/indicators"' in html


def test_indicators_script_loads_after_the_chart_script(client):
    html = page(client)
    chart, indicators = html.index("graficador.js"), html.index("graficador-indicators.js")
    assert chart < indicators  # necesita window.GraficadorChart ya definido


def test_invalid_ticker_page_has_no_indicators_ui(client):
    response = client.get("/app/graficador/?ticker=%3Cscript%3E")
    html = response.get_data(as_text=True)
    assert response.status_code == 400
    assert "gind-picker" not in html and "graficador-indicators.js" not in html


def test_every_element_id_the_js_looks_up_exists_in_the_page(client):
    html = page(client)
    source = INDICATORS_JS.read_text()
    ids = set(re.findall(r'\$\("([\w-]+)"\)', source)) | set(re.findall(r'getElementById\("([\w-]+)"\)', source))
    assert len(ids) >= 15  # la regex sigue encontrando los ids
    missing = sorted(i for i in ids if f'id="{i}"' not in html)
    assert missing == []


def test_js_only_uses_what_the_chart_script_exposes():
    # ``const { a, b } = G;`` en graficador-indicators.js debe existir en el contrato.
    wanted = re.search(r"const \{([^}]+)\} = G;", INDICATORS_JS.read_text()).group(1)
    wanted = {name.strip() for name in wanted.split(",")}
    exposed = re.search(r"window\.GraficadorChart = \{(.*?)\n  \};", CHART_JS.read_text(), re.S).group(1)
    missing = sorted(name for name in wanted if not re.search(rf"\b{name}\b", exposed))
    assert missing == []
    assert re.search(r"\bonData\b", exposed) and re.search(r"\bgetContext\b", exposed)


def test_css_defines_every_class_the_js_builds(client):
    css = (STATIC / "graficador.css").read_text()
    source = INDICATORS_JS.read_text()
    # Los ``gind-…`` del JS son clases salvo los que son ids de la plantilla.
    ids = set(re.findall(r'id="(gind-[\w-]+)"', page(client)))
    classes = set(re.findall(r"(?<!data-)\b(gind-[a-z_-]+)\b", source)) - ids
    assert len(classes) >= 15
    missing = sorted(c for c in classes if f".{c}" not in css)
    assert missing == []


def test_indicator_state_is_never_shared_between_instances():
    # Regresión: ``params: def.defaults`` compartía el mismo objeto entre instancias,
    # y editar una SMA cambiaba todas.
    assert "def.defaults" not in INDICATORS_JS.read_text()


@pytest.mark.skipif(shutil.which("node") is None, reason="node no está instalado")
@pytest.mark.parametrize("path", [CHART_JS, INDICATORS_JS], ids=lambda p: p.name)
def test_js_syntax_is_valid(path):
    result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

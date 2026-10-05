"""Sitio MOAINVEST servido por Flask (antes front-end en Next.js)."""
import re
from pathlib import Path

import pytest

from app.models.watchlists import WATCHLISTS, get_watchlist

STATIC = Path(__file__).resolve().parent.parent / "app" / "static" / "moainvest"


def test_resumen_lists_overview_symbols_with_chart_links(client):
    page = client.get("/moainvest/").get_data(as_text=True)
    overview = get_watchlist("overview")
    assert "<title>MOAINVEST | Resumen, gráficas e informes de mercado</title>" in page
    assert 'Resumen del <span class="accent">mercado</span>.' in page
    assert f'data-watchlist-quotes="{overview.slug}"' in page
    for s in overview.symbols:
        assert f'data-quote="{s.ticker}"' in page
        assert f'data-sparkline="{s.ticker}"' in page
    assert 'href="/moainvest/graficas/overview/%5EGSPC"' in page


def test_layout_has_navigation_and_assets(client):
    page = client.get("/moainvest/informe").get_data(as_text=True)
    for href in ("/moainvest/", "/moainvest/graficas", "/moainvest/informe"):
        assert f'href="{href}"' in page
    assert '<a href="/moainvest/informe" aria-current="page"' in page
    assert "/static/moainvest/moainvest.css" in page
    assert "/static/moainvest/moainvest.js" in page
    assert 'id="menu-movil" hidden' in page


@pytest.mark.parametrize("path", ["/moainvest/graficas", "/moainvest/graficas/overview"])
def test_graficas_redirects_to_first_symbol(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/moainvest/graficas/overview/%5EGSPC")


def test_watchlist_redirects_to_its_first_symbol(client):
    watchlist = WATCHLISTS[1]
    response = client.get(f"/moainvest/graficas/{watchlist.slug}")
    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/moainvest/graficas/{watchlist.slug}/{watchlist.symbols[0].ticker}")


def test_chart_page_renders_workspace(client):
    watchlist = WATCHLISTS[1]
    symbol = watchlist.symbols[1]
    response = client.get(f"/moainvest/graficas/{watchlist.slug}/{symbol.ticker}")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert f"<title>{symbol.display_name} · Gráficas | MOAINVEST</title>" in page
    assert '<meta name="robots" content="noindex">' in page
    assert f'data-chart-workspace data-ticker="{symbol.ticker}"' in page
    assert "lightweight-charts.standalone.production.js" in page
    # El rango por defecto es 1M y todos los símbolos de la watchlist están en la lista.
    assert re.search(r'data-range="1mo" data-interval="1d" aria-pressed="true"', page)
    assert page.count("data-quote=") == len(watchlist.symbols)
    for w in WATCHLISTS:
        assert f'href="/moainvest/graficas/{w.slug}/' in page


def test_chart_page_accepts_encoded_ticker(client):
    assert client.get("/moainvest/graficas/overview/%5EGSPC").status_code == 200


@pytest.mark.parametrize(
    "path",
    ["/moainvest/graficas/no-existe", "/moainvest/graficas/overview/NOPE", "/moainvest/no-existe"],
)
def test_unknown_paths_show_moainvest_404(client, path):
    response = client.get(path)
    assert response.status_code == 404
    assert "Este camino todavía no" in response.get_data(as_text=True)


def test_informe_lists_watchlists_and_api_urls(client):
    page = client.get("/moainvest/informe").get_data(as_text=True)
    assert 'data-preview-url="/api/report/preview"' in page
    assert 'data-send-url="/api/email/send-assets-report"' in page
    for w in WATCHLISTS:
        assert f'name="watchlists" value="{w.slug}" checked' in page


def test_existing_flask_pages_are_untouched(client):
    assert client.get("/").status_code == 200
    assert client.get("/informes/").status_code == 200
    assert client.get("/graficas/").status_code == 302


def test_compiled_css_includes_classes_used_by_templates_and_js():
    css = (STATIC / "moainvest.css").read_text()
    # Clases que solo aparecen en moainvest.js (tonos que se ponen en tiempo de ejecución).
    for cls in ("bg-up-soft", "text-brand-deep", r"hover\:bg-line", r"border-ink\/30"):
        assert cls in css, cls
    for cls in (".accent", ".eyebrow", ".hero-in", "--color-brand:#c8102e"):
        assert cls in css, cls

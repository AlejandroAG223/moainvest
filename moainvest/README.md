# MOAINVEST — Resumen, Gráficas e Informe

Front-end en Next.js 16 (React 19, TypeScript, Tailwind CSS v4) para los datos de mercado del backend Flask de este repo.

| Ruta | Contenido |
|---|---|
| `/` | **Resumen**: watchlist «Resumen» con precios en vivo y la línea del último mes |
| `/graficas/[watchlist]/[ticker]` | **Gráficas**: velas (lightweight-charts), rangos de 1D a Todo y precios del resto de la watchlist |
| `/informe` | **Informe**: elegir watchlists, vista previa y envío por correo (Resend) |

## Arrancar

```bash
# 1. Backend de datos (raíz del repo), puerto 5000
uv run run.py

# 2. Front-end (esta carpeta), puerto 3000
npm install
npm run dev
```

El navegador llama a `/api/*` en este sitio y Next lo reenvía a Flask (ver `next.config.ts`). Si Flask no corre en `http://127.0.0.1:5000`, cambia `FLASK_API_URL` en `.env.local` (ver `.env.example`).

Las watchlists se definen en un solo lugar, `app/models/watchlists.py`; este front-end las lee de `GET /api/watchlists`.

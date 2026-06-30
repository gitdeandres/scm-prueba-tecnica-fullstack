# Repo base — prueba técnica

Esqueleto de partida. El enunciado completo está en `prueba-tecnica-seleccion.md`.

**Stack backend:** FastAPI + SQLAlchemy 2.0 async + SQLite + JWT.

## Arranque

```bash
uv sync
uv run uvicorn app.main:app --reload   # http://127.0.0.1:8000/docs
uv run pytest -v
```

Si no usas `uv`, hay un `requirements.txt` equivalente.

Al arrancar, la aplicación carga unos items de ejemplo si la base de datos está vacía, para que puedas probar la búsqueda sin tener que crear datos a mano.

## Endpoints

| Método | Ruta | Auth | Notas |
|---|---|---|---|
| `POST` | `/auth/login` | — | Body: `{"username": "...", "password": "..."}`. Revisa `/docs` para el schema de respuesta. |
| `POST` | `/items/search` | Bearer | Búsqueda con filtros. Implementación actual **insegura** — es lo que tienes que arreglar. |

Hay más endpoints expuestos en `/docs` (Swagger UI). Échale un vistazo. CORS está abierto a cualquier origen para que el frontend en `localhost` conecte sin fricción.

### Usuarios de prueba

| usuario | password |
|---|---|
| `admin` | `admin` |
| `demo`  | `demo`  |

JWT firmado con HS256. Secret hardcodeado en `app/auth.py` — solo para esta prueba.

## Lo que tienes que tocar (backend)

1. **Contrato JSON de filtros.** El campo `filters: str | None` en `SearchRequest` (`app/main.py`) es placeholder. Sustitúyelo por un contrato razonado y documentado.
2. **`app/filters.py::apply_filters`** debe ser seguro:
   - whitelist de columnas resuelta contra el modelo ORM,
   - whitelist de operadores (`=`, `!=`, `>`, `<`, `like`, `in`, `is null`),
   - valores **siempre parametrizados**,
   - error `400` ante filtros inválidos.
3. Límites razonables (nº de filtros, nº de filas). Documenta los valores.
4. Si decides añadir tests para esta parte, sustituye el placeholder de `tests/test_search.py` por casos propios que sostengan tu solución.

## Lo que NO debes tocar

`app/auth.py` y el endpoint `/auth/login` están dados como punto de partida — úsalos desde tu frontend tal cual. Si encuentras algo que cambiarías en un sistema real (por ej. el secret hardcodeado), coméntalo en el README de tu entrega y no perdamos tiempo.

El esqueleto es punto de partida, no dogma — toca lo que necesites en lo que sí depende de ti, y justifica decisiones en el README.

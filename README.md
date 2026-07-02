# SCM Logística - Prueba técnica fullstack

Solución a la prueba técnica de selección. Incluye backend con filtros dinámicos seguros, frontend con autenticación y consumo del API, tests, y soporte Docker.

---

## Cómo ejecutar

### Con Docker (recomendado)

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend + Swagger UI: http://localhost:8000/docs

### En local

**Backend:**
```bash
uv sync
uv run uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
pnpm install
pnpm dev
```

**Tests:**
```bash
uv run pytest -v
```

### Credenciales de prueba

| Usuario | Contraseña |
|---|---|
| `admin` | `admin` |
| `demo` | `demo` |

---

## Ejercicio 1 | Backend: filtros dinámicos seguros

### Contrato JSON de filtros

El campo `filters` de `POST /items/search` acepta una lista de condiciones con esta estructura:

```json
{
  "filters": [
    { "field": "status", "op": "=", "value": "pending" },
    { "field": "warehouse_id", "op": ">", "value": 1 },
    { "field": "sku", "op": "like", "value": "A%" },
    { "field": "sku", "op": "in", "value": ["A1", "B1"] },
    { "field": "created_at", "op": "is null" }
  ]
}
```

**Campos disponibles:** todos los del modelo `Item`: `id`, `sku`, `status`, `warehouse_id`, `created_at`.

**Operadores disponibles:** `=`, `!=`, `>`, `<`, `like`, `in`, `is null`.

**Reglas de validación:**
- `is null` no requiere `value`.
- `in` requiere que `value` sea una lista.
- `like` requiere que `value` sea un string.
- El resto requiere un valor no nulo.

Cualquier campo o operador inválido es rechazado con `400` y un mensaje claro. Un operador fuera del enum es rechazado con `422` por Pydantic antes de llegar a la lógica de filtros.

### Decisión de diseño: array de condiciones vs mapa campo-operador

Elegí un **array de condiciones** `[{field, op, value}]` en lugar de un mapa `{campo: {op, value}}` por dos razones:

1. Permite múltiples condiciones sobre el mismo campo (por ejemplo, `created_at > X` y `created_at < Y`).
2. Es más extensible. Añadir un conector lógico (`"connector": "OR"`) en el futuro no requiere cambiar la estructura base.

El trade-off es que el array es ligeramente más verboso por filtro. Se consultó con el equipo antes de implementar y se confirmó libertad de elección con tal de justificarlo en el README.

### Seguridad

La implementación garantiza que no hay SQL injection por tres vías:

- **Whitelist de columnas** resuelta dinámicamente desde `Item.__table__.columns`, sin strings sueltos hardcodeados que puedan desincronizarse con el modelo.
- **Whitelist de operadores** implementada como `StrEnum`, Pydantic rechaza cualquier valor fuera del enum con `422` antes de llegar a la lógica de filtros.
- **Valores siempre parametrizados** mediante expresiones ORM de SQLAlchemy (`column.like()`, `column.in_()`, `column.__eq__()`, etc.), nunca interpolados en SQL crudo.

### Límites

| Límite | Valor | Motivo |
|---|---|---|
| Filtros por petición | 5 | Suficiente para casos de uso reales en un WMS; evita consultas excesivamente complejas |
| Filas devueltas | 100 | Adecuado para UI paginada; en producción se complementaría con paginación explícita por cursor u offset |

### Nota sobre `app/auth.py`

El secret JWT está hardcodeado según el repo base. No se modificó respetando las instrucciones. En un sistema real se gestionaría como variable de entorno y se rotaría periódicamente.

---

## Ejercicio 2 | Frontend

Stack: Vue 3 + TypeScript + Vite + Pinia + Vue Router + axios.

### Estructura

```
frontend/src/
├── api/
│   └── client.ts       # axios con interceptores de auth y redirección en 401
├── stores/
│   └── auth.ts         # Pinia store: token, login, logout
├── views/
│   ├── LoginView.vue   # pantalla de login con manejo de errores
│   └── ItemsView.vue   # pantalla protegida con tabla, filtros y cambio de estado
└── router/
    └── index.ts        # rutas + guardia de navegación
```

### Decisiones relevantes

**Persistencia del token: `sessionStorage`**

Se descartó `localStorage` porque persiste entre sesiones de navegador, superficie de ataque innecesaria para una app de gestión interna. Se descartó cookie `HttpOnly` porque requeriría modificar `app/auth.py`, marcado como intocable en el enunciado. `sessionStorage` es el balance correcto: el token vive solo durante la sesión activa y desaparece al cerrar la pestaña.

**Interceptores de axios**

El token se inyecta automáticamente en cada petición via interceptor de request. Los `401` redirigen al login via interceptor de response, sin lógica duplicada en cada vista.

**Cambio de status: PATCH en lugar de GET**

El endpoint dado `GET /items/{id}/status/{new_status}` muta datos, lo cual no es semánticamente correcto (los GET no deben tener efectos secundarios). Se implementó `PATCH /items/{id}/status` con body `{"status": "..."}` y se actualizó el frontend para consumirlo. El GET original se mantiene intacto para no romper el contrato dado. Esta decisión se consultó con el equipo antes de implementar y fue confirmada.

### Bonus implementados

- Input de filtros sobre `status` y `warehouse_id` que usa el contrato definido en el ejercicio 1.
- Persistencia del token con `sessionStorage` (justificada arriba).

---

## Tests

10 tests en `tests/test_search.py` usando pytest-asyncio en modo `auto` con SQLite en memoria. No se requiere `@pytest.mark.asyncio` por la configuración `asyncio_mode = "auto"` en `pyproject.toml`.

| Test | Qué cubre |
|---|---|
| `test_search_sin_filtros_devuelve_items` | Sin filtros devuelve el seed completo |
| `test_search_filtro_por_status` | Filtro de igualdad sobre campo string |
| `test_search_filtro_in` | Operador `in` con lista de valores |
| `test_search_campo_invalido_devuelve_400` | Campo fuera de whitelist → 400 con mensaje claro |
| `test_search_operador_invalido_devuelve_422` | Operador fuera del enum → 422 de Pydantic |
| `test_search_exceso_de_filtros_devuelve_400` | Más de 5 filtros → 400 |
| `test_search_sin_token_devuelve_401` | Token inválido → 401 |
| `test_search_limite_filas` | Respuesta nunca supera 100 filas |
| `test_patch_status_actualiza_item` | PATCH actualiza el status y devuelve el item modificado |
| `test_patch_status_item_inexistente_devuelve_404` | Item inexistente → 404 con mensaje claro |

---

## Docker

Se añadió soporte Docker no requerido en el enunciado, pero coherente con el stack del equipo.

- **Backend:** imagen `python:3.13-slim` con `uv` para gestión de dependencias, mismo gestor que en desarrollo local.
- **Frontend:** imagen `node:22-slim` con `pnpm@10.15.1` fijado explícitamente para evitar conflictos de política entre versiones del lockfile.
- La base de datos SQLite se persiste en un volumen `./data/` entre reinicios del contenedor.

---

## Mejoras futuras detectadas

**Backend:**
- Paginación explícita con cursor u offset en `POST /items/search`, el límite de 100 filas es una solución provisional válida para el alcance de la prueba.
- Validación del valor de `status` contra un enum en el PATCH, actualmente acepta cualquier string.
- Secret JWT como variable de entorno con rotación periódica.
- Logging estructurado (structlog) para trazabilidad en producción.

**Frontend:**
- Soporte para múltiples filtros simultáneos en la UI (actualmente solo uno a la vez).
- Tests de componente con Vitest + Testing Library.
- Manejo del refresh token para renovar la sesión sin forzar logout.

---

## Tiempo de entrega

El tiempo de dedicación efectiva fue de aproximadamente 2,5 horas. El desarrollo comenzó el 01 de julio a las 17:40h y concluyó el 02 de julio a las 12:30h, pero el tiempo transcurrido entre ambas fechas incluye la espera de respuesta a dos consultas enviadas al equipo antes de comenzar la implementación (sobre el contrato de filtros y el endpoint GET que muta datos).

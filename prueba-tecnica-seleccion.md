# Prueba técnica — Proceso de selección

Gracias por dedicar tiempo a esta prueba. Queremos usarla para entender cómo razonas, cómo tomas decisiones técnicas y cómo comunicas los trade-offs, no para comprobar si recuerdas detalles de memoria.

Si durante el ejercicio te quedas atascado, encuentras una ambigüedad o decides dejar algo fuera por tiempo, explícalo en el README. Eso también nos ayuda a evaluar cómo trabajas en situaciones reales.

**Tiempo orientativo:** 3–4 horas. Si necesitas algo más de tiempo, coméntalo en la entrega; no es eliminatorio.
**Entrega:** un repositorio Git, público o compartido por invitación, con un README que explique tus decisiones y cómo ejecutar backend y frontend.

---

## Antes de empezar

Algunas pautas para que todos partamos de la misma base:

- **Backend:** Python 3.13, con lint mediante `ruff`.
- **Frontend:** preferimos Vue 3 + TypeScript + Vite. Si eliges otro framework moderno, no hay problema: explica brevemente el motivo en el README.
- Usa **Conventional Commits** (`feat:`, `fix:`, `refactor:`, etc.) para que podamos seguir la evolución del trabajo.
- Respeta el stack indicado en cada parte, salvo que justifiques una alternativa razonable.
- Priorizamos código claro, decisiones bien explicadas y tests útiles. No buscamos cobertura perfecta ni una solución sobredimensionada.

---

## Ejercicio 1 — Backend: filtros dinámicos seguros

**Stack:** FastAPI + SQLAlchemy 2.0 async + SQLite en memoria para tests.

El repositorio incluye un esqueleto de aplicación FastAPI con:

- un modelo `Item(id, sku, status, warehouse_id, created_at)`;
- un endpoint `POST /items/search`;
- autenticación mediante JWT Bearer.

La implementación actual de filtros es intencionadamente insegura para que puedas mejorarla:

```python
def apply_filters(stmt: Select, filters: str | None) -> Select:
    if not filters:
        return stmt
    return stmt.where(text(filters))  # inseguro: SQL injection directo
```

### Tu objetivo

Queremos poder filtrar `Item` de forma dinámica y segura. Para ello, tendrás que diseñar e implementar una solución que resuelva ese problema.

### Qué esperamos ver

1. **Un contrato JSON de filtros claro**
   Define la estructura esperada, los campos obligatorios y cómo se representan operaciones especiales como `in` o `is null`.

2. **Resolución segura de filtros**
   La implementación debe:

   - obtener la whitelist de columnas desde el modelo ORM, no a partir de strings sueltos;
   - limitar los operadores permitidos, por ejemplo: `=`, `!=`, `>`, `<`, `like`, `in`, `is null`;
   - parametrizar siempre los valores usando expresiones ORM o `bindparams`;
   - devolver `400` cuando un filtro sea inválido, en lugar de ignorarlo silenciosamente.

3. **Límites razonables**
   Añade límites para evitar peticiones excesivas, por ejemplo:

   - número máximo de filtros por petición;
   - número máximo de filas devueltas.

   Elige los valores que consideres adecuados y documéntalos en el README.

### Bonus opcional

Añade tests útiles que cubran los casos que consideres importantes para defender tu solución.

`app/auth.py` y `/auth/login` ya están preparados. Te pedimos que no los modifiques, porque son el punto de partida común para el ejercicio 2.

---

## Ejercicio 2 — Frontend: login y consumo del API

**Stack preferido:** Vue 3 + TypeScript + Vite. Puedes usar otro framework moderno si lo justificas.

Implementa una pequeña aplicación frontend dentro de una subcarpeta `frontend/` del mismo repositorio. La idea es que permita autenticarse contra el backend y consultar items.

### Qué esperamos ver

1. **Pantalla de login**
   Debe pedir usuario y contraseña, llamar a `POST /auth/login` y guardar el token devuelto.

   Credenciales de prueba:

   - `admin` / `admin`
   - `demo` / `demo`

2. **Pantalla protegida**
   Debe incluir un botón “Buscar items” que llame a `POST /items/search` enviando:

   ```http
   Authorization: Bearer <token>
   ```

   Muestra los resultados en una tabla o lista sencilla.

3. **Cambiar el estado de un item**
   Desde la pantalla protegida, permite modificar el `status` de un item (por
   ejemplo con un botón o un desplegable por fila) y refleja el cambio en la
   tabla. El endpoint que necesitas está expuesto en `/docs`; localízalo e
   intégralo tú.

4. **Gestión básica de errores**

   - Si las credenciales son inválidas, muestra un mensaje claro en el formulario.
   - Si el token ha expirado o no existe al llamar a `/items/search`, vuelve a la pantalla de login.
   - Si ocurre otro error, muestra un mensaje comprensible para la persona usuaria.

5. **Logout**
   Añade una acción de logout que elimine el token en cliente y devuelva a la pantalla de login.

### Bonus opcional

Estos puntos no son obligatorios. Añádelos solo si te ayudan a mostrar mejor tu forma de trabajar:

- Un input de filtros básicos sobre `status` o `warehouse_id` que use el contrato definido en el ejercicio 1.
- Persistencia del token entre recargas (`sessionStorage`, `localStorage`, cookie `HttpOnly` u otra opción). Explica por qué eliges una opción y descartas las demás.
- Algún test de frontend, por ejemplo con Vitest, Jest o Testing Library, según lo que encaje con tu framework.

### No hace falta

Para mantener el alcance razonable, no hace falta que priorices:

- una interfaz visual especialmente pulida;
- CSS pixel-perfect;
- routing complejo;
- integración con servicios reales.

Dos vistas funcionales y una redirección al login en caso de `401` son suficientes.

---

## Cómo evaluaremos la prueba

| Criterio | Qué miraremos |
|---|---|
| Correctitud | Que backend y frontend cumplan el comportamiento descrito |
| Seguridad | Validación de entrada, parametrización, manejo del token y errores claros |
| Tests | Si decides incluirlos, que cubran casos relevantes y útiles, sin perseguir cobertura por cobertura |
| Commits y README | Mensajes claros, decisiones justificadas e instrucciones de ejecución |
| Comunicación | Trade-offs, dudas y decisiones explicadas de forma honesta |

---

## Qué no evaluaremos

No queremos que inviertas tiempo en cosas que no aportan a este ejercicio. En concreto, no evaluaremos:

- cobertura de tests al 100%;
- integración con servicios reales;
- velocidad como criterio principal.

Lo visual no es lo más importante en esta prueba, pero una interfaz cuidada también suma. Aun así, preferimos una solución pensada, mantenible y bien explicada antes que una solución hecha con prisas.

---

## ¿Tienes dudas?

Si algo del enunciado no queda claro o te parece incoherente, pregúntanos antes de empezar.

**Preguntar no penaliza; al contrario, nos ayuda a ver cómo aclaras requisitos antes de implementar.**
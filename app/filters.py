from enum import StrEnum
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import Select, and_
from sqlalchemy.orm import DeclarativeBase

# Límite de filtros por petición para evitar consultas excesivamente complejas
MAX_FILTERS = 5


class Operator(StrEnum):
    """Operadores permitidos. Cualquier valor fuera de esta lista es rechazado con 422."""
    EQ = "="
    NEQ = "!="
    GT = ">"
    LT = "<"
    LIKE = "like"
    IN = "in"
    IS_NULL = "is null"


class FilterItem(BaseModel):
    """Unidad mínima de filtro: campo + operador + valor opcional (is null no requiere valor)."""
    field: str
    op: Operator
    value: Any = None


def _get_column_whitelist(model: type[DeclarativeBase]) -> dict:
    """
    Construye la whitelist de columnas filtrables directamente desde el modelo ORM.
    Evita listas hardcodeadas que pueden desincronizarse con el modelo real.
    """
    return {col.name: col for col in model.__table__.columns}


def apply_filters(stmt: Select, filters: list[FilterItem] | None, model: type[DeclarativeBase]) -> Select:
    """
    Aplica filtros dinámicos y seguros sobre un Select de SQLAlchemy.

    Seguridad garantizada por:
    - Whitelist de columnas resuelta contra el modelo ORM (no strings sueltos)
    - Whitelist de operadores via enum (Pydantic rechaza valores inválidos con 422)
    - Valores siempre parametrizados via expresiones ORM (nunca interpolados en SQL)
    - 400 explícito ante campos inválidos o tipos de valor incorrectos
    """
    if not filters:
        return stmt

    # Rechazamos antes de procesar para no iterar una lista potencialmente enorme
    if len(filters) > MAX_FILTERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Demasiados filtros. Máximo permitido: {MAX_FILTERS}.",
        )

    whitelist = _get_column_whitelist(model)
    conditions = []

    for f in filters:
        # Validación de campo contra whitelist — falla rápido con mensaje claro
        if f.field not in whitelist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Campo no permitido: '{f.field}'.",
            )

        column = whitelist[f.field]

        if f.op == Operator.IS_NULL:
            # is_() genera "IS NULL" parametrizado, nunca SQL crudo
            conditions.append(column.is_(None))

        elif f.op == Operator.IN:
            if not isinstance(f.value, list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El operador 'in' requiere una lista de valores en '{f.field}'.",
                )
            conditions.append(column.in_(f.value))

        elif f.op == Operator.LIKE:
            if not isinstance(f.value, str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El operador 'like' requiere un string en '{f.field}'.",
                )
            conditions.append(column.like(f.value))

        elif f.op in (Operator.EQ, Operator.NEQ, Operator.GT, Operator.LT):
            if f.value is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El operador '{f.op}' requiere un valor en '{f.field}'.",
                )
            # Uso de los métodos ORM en lugar de construir SQL manualmente
            op_map = {
                Operator.EQ: column.__eq__,
                Operator.NEQ: column.__ne__,
                Operator.GT: column.__gt__,
                Operator.LT: column.__lt__,
            }
            conditions.append(op_map[f.op](f.value))

    # and_() con múltiples condiciones genera WHERE col1=x AND col2=y ...
    return stmt.where(and_(*conditions))

from sqlalchemy import Select, text


def apply_filters(stmt: Select, filters: str | None) -> Select:
    """
    Aplica una cadena de filtros a un Select.

    TODO (candidato): sustituye esta implementación por una segura.
      - El input debe ser estructurado (JSON), no SQL crudo.
      - Whitelist de columnas resueltas contra el modelo ORM.
      - Whitelist de operadores.
      - Valores siempre parametrizados.
      - 400 ante filtros inválidos.
    """
    if not filters:
        return stmt
    return stmt.where(text(filters))  # inseguro: SQL injection directo

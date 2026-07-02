from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    authenticate,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
)
from app.database import Base, SessionLocal, engine, get_session
from app.filters import apply_filters, FilterItem
from app.models import Item

SEED_ITEMS = [
    Item(sku="A1", status="pending", warehouse_id=1, created_at=datetime(2025, 1, 1)),
    Item(sku="A2", status="done", warehouse_id=1, created_at=datetime(2025, 1, 2)),
    Item(sku="B1", status="pending", warehouse_id=2, created_at=datetime(2025, 1, 3)),
    Item(sku="B2", status="cancelled", warehouse_id=2, created_at=datetime(2025, 1, 4)),
    Item(sku="C1", status="pending", warehouse_id=3, created_at=datetime(2025, 1, 5)),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        existing = await session.scalar(select(func.count()).select_from(Item))
        if not existing:
            session.add_all(
                Item(
                    sku=i.sku,
                    status=i.status,
                    warehouse_id=i.warehouse_id,
                    created_at=i.created_at,
                )
                for i in SEED_ITEMS
            )
            await session.commit()
    yield


app = FastAPI(lifespan=lifespan)

# CORS abierto para que el frontend del candidato pueda conectarse sin fricción
# en local. En producción se restringiría a orígenes conocidos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# Límite de filas devueltas por búsqueda.
# En producción se complementaría con paginación explícita (cursor o offset).
MAX_ROWS = 100


class SearchRequest(BaseModel):
    # Lista de filtros estructurados. None o lista vacía devuelve todos los items (hasta MAX_ROWS).
    # Cada filtro sigue el contrato: {"field": "status", "op": "=", "value": "pending"}
    # Operadores disponibles: =, !=, >, <, like, in, is null
    filters: list[FilterItem] | None = None


class ItemOut(BaseModel):
    id: int
    sku: str
    status: str
    warehouse_id: int

    model_config = {"from_attributes": True}


@app.post("/auth/login")
async def login(payload: LoginRequest) -> TokenPair:
    if not authenticate(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    return TokenPair(
        access_token=create_access_token(payload.username),
        refresh_token=create_refresh_token(payload.username),
    )


@app.post("/auth/refresh")
async def refresh(payload: RefreshRequest) -> TokenPair:
    subject = decode_refresh_token(payload.refresh_token)
    return TokenPair(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


@app.post("/items/search")
async def search_items(
    payload: SearchRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[str, Depends(get_current_user)],
) -> list[ItemOut]:
    # limit() se aplica antes de los filtros para que el tope sea siempre efectivo
    stmt = select(Item).limit(MAX_ROWS)
    stmt = apply_filters(stmt, payload.filters, Item)
    result = await session.execute(stmt)
    return [ItemOut.model_validate(i) for i in result.scalars().all()]


@app.get("/items/{item_id}/status/{new_status}")
async def set_item_status(
    item_id: int,
    new_status: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[str, Depends(get_current_user)],
):
    item = await session.get(Item, item_id)
    if item is None:
        return JSONResponse(
            status_code=200,
            content={"success": False, "error": f"No existe el item {item_id}"},
        )
    item.status = new_status
    await session.commit()
    await session.refresh(item)
    return ItemOut.model_validate(item)


class StatusUpdate(BaseModel):
    # Solo se permite actualizar el campo status
    status: str


@app.patch("/items/{item_id}/status")
async def update_item_status(
    item_id: int,
    payload: StatusUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[str, Depends(get_current_user)],
) -> ItemOut:
    """
    Reemplaza al GET /items/{item_id}/status/{new_status} original.
    PATCH es el método semánticamente correcto para mutaciones parciales de un recurso.
    El GET original se mantiene para no romper compatibilidad con el contrato dado.
    """
    result = await session.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado.")

    item.status = payload.status
    await session.commit()
    await session.refresh(item)
    return ItemOut.model_validate(item)

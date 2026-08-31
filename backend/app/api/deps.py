"""Dependencias compartidas de la API.

`require_admin` (Mision 07, DEC-021) es un control de acceso administrativo
inicial: compara el header `X-Admin-Token` contra `ADMIN_API_KEY`
(`app/core/config.py`). No es un sistema de usuarios ni de sesiones -- el
"usuario" que abre/cierra una votacion sigue siendo texto libre declarado por
quien tiene el token, no una identidad autenticada. Si `ADMIN_API_KEY` no
esta configurado, se rechazan todas las acciones administrativas: falla
cerrado, nunca abierto.
"""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.core.config import settings


def require_admin(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> None:
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administracion deshabilitada: ADMIN_API_KEY no esta configurado.",
        )
    if x_admin_token != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token administrativo invalido o ausente.",
        )

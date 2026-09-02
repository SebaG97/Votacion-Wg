"""Login administrativo usuario/contrasena (Mision 12, DEC-030).

Reemplaza el flujo de "pegar el `ADMIN_API_KEY` crudo" del login por un
usuario y contrasena convencionales, validados contra `ADMIN_USERNAME` /
`ADMIN_PASSWORD` (`Settings`) -- un unico par de credenciales fijo, no una
tabla de usuarios. No toca `require_admin` (`app/api/deps.py`, DEC-021) ni
ningun endpoint ya protegido por el: al validar correctamente devuelve el
mismo `ADMIN_API_KEY` que el resto del panel ya manda como header
`X-Admin-Token` en cada request. Este endpoint es una puerta de entrada nueva
delante de esa proteccion, no un reemplazo.
"""

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import settings
from app.core.rate_limit import RATE_LIMIT_LOGIN, limiter
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
@limiter.limit(RATE_LIMIT_LOGIN)
def login(request: Request, body: LoginRequest) -> LoginResponse:
    if not settings.admin_username or not settings.admin_password or not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Login administrativo deshabilitado: ADMIN_USERNAME, ADMIN_PASSWORD "
                "y ADMIN_API_KEY deben estar configurados en el servidor."
            ),
        )
    if body.usuario != settings.admin_username or body.contrasena != settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
        )
    return LoginResponse(token=settings.admin_api_key)

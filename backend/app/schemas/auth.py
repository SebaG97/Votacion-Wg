from pydantic import BaseModel


class LoginRequest(BaseModel):
    usuario: str
    contrasena: str


class LoginResponse(BaseModel):
    """`token` es el mismo valor que `ADMIN_API_KEY` (DEC-021): el frontend lo
    guarda y lo manda como `X-Admin-Token` en cada request administrativo,
    exactamente como si lo hubiera pegado a mano (Mision 12, DEC-030)."""

    token: str

"""Rate limiting por IP para los endpoints operativos sin control de acceso
(`POST /habilitaciones/consultar` y `POST /votaciones/{id}/votos`, DEC-020).

Ver DEC-029 en `docs/DECISIONES.md`: la votacion queda expuesta en internet
por dias o semanas (no un evento de un dia), y una contrasena compartida no
identifica a la persona ni aporta trazabilidad real. Limitar el ritmo de
requests por IP eleva el costo de escanear el padron o automatizar intentos
de voto, sin reemplazar una autenticacion real por votante (fuera de alcance).
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def get_client_ip(request: Request) -> str:
    """IP real del cliente para contar el rate limit.

    `slowapi.util.get_remote_address` usa `request.client.host`, que detras
    de un proxy o load balancer (DigitalOcean App Platform, Nginx) es la IP
    del proxy, no la del votante: eso rate-limitaria a todos los votantes
    juntos como si fueran uno solo. Si el proxy manda `X-Forwarded-For`, se
    usa el primer valor (la IP original del cliente); si no esta presente,
    se cae a `get_remote_address`. El header es falseable por quien le pega
    directo al backend sin pasar por el proxy, pero en ese despliegue nadie
    le pega directo (DigitalOcean App Platform siempre enruta via su proxy),
    asi que no debilita la proteccion real.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=get_client_ip)

RATE_LIMIT_OPERATIVO = f"{settings.rate_limit_por_minuto}/minute"

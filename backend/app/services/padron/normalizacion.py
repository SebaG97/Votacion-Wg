"""Normalizacion de texto, celular y CI (Mision 02, DEC-005).

Portado sin cambios de conducta desde `backend/scripts/explorar_padron.py`.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any


def texto(valor: Any) -> str | None:
    """Normaliza a texto no vacio. Trata `''` y `' '` como ausencia de dato."""
    if valor is None:
        return None
    limpio = str(valor).strip()
    return limpio or None


def sin_tildes(valor: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", valor) if unicodedata.category(c) != "Mn"
    )


def clave_texto(valor: Any) -> str | None:
    """Clave comparable: sin tildes, mayusculas y espacios colapsados."""
    limpio = texto(valor)
    if limpio is None:
        return None
    return re.sub(r"\s+", " ", sin_tildes(limpio)).upper()


def clave_circulo(valor: Any) -> str | None:
    """Clave de circulo: ademas quita comillas y signos de puntuacion sueltos."""
    base = clave_texto(valor)
    if base is None:
        return None
    base = base.replace('"', " ").replace("'", " ").replace("°", " ")
    return re.sub(r"\s+", " ", base).strip() or None


def normalizar_celular(valor: Any) -> tuple[str | None, str | None]:
    """Devuelve `(celular_normalizado, motivo_de_rechazo)`.

    Formato canonico paraguayo: 10 digitos con `0` inicial (`09XXXXXXXX`).
    Los valores de 9 digitos provienen de celdas cargadas como numero, que
    perdieron el cero inicial; se restaura.
    """
    crudo = texto(valor)
    if crudo is None:
        return None, "FALTANTE"
    digitos = re.sub(r"\D", "", crudo)
    if not digitos:
        return None, "SIN_DIGITOS"
    if digitos.strip("0") == "":
        # Casos `0` / `00`: placeholder de "no tiene", no un numero real.
        return None, "PLACEHOLDER_CERO"
    if len(digitos) == 9:
        digitos = "0" + digitos
    if len(digitos) != 10 or not digitos.startswith("0"):
        return None, "FORMATO_INVALIDO"
    return digitos, None


def normalizar_ci(valor: Any) -> tuple[str | None, str | None]:
    """Devuelve `(ci_normalizada, motivo_de_rechazo)`. Descarta digito verificador."""
    crudo = texto(valor)
    if crudo is None:
        return None, "FALTANTE"
    if not re.search(r"\d", crudo):
        return None, "NO_NUMERICO"
    # `1.470.451-0` -> `1470451`; `840.014` -> `840014`.
    base = crudo.split("-")[0]
    digitos = re.sub(r"\D", "", base)
    if not digitos or digitos.strip("0") == "":
        return None, "PLACEHOLDER_CERO"
    return str(int(digitos)), None


def es_marca(valor: Any) -> bool:
    """`X`, `1` y similares son marcas booleanas; `' '` y `None` no lo son."""
    return texto(valor) is not None

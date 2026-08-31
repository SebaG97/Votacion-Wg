"""Modelo intermedio (no ORM) para representar filas del Excel del padron.

Nombrado `*Excel` para no colisionar con los modelos SQLAlchemy de
`app.models` (`Persona`, `Matrimonio`), que representan otra cosa: una fila
del Excel todavia no es una persona/matrimonio persistido, es un candidato que
el importador puede rechazar o transformar antes de guardar.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class IncidenciaDetectada:
    tipo: str
    severidad: str
    hoja: str
    fila_excel: int | str
    circulo: str | None
    persona: str | None
    detalle: str

    def como_fila(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PersonaExcel:
    fila: int
    circulo: str | None
    circulo_nuevo: str | None
    matrimonio: str | None
    apellidos: str | None
    nombres: str | None
    celular_crudo: Any
    celular: str | None
    celular_motivo: str | None
    email: str | None
    ci: str | None
    ci_motivo: str | None
    es_consagrado: bool
    es_sin_consagracion: bool
    es_ml: bool
    es_viudo: bool
    es_jefe: bool
    tiene_jornada: bool
    marca_no_ml: bool
    observacion: str | None

    @property
    def etiqueta(self) -> str:
        return " ".join(p for p in (self.apellidos, self.nombres) if p) or "(sin nombre)"


@dataclass
class MatrimonioExcel:
    etiqueta: str | None
    circulo: str | None
    filas: list[int] = field(default_factory=list)
    personas: list[PersonaExcel] = field(default_factory=list)

    @property
    def es_consagrado(self) -> bool:
        return any(p.es_consagrado for p in self.personas)

    @property
    def es_sin_consagracion(self) -> bool:
        return any(p.es_sin_consagracion for p in self.personas)

    @property
    def es_jefe(self) -> bool:
        return any(p.es_jefe for p in self.personas)

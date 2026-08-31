"""Nombres de hoja y posiciones de columna del Excel del padron (Mision 02).

Ambas hojas de datos declaran un `max_column` inflado (~16.000) por formato
residual. Los datos reales terminan en S (19) y en I (9) respectivamente, por
eso se acota la lectura en vez de recorrer las columnas fantasma
(`docs/PADRON_ANALISIS.md`, seccion 1.1).
"""

from app.models.enums import SeveridadIncidencia

HOJA_PRINCIPAL = "Copia de Jefes ML 2026. betty(1"
HOJA_JEFES = "LISTADO JEFES"
HOJA_PIVOT = "Hoja1"

COLUMNAS_PRINCIPAL = 19
COLUMNAS_JEFES = 9

# Indices 0-based de la hoja principal.
P_GRUPOS = 0  # A
P_SIN_CIRCULO = 1  # B  (header con typo: "SIN CIRCILO")
P_ML = 2  # C
P_VIUDOS = 3  # D
P_MIEMBROS = 4  # E
P_CIRCULO = 5  # F
P_CIRCULO_NUEVO = 6  # G  (sin header)
P_SIN_CONSAGRACION = 7  # H
P_CONSAGRADOS = 8  # I
P_JORNADA = 9  # J
P_JEFES = 10  # K
P_MATRIMONIO = 11  # L
P_APELLIDOS = 12  # M
P_NOMBRES = 13  # N  (header es un espacio en blanco)
P_CELULAR = 14  # O
P_EMAIL = 15  # P
P_CI = 16  # Q
P_OBSERVACION = 17  # R  (sin header)
P_NO_ML = 18  # S

# Indices 0-based de LISTADO JEFES.
J_ORDEN = 0  # A (sin header)
J_CIRCULO = 1  # B
J_JEFES = 2  # C
J_MATRIMONIO = 3  # D
J_APELLIDOS = 4  # E
J_NOMBRES = 5  # F
J_CELULAR = 6  # G
J_EDUCADORES = 7  # H
J_OBSERVACION = 8  # I

SEVERIDAD_CRITICA = SeveridadIncidencia.CRITICA.value
SEVERIDAD_ALTA = SeveridadIncidencia.ALTA.value
SEVERIDAD_MEDIA = SeveridadIncidencia.MEDIA.value
SEVERIDAD_BAJA = SeveridadIncidencia.BAJA.value

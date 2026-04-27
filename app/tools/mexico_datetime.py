"""Herramienta con fecha y hora actual en zona horaria de México (centro)."""

# En Windows, zoneinfo requiere el paquete PyPI `tzdata` (IANA). Importarlo
# antes de ZoneInfo asegura que haya base de datos disponible.
try:
    import tzdata  # noqa: F401  # pyright: ignore[reportMissingModuleSource]
except ImportError:
    pass  # En Linux/macOS el sistema ya suele traer la zona; si falta, falla claro

from datetime import datetime
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

_MX_CENTRO = None
_MX_CENTRO_KEY = "America/Mexico_City"


def _get_mexico_central() -> ZoneInfo:
    global _MX_CENTRO
    if _MX_CENTRO is None:
        try:
            _MX_CENTRO = ZoneInfo(_MX_CENTRO_KEY)
        except ZoneInfoNotFoundError as e:
            raise RuntimeError(
                "Falta el paquete IANA: instala con `pip install tzdata` "
                "(o `poetry install` en enderman-agent)."
            ) from e
    return _MX_CENTRO


def get_current_datetime_mexico() -> str:
    """Fecha y hora actuales en México (zona horaria de centro: Querétaro, CDMX, etc.).

    Úsala cuando el usuario pregunte qué día o qué hora es, o cuando necesites
    hoy, mañana, o una fecha/hora reales al agendar, calcular días o validar
    sugerencias con respecto al reloj actual.

    Returns:
        Texto con fecha ISO, hora en 24h, día de la semana (español) y zona
        (America/Mexico_City).
    """
    now = datetime.now(_get_mexico_central())
    dias = (
        "lunes",
        "martes",
        "miércoles",
        "jueves",
        "viernes",
        "sábado",
        "domingo",
    )
    dia = dias[now.weekday()]
    return (
        f"Fecha (ISO, México centro): {now:%Y-%m-%d} | Día: {dia} | "
        f"Hora: {now:%H:%M} (24h) | Zona: {_MX_CENTRO_KEY}"
    )

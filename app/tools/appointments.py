import random
import string
from datetime import datetime

_WEEKDAY_HOURS = {
    0: (8, 0, 19, 0),
    1: (8, 0, 19, 0),
    2: (8, 0, 19, 0),
    3: (8, 0, 19, 0),
    4: (8, 0, 19, 0),
    5: (9, 0, 14, 0),
}


def _generate_folio() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"MIDAS-{suffix}"


def _within_business_hours(when: datetime) -> bool:
    hours = _WEEKDAY_HOURS.get(when.weekday())
    if hours is None:
        return False
    open_h, open_m, close_h, close_m = hours
    minutes = when.hour * 60 + when.minute
    open_minutes = open_h * 60 + open_m
    close_minutes = close_h * 60 + close_m
    return open_minutes <= minutes <= close_minutes


def schedule_appointment(
    customer_name: str,
    car_model: str,
    reason: str,
    preferred_date: str,
    preferred_time: str,
) -> str:
    """Agenda una cita en el taller Midas Querétaro.

    Úsala cuando el usuario quiera reservar, agendar o programar una visita
    al taller. Solo llámala cuando ya tengas los cinco datos requeridos.

    Args:
        customer_name: Nombre completo del cliente.
        car_model: Marca y modelo del auto (por ejemplo, "Nissan Sentra 2020").
        reason: Motivo de la visita (servicio o problema a revisar).
        preferred_date: Fecha preferida en formato YYYY-MM-DD.
        preferred_time: Hora preferida en formato HH:MM (24h).

    Horarios de atención válidos:
        - Lunes a viernes: 08:00 a 19:00
        - Sábado: 09:00 a 14:00
        - Domingo: cerrado

    Returns:
        Texto con la confirmación de la cita y un folio único,
        o un mensaje de error si la fecha/hora está fuera de horario
        o tiene formato inválido.
    """
    try:
        when = datetime.strptime(f"{preferred_date} {preferred_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return (
            "No pude registrar la cita: la fecha u hora tiene un formato inválido. "
            "Pide al cliente la fecha como YYYY-MM-DD y la hora como HH:MM (24h)."
        )

    if when.weekday() == 6:
        return (
            "No pude registrar la cita: el domingo el taller está cerrado. "
            "Sugiérele otro día. Horarios: L-V 8:00-19:00, Sáb 9:00-14:00."
        )

    if not _within_business_hours(when):
        return (
            "No pude registrar la cita: la hora está fuera de horario. "
            "Horarios: L-V 8:00-19:00, Sáb 9:00-14:00. Sugiérele un horario válido."
        )

    folio = _generate_folio()
    fecha_legible = when.strftime("%d/%m/%Y")
    hora_legible = when.strftime("%H:%M")
    return (
        f"Cita confirmada. Folio {folio} para {customer_name} "
        f"({car_model}) el {fecha_legible} a las {hora_legible}. "
        f"Motivo: {reason}. Te esperamos en Av. Luis Pasteur Sur 139, Querétaro."
    )

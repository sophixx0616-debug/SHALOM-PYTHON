"""Formatting and business-rule helpers shared by the routes and templates."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_EVEN

MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
MONTHS_ES_SHORT = [
    "ene", "feb", "mar", "abr", "may", "jun",
    "jul", "ago", "sept", "oct", "nov", "dic",
]
DAYS_ES = [
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo",
]
DAYS_ES_SHORT = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


def _as_decimal(value):
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def format_number(value, decimals=0):
    """Group thousands with '.' and use ',' for decimals (es-CO style)."""
    number = _as_decimal(value)
    quant = Decimal(1).scaleb(-decimals)
    number = number.quantize(quant, rounding=ROUND_HALF_EVEN)
    text = f"{number:,.{decimals}f}"
    return text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def format_currency(value):
    return "$" + format_number(value, 0)


def _day_parts(value):
    if isinstance(value, datetime):
        return value.date(), value.time()
    if isinstance(value, date):
        return value, None
    if isinstance(value, time):
        return None, value
    return None, None


def format_date_es(value, pattern="d 'de' MMMM 'de' yyyy"):
    """Small subset of Java DateTimeFormatter patterns used by the templates."""
    if value is None:
        return ""
    day, _ = _day_parts(value)
    if day is None:
        return ""
    # Literal text between single quotes (Thymeleaf/Java escaping).
    out = []
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "'":
            end = pattern.find("'", i + 1)
            if end == -1:
                out.append(pattern[i + 1:])
                break
            out.append(pattern[i + 1:end])
            i = end + 1
            continue
        if ch.isalpha():
            j = i
            while j < len(pattern) and pattern[j] == ch:
                j += 1
            token = pattern[i:j]
            out.append(_date_token(day, token))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _date_token(day, token):
    if token == "yyyy":
        return f"{day.year:04d}"
    if token == "yy":
        return f"{day.year % 100:02d}"
    if token == "MMMM":
        return MONTHS_ES[day.month - 1]
    if token == "MMM":
        return MONTHS_ES_SHORT[day.month - 1]
    if token == "MM":
        return f"{day.month:02d}"
    if token == "M":
        return str(day.month)
    if token == "dd":
        return f"{day.day:02d}"
    if token == "d":
        return str(day.day)
    if token == "EEEE":
        return DAYS_ES[day.weekday()]
    if token == "EEE":
        return DAYS_ES_SHORT[day.weekday()]
    return token


def _time_token(value, token):
    hour12 = value.hour % 12 or 12
    if token == "HH":
        return f"{value.hour:02d}"
    if token == "H":
        return str(value.hour)
    if token == "hh":
        return f"{hour12:02d}"
    if token == "h":
        return str(hour12)
    if token == "mm":
        return f"{value.minute:02d}"
    if token == "m":
        return str(value.minute)
    if token == "ss":
        return f"{value.second:02d}"
    if token == "a":
        return "a. m." if value.hour < 12 else "p. m."
    return token


def format_time_es(value, pattern="h:mm a"):
    if value is None:
        return ""
    _, clock = _day_parts(value)
    if clock is None:
        return ""
    out = []
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "'":
            end = pattern.find("'", i + 1)
            if end == -1:
                out.append(pattern[i + 1:])
                break
            out.append(pattern[i + 1:end])
            i = end + 1
            continue
        if ch.isalpha():
            j = i
            while j < len(pattern) and pattern[j] == ch:
                j += 1
            out.append(_time_token(clock, pattern[i:j]))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


TIME_TOKENS = ("HH", "H", "hh", "h", "mm", "m", "ss", "a")


def format_temporal_es(value, pattern="d 'de' MMMM 'de' yyyy"):
    """Format a date, time or datetime with the Java patterns used in the views."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        out = []
        i = 0
        while i < len(pattern):
            ch = pattern[i]
            if ch == "'":
                end = pattern.find("'", i + 1)
                if end == -1:
                    out.append(pattern[i + 1:])
                    break
                out.append(pattern[i + 1:end])
                i = end + 1
                continue
            if ch.isalpha():
                j = i
                while j < len(pattern) and pattern[j] == ch:
                    j += 1
                token = pattern[i:j]
                if token in TIME_TOKENS:
                    out.append(_time_token(value.time(), token))
                else:
                    out.append(_date_token(value.date(), token))
                i = j
                continue
            out.append(ch)
            i += 1
        return "".join(out)
    if isinstance(value, time):
        return format_time_es(value, pattern)
    return format_date_es(value, pattern)


def parse_date(value):
    if isinstance(value, date):
        return value
    return datetime.strptime((value or "").strip(), "%Y-%m-%d").date()


def parse_time(value):
    if isinstance(value, time):
        return value
    text = (value or "").strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    raise ValueError("invalid time")


OPENING_TIME = time(8, 0)
CLOSING_TIME = time(19, 0)


def validate_business_hours(appointment_date, start_time, duration_minutes):
    """Business rules ported from AppointmentController.validateBusinessHours."""
    if appointment_date is None or start_time is None:
        return "Debes seleccionar una fecha y una hora."

    today = date.today()
    now = datetime.now().time()

    if appointment_date < today:
        return "No puedes reservar una cita en una fecha anterior a hoy."
    if appointment_date == today and start_time <= now:
        return "No puedes reservar una hora que ya pasó."
    if appointment_date.weekday() == 6:  # Sunday
        return "El salón no atiende los domingos."

    if not duration_minutes or duration_minutes <= 0:
        duration_minutes = 30

    start_dt = datetime.combine(appointment_date, start_time)
    end_time = (start_dt + timedelta(minutes=duration_minutes)).time()

    if start_time < OPENING_TIME:
        return "El salón abre a las 8:00 a. m."
    if end_time > CLOSING_TIME:
        return "La cita no puede terminar después de las 7:00 p. m."

    return None


def has_conflict(appointment_date, start_time, end_time, worker, appointments, appointment_id=None):
    """Overlap detection ported from AppointmentController.hasConflict."""
    for existing in appointments:
        if appointment_id is not None and existing.id == appointment_id:
            continue
        if existing.date != appointment_date:
            continue
        if (existing.status or "").lower() == "cancelada":
            continue
        if worker and worker.strip():
            if not existing.worker or worker.lower() != existing.worker.lower():
                continue

        existing_duration = 30
        if existing.service and existing.service.duration and existing.service.duration > 0:
            existing_duration = existing.service.duration
        existing_start = existing.time
        existing_end = (
            datetime.combine(existing.date, existing_start) + timedelta(minutes=existing_duration)
        ).time()

        if start_time < existing_end and end_time > existing_start:
            return True
    return False

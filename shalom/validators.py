"""Reusable server-side validators for every form in the application.

The rules mirror the HTML5 constraints declared in the templates so a user can
never bypass the browser validation by posting the form directly.
"""

import re
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
NAME_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñÀÈÌÒÙàèìòùÂÊÎÔÛâêîôûÇç' .\-]+$")
PHONE_RE = re.compile(r"^[0-9+()\s.\-]{7,20}$")

MAX_TEXT = 255
MAX_LONG_TEXT = 1000
MIN_PASSWORD = 8
MAX_PASSWORD = 128
MAX_PRICE = Decimal("9999999.99")


def clean(value):
    """Trim a form value and convert ``None`` to an empty string."""
    return (value or "").strip() if isinstance(value, str) else ""


def validate_required(value, label, errors, field, max_length=MAX_TEXT, min_length=1):
    """Validate a required free-text field and return the cleaned value."""
    text = clean(value)
    if not text:
        errors[field] = f"{label} es obligatorio."
        return text
    if len(text) < min_length:
        errors[field] = f"{label} debe tener al menos {min_length} caracteres."
    elif len(text) > max_length:
        errors[field] = f"{label} no puede superar los {max_length} caracteres."
    return text


def validate_optional(value, label, errors, field, max_length=MAX_TEXT):
    text = clean(value)
    if len(text) > max_length:
        errors[field] = f"{label} no puede superar los {max_length} caracteres."
    return text


def validate_name(value, label, errors, field, required=True):
    text = clean(value)
    if not text:
        if required:
            errors[field] = f"{label} es obligatorio."
        return text
    if len(text) < 2:
        errors[field] = f"{label} debe tener al menos 2 caracteres."
    elif len(text) > 100:
        errors[field] = f"{label} no puede superar los 100 caracteres."
    elif not NAME_RE.match(text):
        errors[field] = f"{label} solo puede contener letras, espacios, apóstrofos y guiones."
    return text


def validate_email(value, errors, field="email", required=True):
    email = clean(value).lower()
    if not email:
        if required:
            errors[field] = "El correo electrónico es obligatorio."
        return email
    if len(email) > MAX_TEXT or not EMAIL_RE.match(email):
        errors[field] = "Ingresa un correo electrónico válido."
    return email


def validate_phone(value, errors, field="phone", required=False):
    phone = clean(value)
    if not phone:
        if required:
            errors[field] = "El teléfono es obligatorio."
        return phone
    if not PHONE_RE.match(phone):
        errors[field] = "El teléfono debe tener entre 7 y 15 dígitos y solo puede incluir +, -, espacios o paréntesis."
    else:
        digits = re.sub(r"\D", "", phone)
        if not 7 <= len(digits) <= 15:
            errors[field] = "El teléfono debe tener entre 7 y 15 dígitos."
    return phone


def validate_password(password, confirmation, errors, field="password", required=True):
    value = password or ""
    if not value:
        if required:
            errors[field] = "La contraseña es obligatoria."
        return value
    if len(value) < MIN_PASSWORD:
        errors[field] = f"La contraseña debe tener al menos {MIN_PASSWORD} caracteres."
    elif len(value) > MAX_PASSWORD:
        errors[field] = f"La contraseña no puede superar los {MAX_PASSWORD} caracteres."
    elif not re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]", value) or not re.search(r"\d", value):
        errors[field] = "La contraseña debe incluir al menos una letra y un número."
    elif confirmation is not None and value != confirmation:
        errors[field] = "Las contraseñas no coinciden."
    return value


def parse_int(value, errors, field, label, minimum=None, maximum=None):
    text = clean(value)
    if not text:
        errors[field] = f"{label} es obligatorio."
        return None
    try:
        number = int(text)
    except ValueError:
        errors[field] = f"{label} debe ser un número entero."
        return None
    if minimum is not None and number < minimum:
        errors[field] = f"{label} no puede ser menor que {minimum}."
        return None
    if maximum is not None and number > maximum:
        errors[field] = f"{label} no puede ser mayor que {maximum}."
        return None
    return number


def parse_decimal(value, errors, field, label, minimum=Decimal("0"), maximum=MAX_PRICE):
    text = clean(value).replace(",", ".")
    if not text:
        errors[field] = f"{label} es obligatorio."
        return None
    try:
        number = Decimal(text)
    except InvalidOperation:
        errors[field] = f"{label} debe ser un valor numérico válido."
        return None
    if number < minimum:
        errors[field] = f"{label} no puede ser menor que {minimum}."
        return None
    if number > maximum:
        errors[field] = f"{label} no puede ser mayor que {maximum}."
        return None
    if number.as_tuple().exponent < -2:
        errors[field] = f"{label} admite como máximo 2 decimales."
        return None
    return number


def parse_date_field(value, errors, field="date", label="La fecha"):
    text = clean(value)
    if not text:
        errors[field] = f"{label} es obligatoria."
        return None
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        errors[field] = f"{label} no tiene un formato válido."
        return None
    if parsed < date.today():
        errors[field] = "No puedes seleccionar una fecha anterior a hoy."
        return None
    return parsed


def parse_time_field(value, errors, field="time", label="La hora"):
    text = clean(value)
    if not text:
        errors[field] = f"{label} es obligatoria."
        return None
    parts = text.split(":")
    try:
        if len(parts) == 2:
            parsed = time(int(parts[0]), int(parts[1]))
        elif len(parts) == 3:
            parsed = time(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            raise ValueError
    except (TypeError, ValueError):
        errors[field] = f"{label} no tiene un formato válido."
        return None
    return parsed

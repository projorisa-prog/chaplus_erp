"""
utils.py
CHAPLUS PDF Utils
"""

from datetime import datetime

# ==============================================================================
# MONEY
# ==============================================================================

def money(value) -> str:
    """1000000 -> ₩1,000,000"""

    if value is None:
        return ""

    try:
        return f"₩{int(value):,}"
    except Exception:
        return ""


# ==============================================================================
# DATE
# ==============================================================================

def today() -> str:
    return datetime.now().strftime("%Y.%m.%d")


def format_date(value):

    if not value:
        return ""

    if isinstance(value, datetime):
        return value.strftime("%Y.%m.%d")

    try:
        return value.strftime("%Y.%m.%d")
    except Exception:
        return str(value)


def format_datetime(value):

    if not value:
        return ""

    if isinstance(value, datetime):
        return value.strftime("%Y.%m.%d %H:%M")

    try:
        return value.strftime("%Y.%m.%d %H:%M")
    except Exception:
        return str(value)


# ==============================================================================
# NUMBER → KOREAN
# ==============================================================================

_UNITS = ["", "만", "억", "조"]

_DIGITS = [
    "",
    "일",
    "이",
    "삼",
    "사",
    "오",
    "육",
    "칠",
    "팔",
    "구",
]

_PLACES = [
    "",
    "십",
    "백",
    "천",
]


def number_to_korean(number: int) -> str:

    if not number:
        return "영원정"

    number = int(number)

    result = ""
    unit = 0

    while number > 0:

        group = number % 10000

        if group:

            text = ""

            for i, d in enumerate(str(group).zfill(4)):

                digit = int(d)

                if digit == 0:
                    continue

                if not (digit == 1 and i != 3):
                    text += _DIGITS[digit]

                text += _PLACES[3 - i]

            result = text + _UNITS[unit] + result

        unit += 1
        number //= 10000

    return result + "원정"


# ==============================================================================
# TEXT
# ==============================================================================

def empty(value, default=""):

    if value is None:
        return default

    return str(value)


def yes_no(value):

    return "예" if value else "아니오"


# ==============================================================================
# COMPANY
# ==============================================================================

def company_value(settings: dict, key: str) -> str:

    if not settings:
        return ""

    return settings.get(key, "")


# ==============================================================================
# VAT
# ==============================================================================

def calculate_amount(total: int, vat_type: str):

    """
    return

    supply
    vat
    final
    """

    total = int(total or 0)

    if vat_type == "별도":

        supply = total
        vat = int(supply * 0.1)
        final = supply + vat

    elif vat_type == "포함":

        final = total
        supply = int(final / 1.1)
        vat = final - supply

    else:

        supply = total
        vat = 0
        final = total

    return supply, vat, final
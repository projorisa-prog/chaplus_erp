"""
theme.py
CHAPLUS PDF Theme
"""

import os

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ==============================================================================
# PAGE
# ==============================================================================

PAGE_WIDTH = 297 * mm
PAGE_HEIGHT = 210 * mm

MARGIN_LEFT = 14 * mm
MARGIN_RIGHT = 14 * mm
MARGIN_TOP = 12 * mm
MARGIN_BOTTOM = 12 * mm

CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT

# ==============================================================================
# COLOR
# ==============================================================================

PRIMARY = colors.HexColor("#4F8EF7")
PRIMARY_LIGHT = colors.HexColor("#EAF3FF")

SECONDARY = colors.HexColor("#7DB5FF")

SUCCESS = colors.HexColor("#14B8A6")

WARNING = colors.HexColor("#F59E0B")

DANGER = colors.HexColor("#EF4444")

TEXT = colors.HexColor("#334155")

TEXT_LIGHT = colors.HexColor("#64748B")

TEXT_MUTED = colors.HexColor("#94A3B8")

LINE = colors.HexColor("#E2E8F0")

CARD = colors.white

BACKGROUND = colors.HexColor("#F8FAFC")

WHITE = colors.white

# ==============================================================================
# FONT
# ==============================================================================

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

_registered = False


def register_fonts():
    global FONT
    global FONT_BOLD
    global _registered

    if _registered:
        return

    base = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "fonts"
        )
    )

    candidates = [

        ("NanumBarunGothic", os.path.join(base, "NanumBarunGothic.ttf")),

        ("NanumGothic", os.path.join(base, "NanumGothic.ttf")),

        ("MalgunGothic", r"C:\Windows\Fonts\malgun.ttf"),

    ]

    for name, path in candidates:

        if not os.path.exists(path):
            continue

        try:

            pdfmetrics.registerFont(
                TTFont(name, path)
            )

            FONT = name
            FONT_BOLD = name
            break

        except Exception:
            pass

    _registered = True


# ==============================================================================
# LOGO
# ==============================================================================

def logo_path():

    candidates = [

        os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "img",
                "chaplus_logo.png"
            )
        ),

        r"D:\chaplus_erp\img\chaplus_logo.png",

        r"D:\chaplus.erp\img\chaplus_logo.png",

    ]

    for path in candidates:

        if os.path.exists(path):
            return path

    return None


# ==============================================================================
# SIZE
# ==============================================================================

RADIUS = 6

CARD_PADDING = 6 * mm

HEADER_HEIGHT = 24 * mm

FOOTER_HEIGHT = 10 * mm

ROW_HEIGHT = 8 * mm

TABLE_HEADER_HEIGHT = 9 * mm

# ==============================================================================
# FONT SIZE
# ==============================================================================

TITLE_SIZE = 22

SUBTITLE_SIZE = 11

BODY_SIZE = 9

SMALL_SIZE = 8

TINY_SIZE = 7
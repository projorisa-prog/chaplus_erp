"""
components.py
"""

from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader

from .theme import *
from .utils import *

# ==============================================================================
# Paragraph
# ==============================================================================

def p(text, align=TA_LEFT, size=BODY_SIZE, bold=False, color=TEXT):

    register_fonts()

    return Paragraph(

        str(text if text is not None else ""),

        ParagraphStyle(

            "default",

            fontName=FONT_BOLD if bold else FONT,

            fontSize=size,

            leading=size + 3,

            alignment=align,

            textColor=color,

            wordWrap="CJK",

        )

    )


# ==============================================================================
# TEXT
# ==============================================================================

def draw_text(
    canvas,
    x,
    y,
    text,
    size=BODY_SIZE,
    color=TEXT,
    bold=False,
    align="left",
):

    register_fonts()

    canvas.saveState()

    canvas.setFont(
        FONT_BOLD if bold else FONT,
        size,
    )

    canvas.setFillColor(color)

    text = str(text if text is not None else "")

    if align == "center":

        canvas.drawCentredString(x, y, text)

    elif align == "right":

        canvas.drawRightString(x, y, text)

    else:

        canvas.drawString(x, y, text)

    canvas.restoreState()


# ==============================================================================
# LINE
# ==============================================================================

def draw_line(
    canvas,
    x1,
    y1,
    x2,
    y2,
    color=LINE,
    width=0.5,
):

    canvas.saveState()

    canvas.setStrokeColor(color)

    canvas.setLineWidth(width)

    canvas.line(x1, y1, x2, y2)

    canvas.restoreState()


# ==============================================================================
# CARD
# ==============================================================================

def draw_card(
    canvas,
    x,
    y,
    width,
    height,
):

    canvas.saveState()

    canvas.setFillColor(CARD)

    canvas.setStrokeColor(LINE)

    canvas.setLineWidth(0.8)

    canvas.roundRect(
        x,
        y,
        width,
        height,
        RADIUS,
        fill=1,
        stroke=1,
    )

    canvas.restoreState()


# ==============================================================================
# LOGO
# ==============================================================================

def draw_logo(canvas):

    path = logo_path()

    if not path:
        return

    img = ImageReader(path)

    canvas.drawImage(

        img,

        MARGIN_LEFT,

        PAGE_HEIGHT - 24 * mm,

        width=38 * mm,

        height=18 * mm,

        preserveAspectRatio=True,

        mask="auto",

    )


# ==============================================================================
# HEADER
# ==============================================================================

def draw_header(
    canvas,
    title,
    doc_no,
    issue_date,
):

    draw_logo(canvas)

    draw_text(

        canvas,

        PAGE_WIDTH / 2,

        PAGE_HEIGHT - 18 * mm,

        title,

        size=TITLE_SIZE,

        bold=True,

        align="center",

    )

    draw_text(

        canvas,

        PAGE_WIDTH / 2,

        PAGE_HEIGHT - 24 * mm,

        "VIP Chauffeur Service",

        size=SMALL_SIZE,

        color=TEXT_LIGHT,

        align="center",

    )

    x = PAGE_WIDTH - MARGIN_RIGHT - 45 * mm

    y = PAGE_HEIGHT - 14 * mm

    draw_text(canvas, x, y, "문서번호", SMALL_SIZE, TEXT_LIGHT)
    draw_text(canvas, PAGE_WIDTH - MARGIN_RIGHT, y, doc_no,
              SMALL_SIZE, align="right")

    y -= 5 * mm

    draw_text(canvas, x, y, "발행일", SMALL_SIZE, TEXT_LIGHT)
    draw_text(canvas, PAGE_WIDTH - MARGIN_RIGHT, y, issue_date,
              SMALL_SIZE, align="right")

    draw_line(

        canvas,

        MARGIN_LEFT,

        PAGE_HEIGHT - HEADER_HEIGHT,

        PAGE_WIDTH - MARGIN_RIGHT,

        PAGE_HEIGHT - HEADER_HEIGHT,

    )


# ==============================================================================
# INFO CARD
# ==============================================================================

def draw_info_card(
    canvas,
    x,
    y,
    width,
    height,
    title,
    rows,
):

    draw_card(
        canvas,
        x,
        y,
        width,
        height,
    )

    draw_text(

        canvas,

        x + 5 * mm,

        y + height - 7 * mm,

        title,

        size=SUBTITLE_SIZE,

        bold=True,

        color=PRIMARY,

    )

    yy = y + height - 15 * mm

    for label, value in rows:

        draw_text(

            canvas,

            x + 5 * mm,

            yy,

            label,

            SMALL_SIZE,

            TEXT_LIGHT,

        )

        draw_text(

            canvas,

            x + 22 * mm,

            yy,

            value,

            SMALL_SIZE,

        )

        yy -= 5 * mm


# ==============================================================================
# FOOTER
# ==============================================================================

def draw_footer(canvas):

    draw_line(

        canvas,

        MARGIN_LEFT,

        MARGIN_BOTTOM + 6 * mm,

        PAGE_WIDTH - MARGIN_RIGHT,

        MARGIN_BOTTOM + 6 * mm,

    )

    draw_text(

        canvas,

        MARGIN_LEFT,

        MARGIN_BOTTOM + 2 * mm,

        "CHAPLUS VIP Chauffeur Service",

        TINY_SIZE,

        TEXT_LIGHT,

    )

    draw_text(

        canvas,

        PAGE_WIDTH - MARGIN_RIGHT,

        MARGIN_BOTTOM + 2 * mm,

        datetime.now().strftime("%Y.%m.%d"),

        TINY_SIZE,

        TEXT_LIGHT,

        align="right",

    )
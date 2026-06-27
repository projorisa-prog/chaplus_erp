"""
invoice.py
"""

import io

from reportlab.pdfgen import canvas

from .theme import *
from .utils import *
from .components import *
from .tables import *


def generate_invoice_pdf(order, settings):

    register_fonts()

    buffer = io.BytesIO()

    c = canvas.Canvas(
        buffer,
        pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
    )

    client = order.client

    vat_type = client.vat_type or "별도"

    issue_date = today()

    period = (
        f"{format_datetime(order.start_datetime)}"
        f" ~ "
        f"{format_datetime(order.end_datetime)}"
    )

    # =====================================================================
    # HEADER
    # =====================================================================

    draw_header(
        c,
        "청 구 서",
        order.id,
        issue_date,
    )

    y = PAGE_HEIGHT - HEADER_HEIGHT - 10 * mm

    # =====================================================================
    # RECEIVER
    # =====================================================================

    left_width = CONTENT_WIDTH * 0.42
    right_width = CONTENT_WIDTH - left_width - 6 * mm

    card_height = 42 * mm

    draw_info_card(
        c,
        MARGIN_LEFT,
        y - card_height,
        left_width,
        card_height,
        "청구처",
        [
            ("거래처", client.name),
            ("담당자", getattr(client, "manager", "")),
            ("연락처", getattr(client, "phone", "")),
            ("청구번호", order.id),
        ],
    )

    draw_info_card(
        c,
        MARGIN_LEFT + left_width + 6 * mm,
        y - card_height,
        right_width,
        card_height,
        "공급자",
        [
            ("상호", company_value(settings, "company_name")),
            ("대표", company_value(settings, "ceo_name")),
            ("사업자", company_value(settings, "business_no")),
            ("TEL", company_value(settings, "phone")),
            ("E-Mail", company_value(settings, "email")),
        ],
    )

    y -= card_height + 8 * mm

    # =====================================================================
    # SUMMARY
    # =====================================================================

    draw_card(
        c,
        MARGIN_LEFT,
        y - 12 * mm,
        CONTENT_WIDTH,
        12 * mm,
    )

    draw_text(
        c,
        MARGIN_LEFT + 5 * mm,
        y - 7 * mm,
        "운행기간",
        SMALL_SIZE,
        TEXT_LIGHT,
    )

    draw_text(
        c,
        MARGIN_LEFT + 25 * mm,
        y - 7 * mm,
        period,
        BODY_SIZE,
        bold=True,
    )

    y -= 18 * mm

    # =====================================================================
    # TABLE
    # =====================================================================

    table, total = create_invoice_table(
        order.details
    )

    table.wrapOn(
        c,
        CONTENT_WIDTH,
        PAGE_HEIGHT,
    )

    _, table_height = table.wrap(
        CONTENT_WIDTH,
        PAGE_HEIGHT,
    )

    table.drawOn(
        c,
        MARGIN_LEFT,
        y - table_height,
    )

    y -= table_height + 8 * mm

    # =====================================================================
    # TOTAL
    # =====================================================================

    supply, vat, final = calculate_amount(
        total,
        vat_type,
    )

    total_width = 72 * mm
    total_height = 34 * mm

    x = PAGE_WIDTH - MARGIN_RIGHT - total_width

    draw_card(
        c,
        x,
        y - total_height,
        total_width,
        total_height,
    )

    draw_text(
        c,
        x + 5 * mm,
        y - 7 * mm,
        "공급가액",
        SMALL_SIZE,
        TEXT_LIGHT,
    )

    draw_text(
        c,
        x + total_width - 5 * mm,
        y - 7 * mm,
        money(supply),
        SMALL_SIZE,
        align="right",
    )

    draw_text(
        c,
        x + 5 * mm,
        y - 14 * mm,
        "부가세",
        SMALL_SIZE,
        TEXT_LIGHT,
    )

    draw_text(
        c,
        x + total_width - 5 * mm,
        y - 14 * mm,
        money(vat),
        SMALL_SIZE,
        align="right",
    )

    draw_line(
        c,
        x + 5 * mm,
        y - 19 * mm,
        x + total_width - 5 * mm,
        y - 19 * mm,
    )

    draw_text(
        c,
        x + 5 * mm,
        y - 28 * mm,
        "청구금액",
        SUBTITLE_SIZE,
        PRIMARY,
        bold=True,
    )

    draw_text(
        c,
        x + total_width - 5 * mm,
        y - 28 * mm,
        money(final),
        SUBTITLE_SIZE,
        PRIMARY,
        bold=True,
        align="right",
    )

    # =====================================================================
    # PAYMENT
    # =====================================================================

    note_width = CONTENT_WIDTH - total_width - 8 * mm

    draw_card(
        c,
        MARGIN_LEFT,
        y - total_height,
        note_width,
        total_height,
    )

    draw_text(
        c,
        MARGIN_LEFT + 5 * mm,
        y - 7 * mm,
        "입금안내",
        SMALL_SIZE,
        PRIMARY,
        bold=True,
    )

    lines = [

        f"은행 : {company_value(settings,'bank_name')}",

        f"계좌 : {company_value(settings,'bank_account')}",

        f"예금주 : {company_value(settings,'bank_holder')}",

        "세금계산서 발행 가능합니다.",

    ]

    yy = y - 13 * mm

    for line in lines:

        draw_text(
            c,
            MARGIN_LEFT + 5 * mm,
            yy,
            line,
            TINY_SIZE,
            TEXT_LIGHT,
        )

        yy -= 4 * mm

    # =====================================================================
    # FOOTER
    # =====================================================================

    draw_footer(c)

    c.save()

    buffer.seek(0)

    return buffer
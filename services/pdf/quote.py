"""
quote.py
"""

import io

from reportlab.pdfgen import canvas

from .theme import *
from .utils import *
from .components import *
from .tables import *


def generate_quote_pdf(quote, settings):

    register_fonts()

    buffer = io.BytesIO()

    c = canvas.Canvas(
        buffer,
        pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
    )

    client = quote.client

    vat_type = client.vat_type or "별도"

    issue_date = today()

    period = f"{format_datetime(quote.start_datetime)} ~ {format_datetime(quote.end_datetime)}"

    # ==========================================================================
    # HEADER
    # ==========================================================================

    draw_header(
        c,
        "견 적 서",
        quote.id,
        issue_date,
    )

    y = PAGE_HEIGHT - HEADER_HEIGHT - 10 * mm

    # ==========================================================================
    # RECEIVER
    # ==========================================================================

    left_width = CONTENT_WIDTH * 0.42
    right_width = CONTENT_WIDTH - left_width - 6 * mm

    card_height = 42 * mm

    draw_info_card(
        c,
        MARGIN_LEFT,
        y - card_height,
        left_width,
        card_height,
        "수신",
        [
            ("거래처", client.name),
            ("담당자", getattr(client, "manager", "")),
            ("연락처", getattr(client, "phone", "")),
            ("문서번호", quote.id),
        ],
    )

    draw_info_card(
        c,
        MARGIN_LEFT + left_width + 6 * mm,
        y - card_height,
        right_width,
        card_height,
        "발신",
        [
            ("상호", company_value(settings, "company_name")),
            ("대표", company_value(settings, "ceo_name")),
            ("사업자", company_value(settings, "business_no")),
            ("TEL", company_value(settings, "phone")),
            ("E-Mail", company_value(settings, "email")),
        ],
    )

    y -= card_height + 8 * mm

    # ==========================================================================
    # SUMMARY
    # ==========================================================================

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

    # ==========================================================================
    # TABLE
    # ==========================================================================

    table, total = create_quote_table(
        quote.details
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

    # ==========================================================================
    # TOTAL
    # ==========================================================================

    supply, vat, final = calculate_amount(
        total,
        vat_type,
    )

    total_width = 72 * mm
    total_height = 30 * mm

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
        y - 13 * mm,
        "부가세",
        SMALL_SIZE,
        TEXT_LIGHT,
    )

    draw_text(
        c,
        x + total_width - 5 * mm,
        y - 13 * mm,
        money(vat),
        SMALL_SIZE,
        align="right",
    )

    draw_line(
        c,
        x + 5 * mm,
        y - 17 * mm,
        x + total_width - 5 * mm,
        y - 17 * mm,
    )

    draw_text(
        c,
        x + 5 * mm,
        y - 24 * mm,
        "TOTAL",
        SUBTITLE_SIZE,
        PRIMARY,
        bold=True,
    )

    draw_text(
        c,
        x + total_width - 5 * mm,
        y - 24 * mm,
        money(final),
        SUBTITLE_SIZE,
        PRIMARY,
        bold=True,
        align="right",
    )

    # ==========================================================================
    # NOTE
    # ==========================================================================

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
        "안내사항",
        SMALL_SIZE,
        PRIMARY,
        bold=True,
    )

    notes = [

        "• 단가에는 차량, 기사, 유류비가 포함됩니다.",

        "• 지방 운행은 지역할증이 적용됩니다.",

        "• 추가시간은 별도 청구됩니다.",

        "• 카드결제 및 세금계산서 발행 가능합니다.",

    ]

    yy = y - 13 * mm

    for note in notes:

        draw_text(
            c,
            MARGIN_LEFT + 5 * mm,
            yy,
            note,
            TINY_SIZE,
            TEXT_LIGHT,
        )

        yy -= 4 * mm

    # ==========================================================================
    # FOOTER
    # ==========================================================================

    draw_footer(c)

    c.save()

    buffer.seek(0)

    return buffer
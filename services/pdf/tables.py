"""
tables.py
"""

from reportlab.platypus import Table
from reportlab.platypus import TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from .theme import *
from .components import p

# ==============================================================================
# TABLE STYLE
# ==============================================================================

def quote_table_style():

    return TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),

        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),

        ("FONTNAME", (0, 0), (-1, -1), FONT),

        ("FONTSIZE", (0, 0), (-1, 0), SMALL_SIZE),

        ("FONTSIZE", (0, 1), (-1, -1), SMALL_SIZE),

        ("ALIGN", (0, 0), (-1, -1), "CENTER"),

        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),

        ("TOPPADDING", (0, 0), (-1, 0), 7),

        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),

        ("TOPPADDING", (0, 1), (-1, -1), 6),

        ("LINEBELOW", (0, 0), (-1, 0), 0.8, LINE),

        ("LINEBELOW", (0, 1), (-1, -1), 0.25, LINE),

        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            WHITE,
            BACKGROUND,
        ]),

        ("LEFTPADDING", (0, 0), (-1, -1), 4),

        ("RIGHTPADDING", (0, 0), (-1, -1), 4),

    ])


# ==============================================================================
# QUOTE TABLE
# ==============================================================================

def create_quote_table(details):

    headers = [

        p("날짜", TA_CENTER, bold=True, color=WHITE),

        p("구분", TA_CENTER, bold=True, color=WHITE),

        p("차량", TA_CENTER, bold=True, color=WHITE),

        p("포함내역", TA_CENTER, bold=True, color=WHITE),

        p("수량", TA_CENTER, bold=True, color=WHITE),

        p("단가", TA_CENTER, bold=True, color=WHITE),

        p("지역", TA_CENTER, bold=True, color=WHITE),

        p("지역할증", TA_CENTER, bold=True, color=WHITE),

        p("이용시간", TA_CENTER, bold=True, color=WHITE),

        p("OT", TA_CENTER, bold=True, color=WHITE),

        p("숙식", TA_CENTER, bold=True, color=WHITE),

        p("금액", TA_CENTER, bold=True, color=WHITE),

    ]

    rows = [headers]

    total = 0

    for item in details:

        amount = (

            (item.unit_price * item.qty)

            + item.region_surcharge

            + item.time_surcharge

            + item.lodging_fee

        )

        total += amount

        vehicle = ""

        if item.vehicle:

            vehicle = item.vehicle.name

            if item.vehicle.capacity:

                vehicle += f" ({item.vehicle.capacity}인승)"

        rows.append([

            p(item.run_date or "", TA_CENTER),

            p(item.product_type or "", TA_CENTER),

            p(vehicle, TA_LEFT),

            p(item.includes or "", TA_LEFT),

            p(item.qty),

            p(f"{item.unit_price:,}", TA_RIGHT),

            p(item.region or "", TA_LEFT),

            p(f"{item.region_surcharge:,}" if item.region_surcharge else "", TA_RIGHT),

            p(item.use_time or "", TA_CENTER),

            p(item.extra_time if item.extra_time else "", TA_CENTER),

            p(f"{item.lodging_fee:,}" if item.lodging_fee else "", TA_RIGHT),

            p(
                f"{amount:,}",
                TA_RIGHT,
                bold=True,
                color=PRIMARY,
            ),

        ])

    widths = [

        20*mm,
        16*mm,
        26*mm,
        55*mm,
        12*mm,
        22*mm,
        24*mm,
        20*mm,
        18*mm,
        10*mm,
        18*mm,
        24*mm,

    ]

    table = Table(
        rows,
        colWidths=widths,
        repeatRows=1,
    )

    table.setStyle(
        quote_table_style()
    )

    return table, total


# ==============================================================================
# INVOICE TABLE
# ==============================================================================

def create_invoice_table(details):

    headers = [

        p("날짜", TA_CENTER, bold=True, color=WHITE),

        p("차량", TA_CENTER, bold=True, color=WHITE),

        p("시작", TA_CENTER, bold=True, color=WHITE),

        p("종료", TA_CENTER, bold=True, color=WHITE),

        p("추가", TA_CENTER, bold=True, color=WHITE),

        p("시간할증", TA_CENTER, bold=True, color=WHITE),

        p("지역", TA_CENTER, bold=True, color=WHITE),

        p("지역할증", TA_CENTER, bold=True, color=WHITE),

        p("숙식", TA_CENTER, bold=True, color=WHITE),

        p("금액", TA_CENTER, bold=True, color=WHITE),

    ]

    rows = [headers]

    total = 0

    for item in details:

        amount = (

            item.unit_price

            + item.time_surcharge

            + item.region_surcharge

            + item.lodging_fee

        )

        total += amount

        vehicle = ""

        if item.vehicle:

            vehicle = item.vehicle.name

            if item.vehicle.capacity:

                vehicle += f" ({item.vehicle.capacity}인승)"

        rows.append([

            p(item.run_date or "", TA_CENTER),

            p(vehicle, TA_LEFT),

            p(item.start_time or "", TA_CENTER),

            p(item.end_time or "", TA_CENTER),

            p(item.extra_time if item.extra_time else "", TA_CENTER),

            p(f"{item.time_surcharge:,}" if item.time_surcharge else "", TA_RIGHT),

            p(item.region or "", TA_LEFT),

            p(f"{item.region_surcharge:,}" if item.region_surcharge else "", TA_RIGHT),

            p(f"{item.lodging_fee:,}" if item.lodging_fee else "", TA_RIGHT),

            p(
                f"{amount:,}",
                TA_RIGHT,
                bold=True,
                color=PRIMARY,
            ),

        ])

    widths = [

        22*mm,
        34*mm,
        18*mm,
        18*mm,
        12*mm,
        24*mm,
        28*mm,
        22*mm,
        18*mm,
        28*mm,

    ]

    table = Table(
        rows,
        colWidths=widths,
        repeatRows=1,
    )

    table.setStyle(
        quote_table_style()
    )

    return table, total
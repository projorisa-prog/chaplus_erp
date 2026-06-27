"""
견적서 / 청구서 PDF 생성 서비스
ReportLab 직접 드로잉 방식 - 현대적 디자인
"""
import io, os
from datetime import datetime
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── 페이지 설정 (A4 가로) ─────────────────
PW, PH = 297*mm, 210*mm
ML, MR, MT, MB = 14*mm, 14*mm, 12*mm, 12*mm
CW = PW - ML - MR

# ── 컬러 팔레트 ───────────────────────────
C_NAVY   = colors.HexColor('#1B2A4A')
C_BLUE   = colors.HexColor('#2563EB')
C_LBLUE  = colors.HexColor('#EFF6FF')
C_RED    = colors.HexColor('#991B1B')
C_LRED   = colors.HexColor('#FEF2F2')
C_GRAY1  = colors.HexColor('#F8FAFC')
C_GRAY2  = colors.HexColor('#E2E8F0')
C_GRAY3  = colors.HexColor('#64748B')
C_BLACK  = colors.HexColor('#1E293B')
C_WHITE  = colors.white

_FONT_REG = False
_FN = 'Helvetica'
_FB = 'Helvetica-Bold'


def _register():
    global _FONT_REG, _FN, _FB
    if _FONT_REG:
        return
    base = os.path.join(os.path.dirname(__file__), '..', 'fonts')
    candidates = [
        ('NanumBarunGothic', os.path.join(base, 'NanumBarunGothic.ttf')),
        ('NanumBarunGothic', os.path.join(base, 'NanumBarunGothic.ttf').replace('/', '\\')),
        ('MalgunGothic',     r'C:\Windows\Fonts\malgun.ttf'),
        ('MalgunGothic',     r'C:\Windows\Fonts\malgunbd.ttf'),
    ]
    for name, path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                _FN = name
                _FB = name
                _FONT_REG = True
                break
            except Exception:
                pass
    _FONT_REG = True


def fn(): _register(); return _FN
def fb(): _register(); return _FB


# ── 기본 드로잉 헬퍼 ─────────────────────
def rect(c, x, y, w, h, fill=None, stroke=None, lw=0.5, radius=0):
    c.saveState()
    if lw:
        c.setLineWidth(lw)
    if fill:
        c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
    if radius:
        c.roundRect(x, y, w, h, radius, fill=1 if fill else 0, stroke=1 if stroke else 0)
    else:
        c.rect(x, y, w, h, fill=1 if fill else 0, stroke=1 if stroke else 0)
    c.restoreState()


def txt(c, x, y, s, font=None, size=9, color=C_BLACK, align='left', bold=False):
    c.saveState()
    c.setFont(fb() if bold else (font or fn()), size)
    c.setFillColor(color)
    s = str(s)
    if align == 'center':
        c.drawCentredString(x, y, s)
    elif align == 'right':
        c.drawRightString(x, y, s)
    else:
        c.drawString(x, y, s)
    c.restoreState()


def line(c, x1, y1, x2, y2, color=C_GRAY2, lw=0.5):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.line(x1, y1, x2, y2)
    c.restoreState()


def money(n):
    return f'₩{int(n or 0):,}' if n else ''


# ── 공통 헤더 그리기 ──────────────────────
def _draw_header(c, doc_title, title_color, bg_color,
                 doc_id, client, settings, today, period):
    _register()
    y = PH - MT

    # 상단 컬러 바
    bar_h = 10*mm
    rect(c, 0, y - bar_h, PW, bar_h, fill=title_color)
    txt(c, PW/2, y - bar_h + 3*mm, doc_title, size=16, color=C_WHITE, bold=True, align='center')
    txt(c, PW - MR, y - bar_h + 3*mm,
        settings.get('company_name', '차플러스'),
        size=11, color=C_WHITE, align='right', bold=True)

    y -= bar_h + 5*mm

    # ── 왼쪽: 수신 정보 ─────────────────────
    lx = ML
    bw = CW * 0.42
    bh = 38*mm

    rect(c, lx, y - bh, bw, bh, fill=C_GRAY1, stroke=C_GRAY2, lw=0.5)
    rect(c, lx, y - 7*mm, bw, 7*mm, fill=bg_color)
    txt(c, lx + bw/2, y - 5.5*mm, '수  신', size=9, color=C_WHITE, align='center', bold=True)

    ry = y - 10*mm
    recv_rows = [
        ('거래처', client.name, True),
        ('문서ID', doc_id, False),
        ('발행일', today, False),
     ]
    for lbl, val, bold_val in recv_rows:
        txt(c, lx + 3*mm, ry, lbl, size=7.5, color=C_GRAY3)
        txt(c, lx + 18*mm, ry, val, size=9 if bold_val else 8,
            color=C_BLACK, bold=bold_val)
        ry -= 5*mm

    # ── 오른쪽: 발신 정보 ────────────────────
    rx = ML + bw + 6*mm
    rw = CW - bw - 6*mm

    rect(c, rx, y - bh, rw, bh, fill=C_GRAY1, stroke=C_GRAY2, lw=0.5)
    rect(c, rx, y - 7*mm, rw, 7*mm, fill=bg_color)
    txt(c, rx + rw/2, y - 5.5*mm, '발  신', size=9, color=C_WHITE, align='center', bold=True)

    comp   = settings.get('company_name', '차플러스')
    ceo    = settings.get('ceo_name', '')
    biz    = settings.get('business_no', '')
    addr   = settings.get('address', '')
    phone  = settings.get('phone', '')
    email  = settings.get('email', '')
    bank_n = settings.get('bank_name', '')
    bank_a = settings.get('bank_account', '')
    bank_h = settings.get('bank_holder', '')

    ry2 = y - 10*mm
    send_rows = [
        ('상  호', comp, True),
        ('대  표', ceo, False),
        ('사업자', biz, False),
        ('주  소', addr[:28] if addr else '', False),
        ('TEL',   phone, False),
        ('E-Mail', email, False),
    ]
    for lbl, val, bold_val in send_rows:
        txt(c, rx + 3*mm, ry2, lbl, size=7.5, color=C_GRAY3)
        txt(c, rx + 18*mm, ry2, val, size=8.5 if bold_val else 8,
            color=C_BLACK, bold=bold_val)
        ry2 -= 5*mm

    y -= bh + 4*mm

    # ── 기간 + 금액 요약 바 ──────────────────
    sb_h = 9*mm
    rect(c, ML, y - sb_h, CW, sb_h, fill=bg_color, radius=2)

    txt(c, ML + 4*mm, y - 6*mm, '제목: 기사포함렌터카', size=9, color=C_WHITE, bold=True)
    txt(c, ML + CW/2, y - 6*mm, '운행기간 : ', size=8, color=C_WHITE, align='right')
    txt(c, ML + CW/2 + 2*mm, y - 6*mm, period, size=9, color=C_WHITE, bold=True)

    y -= sb_h + 3*mm
    return y


# ── 명세 테이블 공통 ──────────────────────
def _table_style(hdr_color):
    return TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), hdr_color),
        ('TEXTCOLOR',     (0, 0), (-1, 0), C_WHITE),
        ('FONTNAME',      (0, 0), (-1, -1), fn()),
        ('FONTSIZE',      (0, 0), (-1, 0), 8),
        ('FONTSIZE',      (0, 1), (-1, -1), 7.5),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [C_WHITE, C_GRAY1]),
        ('GRID',          (0, 0), (-1, -1), 0.3, C_GRAY2),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 3),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 3),
    ])


def p(text, align='center', size=7.5, bold=False, color=C_BLACK):
    _register()
    al = TA_CENTER if align == 'center' else (TA_RIGHT if align == 'right' else TA_LEFT)
    return Paragraph(str(text), ParagraphStyle('x',
        fontName=fb() if bold else fn(),
        fontSize=size, alignment=al,
        textColor=color, leading=10, wordWrap='CJK'))


# ── 합계 섹션 ─────────────────────────────
def _draw_total(c, y, total, vat_type, bg_color):
    # vat_type별 금액 계산
    if vat_type == '별도':
        supply = total
        vat    = int(supply * 0.1)
        final  = supply + vat
    elif vat_type == '포함':
        final  = total
        supply = int(total / 1.1)
        vat    = final - supply
    else:  # 면세
        final  = total
        supply = None
        vat    = None

    th = 14*mm

    if vat_type == '면세':
        # 합계금액만 표시
        rect(c, ML, y - th, CW, th, fill=bg_color, radius=0)
        txt(c, ML + 4*mm, y - th/2 + 1*mm, '합계금액 (면세)', size=7.5, color=C_WHITE)
        txt(c, ML + CW - 4*mm, y - th/2 - 1*mm,
            f'₩{final:,}', size=11, color=C_WHITE, align='right', bold=True)
    else:
        col_w = CW / 3
        rect(c, ML, y - th, CW, th, fill=C_GRAY1, stroke=C_GRAY2, lw=0.5)

        txt(c, ML + col_w * 0 + 4*mm, y - th/2 - 1*mm, '공급가액', size=7.5, color=C_GRAY3)
        txt(c, ML + col_w * 1 - 4*mm, y - th/2 - 1*mm,
            f'₩{supply:,}', size=9, align='right', bold=True)

        txt(c, ML + col_w * 1 + 4*mm, y - th/2 - 1*mm, '부가세 (10%)', size=7.5, color=C_GRAY3)
        txt(c, ML + col_w * 2 - 4*mm, y - th/2 - 1*mm,
            f'₩{vat:,}', size=9, align='right')

        rect(c, ML + col_w * 2, y - th, col_w, th, fill=bg_color, radius=0)
        txt(c, ML + col_w * 2 + 4*mm, y - th/2 - 1*mm, '합계금액', size=7.5, color=C_WHITE)
        txt(c, ML + CW - 4*mm, y - th/2 - 1*mm,
            f'₩{final:,}', size=11, color=C_WHITE, align='right', bold=True)

        line(c, ML + col_w,   y, ML + col_w,   y - th, color=C_GRAY2)
        line(c, ML + col_w*2, y, ML + col_w*2, y - th, color=C_WHITE)

    return y - th - 3*mm, final


# ── NOTE 섹션 ────────────────────────────
def _draw_note(c, y, lines_text):
    txt(c, ML, y - 4*mm, 'NOTE', size=8, bold=True, color=C_GRAY3)
    ny = y - 8*mm
    for t in lines_text:
        txt(c, ML + 2*mm, ny, f'· {t}', size=7, color=C_GRAY3)
        ny -= 4*mm


# ═══════════════════════════════════════════
# 견적서 PDF
# ═══════════════════════════════════════════
def generate_quote_pdf(quote, settings):
    _register()
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(PW, PH))
    c.setTitle(f'견적서_{quote.id}')

    client   = quote.client
    vat_type = client.vat_type or '별도'
    today    = datetime.today().strftime('%Y년 %m월 %d일')
    period   = f"{quote.start_datetime or ''} ~ {quote.end_datetime or ''}"

    y = _draw_header(c, '견    적    서', C_NAVY, C_BLUE,
                     quote.id, client, settings, today, period)

    # ── 명세 테이블 ──────────────────────────
    hdrs = ['날짜','구분','차량','포함 내역','대','단가','지역','지역할증','이용시간','OT','숙식','소계']
    cws  = [18,14,18,38,8,18,22,17,16,8,14,18]
    _raw = [v*mm for v in cws]
    _scale = CW / sum(_raw)
    cws_mm = [w * _scale for w in _raw]

    # 총액 먼저 계산
    total = sum((qd.unit_price * qd.qty) + qd.region_surcharge + qd.time_surcharge + qd.lodging_fee for qd in quote.details)
    vat_type = client.vat_type or '별도'
    if vat_type == '별도':
        final_preview = total + int(total * 0.1)
    elif vat_type == '포함':
        final_preview = total
    else:
        final_preview = total

    txt(c, ML, y - 4*mm,
        f'견적금액 :  일금  {_num_to_korean(final_preview)}  (₩{final_preview:,})',
        size=9, bold=True, color=C_NAVY)
    y -= 8*mm

    rows = [[p(h, bold=True, color=C_WHITE) for h in hdrs]]
    total = 0
    for qd in quote.details:
        sub = (qd.unit_price * qd.qty) + qd.region_surcharge + qd.time_surcharge + qd.lodging_fee
        total += sub
        cap = f' {qd.vehicle.capacity}인승' if qd.vehicle and qd.vehicle.capacity else ''
        vn  = (qd.vehicle.name + cap) if qd.vehicle else ''
        rows.append([
            p(qd.run_date or ''),
            p(qd.product_type or ''),
            p(vn, 'left'),
            p(qd.includes or '', 'left'),
            p(str(qd.qty or 1)),
            p(money(qd.unit_price), 'right'),
            p(qd.region or '', 'left'),
            p(money(qd.region_surcharge), 'right'),
            p(qd.use_time or ''),
            p(str(qd.extra_time) if qd.extra_time else ''),
            p(money(qd.lodging_fee), 'right'),
            p(money(sub), 'right', bold=True, color=C_BLUE),
        ])
    pass

    tbl = Table(rows, colWidths=cws_mm, repeatRows=1)
    tbl.setStyle(_table_style(C_NAVY))
    tbl.wrapOn(c, sum(cws_mm), PH)
    _, th = tbl.wrap(sum(cws_mm), PH)
    tbl.drawOn(c, ML, y - th)
    y -= th + 4*mm

    # ── 합계 ─────────────────────────────────
    y, final = _draw_total(c, y, total, vat_type, C_BLUE)

    

    # ── NOTE ─────────────────────────────────
    _draw_note(c, y, [
        '단가에는 서울내에서의 차량렌트비, 유류비, 인건비가 포함되어 있으며, 10시간 이후에는 단가의 10%/추가시간당 청구됩니다.',
        '지역할증은 서울외 지역 운행에 따른 추가 유류비, 통행료, 인건비입니다.',
        '결제방법: 현금 또는 계좌이체 (세금계산서 발행), 카드결제(사전요청)',
    ])

    c.save()
    buf.seek(0)
    return buf


# ═══════════════════════════════════════════
# 청구서 PDF
# ═══════════════════════════════════════════
def generate_invoice_pdf(order, settings):
    _register()
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(PW, PH))
    c.setTitle(f'청구서_{order.id}')

    client   = order.client
    vat_type = client.vat_type or '별도'
    today    = datetime.today().strftime('%Y년 %m월 %d일')
    period   = f"{order.start_datetime or ''} ~ {order.end_datetime or ''}"

    y = _draw_header(c, '청  구  서', C_RED, C_RED,
                     order.id, client, settings, today, period)

    # ── 명세 테이블 ──────────────────────────
    hdrs = ['날짜','구분','차종','단가','시작','종료','추가h','시간할증','지역','지역할증','숙식(청)','소계']
    cws  = [18,14,20,18,13,13,11,17,18,17,14,18]
    _raw = [v*mm for v in cws]
    _scale = CW / sum(_raw)
    cws_mm = [w * _scale for w in _raw]

    # 총액 먼저 계산
    total = sum((qd.unit_price * qd.qty) + qd.region_surcharge + qd.time_surcharge + qd.lodging_fee for qd in quote.details)
    vat_type = client.vat_type or '별도'
    if vat_type == '별도':
        final_preview = total + int(total * 0.1)
    elif vat_type == '포함':
        final_preview = total
    else:
        final_preview = total

    txt(c, ML, y - 4*mm,
        f'청구금액 :  일금  {_num_to_korean(final_preview)}  (₩{final_preview:,})',
        size=9, bold=True, color=C_NAVY)
    y -= 8*mm

    rows = [[p(h, bold=True, color=C_WHITE) for h in hdrs]]
    total = 0
    for od in order.details:
        sub = od.unit_price + od.region_surcharge + od.time_surcharge + od.lodging_fee
        total += sub
        cap = f' {od.vehicle.capacity}인승' if od.vehicle and od.vehicle.capacity else ''
        vn  = (od.vehicle.name + cap) if od.vehicle else ''
        rows.append([
            p(od.run_date or ''),
            p(od.product_type or ''),
            p(vn, 'left'),
            p(money(od.unit_price), 'right'),
            p(od.start_time or ''),
            p(od.end_time or ''),
            p(str(od.extra_time) if od.extra_time else ''),
            p(money(od.time_surcharge), 'right'),
            p(od.region or '', 'left'),
            p(money(od.region_surcharge), 'right'),
            p(money(od.lodging_fee), 'right'),
            p(money(sub), 'right', bold=True, color=C_RED),
        ])
    pass

    tbl = Table(rows, colWidths=cws_mm, repeatRows=1)
    tbl.setStyle(_table_style(C_RED))
    tbl.wrapOn(c, sum(cws_mm), PH)
    _, th = tbl.wrap(sum(cws_mm), PH)
    tbl.drawOn(c, ML, y - th)
    y -= th + 4*mm

    # ── 합계 ─────────────────────────────────
    y, final = _draw_total(c, y, total, vat_type, C_RED)

    # ── NOTE ─────────────────────────────────
    bank_n = settings.get('bank_name', '')
    bank_a = settings.get('bank_account', '')
    bank_h = settings.get('bank_holder', '')
    _draw_note(c, y, [
        f'위 금액을 청구하오니 검토 후 아래 계좌로 입금 부탁드립니다.',
        f'입금계좌: {bank_n}  {bank_a}  ({bank_h})',
        '세금계산서 발행 가능합니다. 요청 시 연락 부탁드립니다.',
    ])

    c.save()
    buf.seek(0)
    return buf


# ── 숫자 → 한국어 ─────────────────────────
def _num_to_korean(n):
    if not n:
        return '영원정'
    units  = ['', '만', '억', '조']
    digits = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
    places = ['', '십', '백', '천']
    result = ''
    ui = 0
    n = int(n)
    while n > 0:
        g = n % 10000
        if g:
            gs = ''
            for i, d in enumerate(str(g).zfill(4)):
                v = int(d)
                if v:
                    gs += (digits[v] if not (i==0 and v==1 and g >= 1000) else '') + places[3-i]
            result = gs + units[ui] + result
        ui += 1
        n //= 10000
    return result + '원정'

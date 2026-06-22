from flask import Blueprint, render_template, request, jsonify

from extensions import db
from models import Quote, QuoteDetail, Client, Vehicle
from utils import generate_id
from services.time_calc_service import (
    calc_extra_time, calc_time_surcharge, generate_includes
)

quotes_bp = Blueprint('quotes', __name__)


def _vehicle_list():
    return Vehicle.query.order_by(Vehicle.id).all()


def _client_list():
    return Client.query.order_by(Client.id).all()


# ── 견적 목록 페이지 ─────────────────────
@quotes_bp.route('/quotes')
def quotes_page():
    quotes = Quote.query.order_by(Quote.id.desc()).all()
    return render_template('quotes.html',
                           quotes=quotes,
                           clients=_client_list())


# ── 견적 목록 부분 갱신 ──────────────────
@quotes_bp.route('/api/quotes/')
def quotes_list():
    q = request.args.get('q', '').strip()
    status = request.args.get('status_filter', '').strip()

    query = Quote.query.join(Client)
    if q:
        query = query.filter(Client.name.contains(q))
    if status:
        query = query.filter(Quote.status == status)

    quotes = query.order_by(Quote.id.desc()).all()
    return render_template('_quote_rows.html', quotes=quotes)


# ── 견적 생성 (부모만) ────────────────────
@quotes_bp.route('/api/quotes/', methods=['POST'])
def quotes_create():
    data = request.form
    q = Quote(
        id=generate_id('Q', Quote),
        client_id=data.get('client_id'),
        start_datetime=data.get('start_datetime') or None,
        end_datetime=data.get('end_datetime') or None,
        status='견적',
    )
    db.session.add(q)
    db.session.commit()
    quotes = Quote.query.order_by(Quote.id.desc()).all()
    return render_template('_quote_rows.html', quotes=quotes)


# ── 견적 상세 페이지 (부모+자식) ──────────
@quotes_bp.route('/quotes/<id>')
def quote_detail_page(id):
    q = Quote.query.get_or_404(id)
    return render_template('quote_detail.html',
                           q=q,
                           clients=_client_list(),
                           vehicles=_vehicle_list())


# ── 견적 부모 수정 ────────────────────────
@quotes_bp.route('/api/quotes/<id>', methods=['PUT'])
def quote_update(id):
    q = Quote.query.get_or_404(id)
    data = request.form
    q.client_id = data.get('client_id')
    q.start_datetime = data.get('start_datetime') or None
    q.end_datetime = data.get('end_datetime') or None
    q.status = data.get('status')
    db.session.commit()
    return render_template('_quote_header.html', q=q, clients=_client_list())


# ── 견적 삭제 ────────────────────────────
@quotes_bp.route('/api/quotes/<id>', methods=['DELETE'])
def quote_delete(id):
    q = Quote.query.get_or_404(id)
    db.session.delete(q)
    db.session.commit()
    quotes = Quote.query.order_by(Quote.id.desc()).all()
    return render_template('_quote_rows.html', quotes=quotes)


# ── 견적 상태 변경 (견적→확정) ──────────
@quotes_bp.route('/api/quotes/<id>/status', methods=['PUT'])
def quote_status(id):
    q = Quote.query.get_or_404(id)
    q.status = request.form.get('status', q.status)
    db.session.commit()
    return render_template('_quote_header.html', q=q, clients=_client_list())


# ── 견적 자식 추가 ────────────────────────
@quotes_bp.route('/api/quotes/<quote_id>/details', methods=['POST'])
def quote_detail_create(quote_id):
    Quote.query.get_or_404(quote_id)
    data = request.form

    product_type = data.get('product_type')
    start_time = data.get('start_time') or None
    end_time = data.get('end_time') or None
    unit_price = int(data.get('unit_price') or 0)
    region_surcharge = int(data.get('region_surcharge') or 0)
    lodging_fee = int(data.get('lodging_fee') or 0)

    # 시간할증 자동계산
    final_type, extra_time = calc_extra_time(product_type, start_time, end_time)
    time_surcharge = calc_time_surcharge(unit_price, extra_time)

    use_time = f"{start_time}-{end_time}" if start_time and end_time else None

    qd = QuoteDetail(
        id=generate_id('QD', QuoteDetail),
        quote_id=quote_id,
        run_date=data.get('run_date'),
        product_type=final_type,
        vehicle_id=data.get('vehicle_id') or None,
        includes=generate_includes(final_type),
        qty=int(data.get('qty') or 1),
        unit_price=unit_price,
        region=data.get('region') or None,
        region_surcharge=region_surcharge,
        use_time=use_time,
        extra_time=extra_time,
        time_surcharge=time_surcharge,
        lodging_fee=lodging_fee,
    )
    db.session.add(qd)
    db.session.commit()
    q = Quote.query.get(quote_id)
    return render_template('_quote_detail_rows.html', q=q, vehicles=_vehicle_list())


# ── 견적 자식 삭제 ────────────────────────
@quotes_bp.route('/api/quote_details/<id>', methods=['DELETE'])
def quote_detail_delete(id):
    qd = QuoteDetail.query.get_or_404(id)
    quote_id = qd.quote_id
    db.session.delete(qd)
    db.session.commit()
    q = Quote.query.get(quote_id)
    return render_template('_quote_detail_rows.html', q=q, vehicles=_vehicle_list())


# ── 견적 자식 인라인 수정 ─────────────────
@quotes_bp.route('/api/quote_details/<id>/edit')
def quote_detail_edit_form(id):
    qd = QuoteDetail.query.get_or_404(id)
    return render_template('_quote_detail_row_edit.html', qd=qd, vehicles=_vehicle_list())


@quotes_bp.route('/api/quote_details/<id>/cancel')
def quote_detail_edit_cancel(id):
    qd = QuoteDetail.query.get_or_404(id)
    return render_template('_quote_detail_row.html', qd=qd, vehicles=_vehicle_list())


@quotes_bp.route('/api/quote_details/<id>', methods=['PUT'])
def quote_detail_update(id):
    qd = QuoteDetail.query.get_or_404(id)
    data = request.form

    product_type = data.get('product_type')
    start_time = data.get('start_time') or None
    end_time = data.get('end_time') or None
    unit_price = int(data.get('unit_price') or 0)

    final_type, extra_time = calc_extra_time(product_type, start_time, end_time)
    time_surcharge = calc_time_surcharge(unit_price, extra_time)

    qd.run_date = data.get('run_date')
    qd.product_type = final_type
    qd.vehicle_id = data.get('vehicle_id') or None
    qd.includes = data.get('includes') or generate_includes(final_type)
    qd.qty = int(data.get('qty') or 1)
    qd.unit_price = unit_price
    qd.region = data.get('region') or None
    qd.region_surcharge = int(data.get('region_surcharge') or 0)
    qd.use_time = f"{start_time}-{end_time}" if start_time and end_time else None
    qd.extra_time = extra_time
    qd.time_surcharge = time_surcharge
    qd.lodging_fee = int(data.get('lodging_fee') or 0)
    db.session.commit()

    q = Quote.query.get(qd.quote_id)
    return render_template('_quote_detail_rows.html', q=q, vehicles=_vehicle_list())


# ── 시간할증 즉시계산 API (폼 입력 중 실시간 반영) ──
@quotes_bp.route('/api/calc/time_surcharge')
def api_calc_time_surcharge():
    product_type = request.args.get('product_type')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    unit_price = int(request.args.get('unit_price') or 0)

    if product_type and start_time and end_time:
        final_type, extra_time = calc_extra_time(product_type, start_time, end_time)
        surcharge = calc_time_surcharge(unit_price, extra_time)
    else:
        final_type, extra_time, surcharge = product_type, 0, 0

    return jsonify({
        'final_type': final_type,
        'extra_time': extra_time,
        'time_surcharge': surcharge,
        'includes': generate_includes(final_type or product_type),
    })

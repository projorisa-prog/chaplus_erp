from flask import Blueprint, render_template, request, jsonify, send_file
from datetime import datetime

from extensions import db
from models import (OperationOrder, OperationDetail, Quote,
                    Client, Vehicle, Driver, Ledger, AccountSubject, PaymentAccount)
from utils import generate_id
from services.time_calc_service import (
    calc_extra_time, calc_time_surcharge, calc_driver_time_surcharge)

operations_bp = Blueprint('operations', __name__)
CARD_DEFAULT = '회사카드'


def _vehicle_list():
    return Vehicle.query.order_by(Vehicle.id).all()

def _client_list():
    return Client.query.order_by(Client.id).all()

def _driver_list():
    return Driver.query.order_by(Driver.id).all()

def _account_list():
    return PaymentAccount.query.filter_by(is_active=True).order_by(PaymentAccount.id).all()

def _quote_confirmed_list():
    return Quote.query.filter_by(status='확정').order_by(Quote.id.desc()).all()

def _resolve_plate(vehicle_id, driver):
    if vehicle_id:
        v = Vehicle.query.get(vehicle_id)
        if v and v.plate_number:
            return v.plate_number
    if driver and driver.plate_number:
        return driver.plate_number
    return None

def _get_or_create_subject(name, stype='지출'):
    """계정과목 조회 또는 생성"""
    s = AccountSubject.query.filter_by(name=name).first()
    if not s:
        s = AccountSubject(name=name, type=stype, is_fixed=False, fixed_amount=0, sort_order=99)
        db.session.add(s)
        db.session.flush()
    return s

def _create_card_ledger_entries(data, run_date, order_id):
    """회사카드 경비를 입출금관리에 자동 등록"""
    card_account_id = data.get('card_account_id') or None
    run_date_val = run_date
    if isinstance(run_date_val, str) and run_date_val:
        try:
            run_date_val = datetime.strptime(run_date_val, '%Y-%m-%d').date()
        except:
            run_date_val = datetime.today().date()
    elif not run_date_val:
        run_date_val = datetime.today().date()

    # 차량유지비: 유류비, 통행료, 주차비
    subj_vehicle = _get_or_create_subject('차량유지비')
    vehicle_items = [
        ('card_fuel',    '유류비'),
        ('card_toll',    '통행료'),
        ('card_parking', '주차비'),
    ]
    for field, label in vehicle_items:
        amt = int(data.get(field) or 0)
        if amt > 0:
            e = Ledger(
                id=generate_id('L', Ledger),
                date=run_date_val,
                type='출금',
                amount=amt,
                payment_account_id=card_account_id,
                account_subject_id=subj_vehicle.id,
                memo=f'[{order_id}] {label}',
            )
            db.session.add(e)

    # 여비교통비: 식대, 숙식비, 기타
    subj_travel = _get_or_create_subject('여비교통비')
    travel_items = [
        ('card_meal',    '식대'),
        ('card_lodging', '숙식비'),
        ('card_etc',     '기타'),
    ]
    for field, label in travel_items:
        amt = int(data.get(field) or 0)
        if amt > 0:
            e = Ledger(
                id=generate_id('L', Ledger),
                date=run_date_val,
                type='출금',
                amount=amt,
                payment_account_id=card_account_id,
                account_subject_id=subj_travel.id,
                memo=f'[{order_id}] {label}',
            )
            db.session.add(e)


# ── 운행 목록 페이지 ─────────────────────
@operations_bp.route('/operations')
def operations_page():
    orders = OperationOrder.query.order_by(OperationOrder.id.desc()).all()
    return render_template('operations.html',
                           orders=orders,
                           clients=_client_list(),
                           quotes=_quote_confirmed_list())


@operations_bp.route('/api/operations/')
def operations_list():
    q       = request.args.get('q', '').strip()
    status  = request.args.get('status_filter', '').strip()
    query   = OperationOrder.query.join(Client)
    if q:
        query = query.filter(Client.name.contains(q))
    if status:
        query = query.filter(OperationOrder.status == status)
    orders = query.order_by(OperationOrder.id.desc()).all()
    return render_template('_operation_rows.html', orders=orders)


@operations_bp.route('/api/operations/', methods=['POST'])
def operations_create():
    data = request.form
    o = OperationOrder(
        id=generate_id('O', OperationOrder),
        client_id=data.get('client_id'),
        start_datetime=data.get('start_datetime') or None,
        end_datetime=data.get('end_datetime') or None,
        status='예약확정',
    )
    db.session.add(o)
    db.session.commit()
    orders = OperationOrder.query.order_by(OperationOrder.id.desc()).all()
    return render_template('_operation_rows.html', orders=orders)


@operations_bp.route('/api/operations/copy_from_quote', methods=['POST'])
def copy_from_quote():
    quote_id = request.form.get('quote_id')
    q = Quote.query.get_or_404(quote_id)
    o = OperationOrder(
        id=generate_id('O', OperationOrder),
        quote_id=quote_id,
        client_id=q.client_id,
        start_datetime=q.start_datetime,
        end_datetime=q.end_datetime,
        status='예약확정',
    )
    db.session.add(o)
    db.session.flush()
    for qd in q.details:
        start_time, end_time = None, None
        if qd.use_time and '-' in qd.use_time:
            parts = qd.use_time.split('-', 1)
            start_time, end_time = parts[0], parts[1]
        driver = Driver.query.filter_by(type='용역', vehicle_id=qd.vehicle_id).first() if qd.vehicle_id else None
        plate = _resolve_plate(qd.vehicle_id, driver)
        ot_pay = driver.ot_pay if driver else 0
        driver_time_surcharge = calc_driver_time_surcharge(ot_pay, qd.extra_time or 0)
        od = OperationDetail(
            id=generate_id('OD', OperationDetail),
            order_id=o.id,
            run_date=qd.run_date,
            product_type=qd.product_type,
            vehicle_id=qd.vehicle_id,
            unit_price=qd.unit_price,
            region=qd.region,
            region_surcharge=qd.region_surcharge or 0,
            start_time=start_time, end_time=end_time,
            extra_time=qd.extra_time or 0,
            time_surcharge=qd.time_surcharge or 0,
            lodging_fee=qd.lodging_fee or 0,
            driver_id=driver.id if driver else None,
            plate_number=plate,
            base_pay=driver.base_pay if driver else 0,
            driver_extra_time=qd.extra_time or 0,
            driver_time_surcharge=driver_time_surcharge,
            fuel_card=CARD_DEFAULT, toll_card=CARD_DEFAULT,
            parking_card=CARD_DEFAULT, meal_card=CARD_DEFAULT,
            lodging_card=CARD_DEFAULT,
        )
        db.session.add(od)
    db.session.commit()
    orders = OperationOrder.query.order_by(OperationOrder.id.desc()).all()
    return render_template('_operation_rows.html', orders=orders)


@operations_bp.route('/operations/<id>')
def operation_detail_page(id):
    o = OperationOrder.query.get_or_404(id)
    return render_template('operation_detail.html',
                           o=o,
                           clients=_client_list(),
                           vehicles=_vehicle_list(),
                           drivers=_driver_list(),
                           accounts=_account_list())


@operations_bp.route('/api/operations/<id>', methods=['PUT'])
def operation_update(id):
    o = OperationOrder.query.get_or_404(id)
    data = request.form
    o.client_id     = data.get('client_id')
    o.start_datetime= data.get('start_datetime') or None
    o.end_datetime  = data.get('end_datetime') or None
    o.departure     = data.get('departure') or None
    o.status        = data.get('status')
    db.session.commit()
    return render_template('_operation_header.html', o=o, clients=_client_list())


@operations_bp.route('/api/operations/<id>', methods=['DELETE'])
def operation_delete(id):
    o = OperationOrder.query.get_or_404(id)
    db.session.delete(o)
    db.session.commit()
    orders = OperationOrder.query.order_by(OperationOrder.id.desc()).all()
    return render_template('_operation_rows.html', orders=orders)


# ── 운행 자식 추가 ────────────────────────
@operations_bp.route('/api/operations/<order_id>/details', methods=['POST'])
def operation_detail_create(order_id):
    OperationOrder.query.get_or_404(order_id)
    data = request.form

    product_type = data.get('product_type')
    start_time   = data.get('start_time') or None
    end_time     = data.get('end_time') or None
    unit_price   = int(data.get('unit_price') or 0)
    driver_id    = data.get('driver_id') or None
    vehicle_id   = data.get('vehicle_id') or None
    run_date     = data.get('run_date')

    final_type, extra_time = calc_extra_time(product_type, start_time, end_time)
    time_surcharge = calc_time_surcharge(unit_price, extra_time)

    driver   = Driver.query.get(driver_id) if driver_id else None
    base_pay = int(data.get('base_pay') or 0) or (driver.base_pay if driver else 0)
    ot_pay   = driver.ot_pay if driver else 0
    plate    = data.get('plate_number') or _resolve_plate(vehicle_id, driver)

    driver_extra_time     = extra_time
    driver_time_surcharge = calc_driver_time_surcharge(ot_pay, driver_extra_time)

    od = OperationDetail(
        id=generate_id('OD', OperationDetail),
        order_id=order_id,
        run_date=run_date,
        product_type=final_type,
        vehicle_id=vehicle_id,
        unit_price=unit_price,
        region=data.get('region') or None,
        region_surcharge=int(data.get('region_surcharge') or 0),
        start_time=start_time, end_time=end_time,
        extra_time=extra_time, time_surcharge=time_surcharge,
        lodging_fee=int(data.get('lodging_fee') or 0),
        driver_id=driver_id, plate_number=plate, base_pay=base_pay,
        driver_extra_time=driver_extra_time,
        driver_time_surcharge=driver_time_surcharge,
        fuel_cost=int(data.get('fuel_cost') or 0),
        fuel_card=CARD_DEFAULT,
        toll_fee=int(data.get('toll_fee') or 0),
        toll_card=CARD_DEFAULT,
        parking_fee=int(data.get('parking_fee') or 0),
        parking_card=CARD_DEFAULT,
        meal_fee=int(data.get('meal_fee') or 0),
        meal_card=CARD_DEFAULT,
        lodging_pay=int(data.get('lodging_pay') or 0),
        lodging_card=CARD_DEFAULT,
    )
    db.session.add(od)
    db.session.flush()

    # 회사카드 경비 → 입출금관리 자동 등록
    _create_card_ledger_entries(data, run_date, order_id)

    db.session.commit()
    o = OperationOrder.query.get(order_id)
    return render_template('_operation_detail_rows.html',
                           o=o, vehicles=_vehicle_list(), drivers=_driver_list())


# ── 운행 자식 삭제 ────────────────────────
@operations_bp.route('/api/operation_details/<id>', methods=['DELETE'])
def operation_detail_delete(id):
    od = OperationDetail.query.get_or_404(id)
    order_id = od.order_id
    db.session.delete(od)
    db.session.commit()
    o = OperationOrder.query.get(order_id)
    return render_template('_operation_detail_rows.html',
                           o=o, vehicles=_vehicle_list(), drivers=_driver_list())


# ── 운행 자식 수정 (폼 데이터 반환) ─────────
@operations_bp.route('/api/operation_details/<id>/form_data')
def operation_detail_form_data(id):
    od = OperationDetail.query.get_or_404(id)
    return jsonify({
        'run_date':        od.run_date or '',
        'product_type':    od.product_type or '',
        'vehicle_id':      od.vehicle_id or '',
        'unit_price':      od.unit_price or 0,
        'start_time':      od.start_time or '',
        'end_time':        od.end_time or '',
        'region':          od.region or '',
        'region_surcharge':od.region_surcharge or 0,
        'lodging_fee':     od.lodging_fee or 0,
        'driver_id':       od.driver_id or '',
        'plate_number':    od.plate_number or '',
        'base_pay':        od.base_pay or 0,
        'fuel_cost':       od.fuel_cost or 0,
        'toll_fee':        od.toll_fee or 0,
        'parking_fee':     od.parking_fee or 0,
        'meal_fee':        od.meal_fee or 0,
        'lodging_pay':     od.lodging_pay or 0,
    })


# ── 운행 자식 수정 저장 ───────────────────
@operations_bp.route('/api/operation_details/<id>', methods=['PUT'])
def operation_detail_update(id):
    od = OperationDetail.query.get_or_404(id)
    data = request.form

    product_type = data.get('product_type')
    start_time   = data.get('start_time') or None
    end_time     = data.get('end_time') or None
    unit_price   = int(data.get('unit_price') or 0)
    driver_id    = data.get('driver_id') or None
    vehicle_id   = data.get('vehicle_id') or None
    run_date     = data.get('run_date')

    final_type, extra_time = calc_extra_time(product_type, start_time, end_time)
    time_surcharge = calc_time_surcharge(unit_price, extra_time)

    driver = Driver.query.get(driver_id) if driver_id else None
    ot_pay = driver.ot_pay if driver else 0
    plate  = data.get('plate_number') or _resolve_plate(vehicle_id, driver)

    driver_extra_time     = int(data.get('driver_extra_time') or extra_time)
    driver_time_surcharge = calc_driver_time_surcharge(ot_pay, driver_extra_time)

    od.run_date           = run_date
    od.product_type       = final_type
    od.vehicle_id         = vehicle_id
    od.unit_price         = unit_price
    od.region             = data.get('region') or None
    od.region_surcharge   = int(data.get('region_surcharge') or 0)
    od.start_time         = start_time
    od.end_time           = end_time
    od.extra_time         = extra_time
    od.time_surcharge     = time_surcharge
    od.lodging_fee        = int(data.get('lodging_fee') or 0)
    od.driver_id          = driver_id
    od.plate_number       = plate
    od.base_pay           = int(data.get('base_pay') or 0)
    od.driver_extra_time  = driver_extra_time
    od.driver_time_surcharge = driver_time_surcharge
    od.fuel_cost          = int(data.get('fuel_cost') or 0)
    od.toll_fee           = int(data.get('toll_fee') or 0)
    od.parking_fee        = int(data.get('parking_fee') or 0)
    od.meal_fee           = int(data.get('meal_fee') or 0)
    od.lodging_pay        = int(data.get('lodging_pay') or 0)

    # 회사카드 경비 → 입출금관리 자동 등록
    _create_card_ledger_entries(data, run_date, od.order_id)

    db.session.commit()
    o = OperationOrder.query.get(od.order_id)
    return render_template('_operation_detail_rows.html',
                           o=o, vehicles=_vehicle_list(), drivers=_driver_list())


# ── 기사 정보 자동완성 ────────────────────
@operations_bp.route('/api/drivers/<id>/info')
def driver_info(id):
    d = Driver.query.get_or_404(id)
    plate = ''
    if d.vehicle_id:
        v = Vehicle.query.get(d.vehicle_id)
        if v and v.plate_number:
            plate = v.plate_number
    if not plate and d.plate_number:
        plate = d.plate_number
    return jsonify({
        'base_pay':    d.base_pay or 0,
        'ot_pay':      d.ot_pay or 0,
        'plate_number':plate,
        'vehicle_id':  d.vehicle_id or '',
    })


# ── 청구서 PDF ────────────────────────────
@operations_bp.route('/operations/<id>/pdf')
def operation_pdf(id):
    from models import Settings
    from services.pdf_service import generate_invoice_pdf
    o = OperationOrder.query.get_or_404(id)
    settings = {s.key: s.value for s in Settings.query.all()}
    buf = generate_invoice_pdf(o, settings)
    filename = f"청구서_{o.id}_{o.client.name}.pdf"
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)

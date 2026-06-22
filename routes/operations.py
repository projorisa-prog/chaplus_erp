from flask import Blueprint, render_template, request, jsonify

from extensions import db
from models import OperationOrder, OperationDetail, Quote, Client, Vehicle, Driver
from utils import generate_id
from services.time_calc_service import (
    calc_extra_time, calc_time_surcharge,
    calc_driver_time_surcharge, generate_includes
)

operations_bp = Blueprint('operations', __name__)


def _vehicle_list():
    return Vehicle.query.order_by(Vehicle.id).all()


def _client_list():
    return Client.query.order_by(Client.id).all()


def _driver_list():
    return Driver.query.order_by(Driver.id).all()


def _quote_confirmed_list():
    return Quote.query.filter_by(status='확정').order_by(Quote.id.desc()).all()


# ── 운행 목록 페이지 ─────────────────────
@operations_bp.route('/operations')
def operations_page():
    orders = OperationOrder.query.order_by(OperationOrder.id.desc()).all()
    return render_template('operations.html',
                           orders=orders,
                           clients=_client_list(),
                           quotes=_quote_confirmed_list())


# ── 운행 목록 부분 갱신 ──────────────────
@operations_bp.route('/api/operations/')
def operations_list():
    q = request.args.get('q', '').strip()
    status = request.args.get('status_filter', '').strip()

    query = OperationOrder.query.join(Client)
    if q:
        query = query.filter(Client.name.contains(q))
    if status:
        query = query.filter(OperationOrder.status == status)

    orders = query.order_by(OperationOrder.id.desc()).all()
    return render_template('_operation_rows.html', orders=orders)


# ── 운행 생성 (직접 생성) ─────────────────
@operations_bp.route('/api/operations/', methods=['POST'])
def operations_create():
    data = request.form
    o = OperationOrder(
        id=generate_id('O', OperationOrder),
        client_id=data.get('client_id'),
        start_datetime=data.get('start_datetime') or None,
        end_datetime=data.get('end_datetime') or None,
        departure=data.get('departure') or None,
        product_type=data.get('product_type') or None,
        status='예약확정',
    )
    db.session.add(o)
    db.session.commit()
    orders = OperationOrder.query.order_by(OperationOrder.id.desc()).all()
    return render_template('_operation_rows.html', orders=orders)


# ── 견적 → 운행 복사 생성 ────────────────
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
        od = OperationDetail(
            id=generate_id('OD', OperationDetail),
            order_id=o.id,
            run_date=qd.run_date,
            vehicle_id=qd.vehicle_id,
            unit_price=qd.unit_price,
            region=qd.region,
            region_surcharge=qd.region_surcharge,
            start_time=qd.use_time.split('-')[0] if qd.use_time else None,
            end_time=qd.use_time.split('-')[1] if qd.use_time and '-' in qd.use_time else None,
            extra_time=qd.extra_time,
            time_surcharge=qd.time_surcharge,
            lodging_fee=qd.lodging_fee,
        )
        # 용역기사 차종 일치 시 자동 배정
        if qd.vehicle_id:
            driver = Driver.query.filter_by(
                type='용역', vehicle_id=qd.vehicle_id
            ).first()
            if driver:
                od.driver_id = driver.id
                od.plate_number = driver.plate_number
                od.base_pay = driver.base_pay
                od.ot_pay = driver.ot_pay if hasattr(driver, 'ot_pay') else 0
        db.session.add(od)

    db.session.commit()
    orders = OperationOrder.query.order_by(OperationOrder.id.desc()).all()
    return render_template('_operation_rows.html', orders=orders)


# ── 운행 상세 페이지 ─────────────────────
@operations_bp.route('/operations/<id>')
def operation_detail_page(id):
    o = OperationOrder.query.get_or_404(id)
    return render_template('operation_detail.html',
                           o=o,
                           clients=_client_list(),
                           vehicles=_vehicle_list(),
                           drivers=_driver_list())


# ── 운행 부모 수정 ────────────────────────
@operations_bp.route('/api/operations/<id>', methods=['PUT'])
def operation_update(id):
    o = OperationOrder.query.get_or_404(id)
    data = request.form
    o.client_id = data.get('client_id')
    o.start_datetime = data.get('start_datetime') or None
    o.end_datetime = data.get('end_datetime') or None
    o.departure = data.get('departure') or None
    o.status = data.get('status')
    db.session.commit()
    return render_template('_operation_header.html', o=o, clients=_client_list())


# ── 운행 삭제 ────────────────────────────
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
    start_time = data.get('start_time') or None
    end_time = data.get('end_time') or None
    unit_price = int(data.get('unit_price') or 0)
    driver_id = data.get('driver_id') or None

    final_type, extra_time = calc_extra_time(product_type, start_time, end_time)
    time_surcharge = calc_time_surcharge(unit_price, extra_time)

    # 기사 정보 자동세팅
    base_pay = int(data.get('base_pay') or 0)
    ot_pay = 0
    plate_number = data.get('plate_number') or None

    if driver_id:
        driver = Driver.query.get(driver_id)
        if driver:
            if not base_pay:
                base_pay = driver.base_pay or 0
            ot_pay = driver.ot_pay or 0
            if not plate_number and driver.plate_number:
                plate_number = driver.plate_number

    driver_extra_time = extra_time  # 기본값: 청구와 동일
    driver_time_surcharge = calc_driver_time_surcharge(ot_pay, driver_extra_time)

    od = OperationDetail(
        id=generate_id('OD', OperationDetail),
        order_id=order_id,
        run_date=data.get('run_date'),
        vehicle_id=data.get('vehicle_id') or None,
        unit_price=unit_price,
        region=data.get('region') or None,
        region_surcharge=int(data.get('region_surcharge') or 0),
        start_time=start_time,
        end_time=end_time,
        extra_time=extra_time,
        time_surcharge=time_surcharge,
        lodging_fee=int(data.get('lodging_fee') or 0),
        driver_id=driver_id,
        plate_number=plate_number,
        base_pay=base_pay,
        driver_extra_time=driver_extra_time,
        driver_time_surcharge=driver_time_surcharge,
        fuel_cost=int(data.get('fuel_cost') or 0),
        fuel_card=data.get('fuel_card') or None,
        toll_fee=int(data.get('toll_fee') or 0),
        toll_card=data.get('toll_card') or None,
        parking_fee=int(data.get('parking_fee') or 0),
        parking_card=data.get('parking_card') or None,
        meal_fee=int(data.get('meal_fee') or 0),
        meal_card=data.get('meal_card') or None,
        lodging_pay=int(data.get('lodging_pay') or 0),
        lodging_card=data.get('lodging_card') or None,
    )
    db.session.add(od)
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


# ── 운행 자식 인라인 수정 ─────────────────
@operations_bp.route('/api/operation_details/<id>/edit')
def operation_detail_edit_form(id):
    od = OperationDetail.query.get_or_404(id)
    return render_template('_operation_detail_row_edit.html',
                           od=od,
                           vehicles=_vehicle_list(),
                           drivers=_driver_list())


@operations_bp.route('/api/operation_details/<id>/cancel')
def operation_detail_edit_cancel(id):
    od = OperationDetail.query.get_or_404(id)
    return render_template('_operation_detail_row.html',
                           od=od,
                           vehicles=_vehicle_list(),
                           drivers=_driver_list())


@operations_bp.route('/api/operation_details/<id>', methods=['PUT'])
def operation_detail_update(id):
    od = OperationDetail.query.get_or_404(id)
    data = request.form

    product_type = data.get('product_type')
    start_time = data.get('start_time') or None
    end_time = data.get('end_time') or None
    unit_price = int(data.get('unit_price') or 0)
    driver_id = data.get('driver_id') or None

    final_type, extra_time = calc_extra_time(product_type, start_time, end_time)
    time_surcharge = calc_time_surcharge(unit_price, extra_time)

    ot_pay = 0
    if driver_id:
        driver = Driver.query.get(driver_id)
        if driver:
            ot_pay = driver.ot_pay or 0

    driver_extra_time = int(data.get('driver_extra_time') or extra_time)
    driver_time_surcharge = calc_driver_time_surcharge(ot_pay, driver_extra_time)

    od.run_date = data.get('run_date')
    od.vehicle_id = data.get('vehicle_id') or None
    od.unit_price = unit_price
    od.region = data.get('region') or None
    od.region_surcharge = int(data.get('region_surcharge') or 0)
    od.start_time = start_time
    od.end_time = end_time
    od.extra_time = extra_time
    od.time_surcharge = time_surcharge
    od.lodging_fee = int(data.get('lodging_fee') or 0)
    od.driver_id = driver_id
    od.plate_number = data.get('plate_number') or None
    od.base_pay = int(data.get('base_pay') or 0)
    od.driver_extra_time = driver_extra_time
    od.driver_time_surcharge = driver_time_surcharge
    od.fuel_cost = int(data.get('fuel_cost') or 0)
    od.fuel_card = data.get('fuel_card') or None
    od.toll_fee = int(data.get('toll_fee') or 0)
    od.toll_card = data.get('toll_card') or None
    od.parking_fee = int(data.get('parking_fee') or 0)
    od.parking_card = data.get('parking_card') or None
    od.meal_fee = int(data.get('meal_fee') or 0)
    od.meal_card = data.get('meal_card') or None
    od.lodging_pay = int(data.get('lodging_pay') or 0)
    od.lodging_card = data.get('lodging_card') or None
    db.session.commit()

    o = OperationOrder.query.get(od.order_id)
    return render_template('_operation_detail_rows.html',
                           o=o, vehicles=_vehicle_list(), drivers=_driver_list())


# ── 기사 선택 시 정보 자동완성 API ──────────
@operations_bp.route('/api/drivers/<id>/info')
def driver_info(id):
    d = Driver.query.get_or_404(id)
    return jsonify({
        'base_pay': d.base_pay or 0,
        'ot_pay': d.ot_pay or 0,
        'plate_number': d.plate_number or '',
        'vehicle_id': d.vehicle_id or '',
    })

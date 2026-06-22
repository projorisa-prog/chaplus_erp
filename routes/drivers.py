from flask import Blueprint, render_template, request

from extensions import db
from models import Driver, Vehicle
from utils import generate_id

drivers_bp = Blueprint('drivers', __name__)


def _outsourced_vehicles():
    """용역기사 차종 선택용: 타사 차량만 조회"""
    return Vehicle.query.filter_by(vehicle_type='타사').order_by(Vehicle.id).all()


# ── 페이지 ──────────────────────────────
@drivers_bp.route('/drivers')
def drivers_page():
    drivers = Driver.query.order_by(Driver.id).all()
    return render_template('drivers.html', drivers=drivers, vehicles=_outsourced_vehicles())


# ── 목록 조회 / 추가 ─────────────────────
@drivers_bp.route('/api/drivers/', methods=['GET', 'POST'])
def drivers_api():
    if request.method == 'POST':
        data = request.form
        driver_type = data.get('type')

        d = Driver(
            id=generate_id('D', Driver),
            type=driver_type,
            name=data.get('name'),
            phone=data.get('phone') or None,
            team_leader=data.get('team_leader') or None,
            base_pay=data.get('base_pay') or 0,
            ot_pay=data.get('ot_pay') or 0,
            # 용역만 사용하는 필드
            vehicle_id=data.get('vehicle_id') if driver_type == '용역' else None,
            plate_number=data.get('plate_number') if driver_type == '용역' else None,
            incheon_airport_fee=data.get('incheon_airport_fee') or 0,
            gimpo_airport_fee=data.get('gimpo_airport_fee') or 0,
        )
        db.session.add(d)
        db.session.commit()
        return _rows_response()

    # GET (검색)
    name = request.args.get('name', '').strip()
    dtype = request.args.get('type_filter', '').strip()
    team_leader = request.args.get('team_leader', '').strip()

    query = Driver.query
    if name:
        query = query.filter(Driver.name.contains(name))
    if dtype:
        query = query.filter(Driver.type == dtype)
    if team_leader:
        query = query.filter(Driver.team_leader.contains(team_leader))

    drivers = query.order_by(Driver.id).all()
    return render_template('_driver_rows.html', drivers=drivers)


# ── 수정 / 삭제 ──────────────────────────
@drivers_bp.route('/api/drivers/<id>', methods=['PUT', 'DELETE'])
def driver_detail(id):
    d = Driver.query.get_or_404(id)

    if request.method == 'DELETE':
        db.session.delete(d)
        db.session.commit()
        return _rows_response()

    # PUT
    data = request.form
    driver_type = data.get('type')

    d.type = driver_type
    d.name = data.get('name')
    d.phone = data.get('phone') or None
    d.team_leader = data.get('team_leader') or None
    d.base_pay = data.get('base_pay') or 0
    d.ot_pay = data.get('ot_pay') or 0
    d.vehicle_id = data.get('vehicle_id') if driver_type == '용역' else None
    d.plate_number = data.get('plate_number') if driver_type == '용역' else None
    d.incheon_airport_fee = data.get('incheon_airport_fee') or 0
    d.gimpo_airport_fee = data.get('gimpo_airport_fee') or 0
    db.session.commit()
    return _rows_response()


# ── 인라인 수정 폼 토글 ───────────────────
@drivers_bp.route('/api/drivers/<id>/edit')
def driver_edit_form(id):
    d = Driver.query.get_or_404(id)
    return render_template('_driver_row_edit.html', d=d, vehicles=_outsourced_vehicles())


@drivers_bp.route('/api/drivers/<id>/cancel')
def driver_edit_cancel(id):
    d = Driver.query.get_or_404(id)
    return render_template('_driver_row.html', d=d)


def _rows_response():
    drivers = Driver.query.order_by(Driver.id).all()
    return render_template('_driver_rows.html', drivers=drivers)

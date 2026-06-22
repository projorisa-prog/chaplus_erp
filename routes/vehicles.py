from flask import Blueprint, render_template, request

from extensions import db
from models import Vehicle
from utils import generate_id

vehicles_bp = Blueprint('vehicles', __name__)


# ── 페이지 ──────────────────────────────
@vehicles_bp.route('/vehicles')
def vehicles_page():
    vehicles = Vehicle.query.order_by(Vehicle.id).all()
    return render_template('vehicles.html', vehicles=vehicles)


# ── 목록 조회 / 추가 ─────────────────────
@vehicles_bp.route('/api/vehicles/', methods=['GET', 'POST'])
def vehicles_api():
    if request.method == 'POST':
        data = request.form
        v = Vehicle(
            id=generate_id('V', Vehicle),
            name=data.get('name'),
            capacity=data.get('capacity') or None,
            vehicle_type=data.get('vehicle_type'),
            plate_number=data.get('plate_number') or None,
        )
        db.session.add(v)
        db.session.commit()
        return _rows_response()

    # GET (검색)
    q = request.args.get('q', '').strip()
    vtype = request.args.get('vehicle_type_filter', '').strip()

    query = Vehicle.query
    if q:
        query = query.filter(Vehicle.name.contains(q))
    if vtype:
        query = query.filter(Vehicle.vehicle_type == vtype)

    vehicles = query.order_by(Vehicle.id).all()
    return render_template('_vehicle_rows.html', vehicles=vehicles)


# ── 수정 / 삭제 ──────────────────────────
@vehicles_bp.route('/api/vehicles/<id>', methods=['PUT', 'DELETE'])
def vehicle_detail(id):
    v = Vehicle.query.get_or_404(id)

    if request.method == 'DELETE':
        db.session.delete(v)
        db.session.commit()
        return _rows_response()

    # PUT
    data = request.form
    v.name = data.get('name')
    v.capacity = data.get('capacity') or None
    v.vehicle_type = data.get('vehicle_type')
    v.plate_number = data.get('plate_number') or None
    db.session.commit()
    return _rows_response()


# ── 인라인 수정 폼 토글 ───────────────────
@vehicles_bp.route('/api/vehicles/<id>/edit')
def vehicle_edit_form(id):
    v = Vehicle.query.get_or_404(id)
    return render_template('_vehicle_row_edit.html', v=v)


@vehicles_bp.route('/api/vehicles/<id>/cancel')
def vehicle_edit_cancel(id):
    v = Vehicle.query.get_or_404(id)
    return render_template('_vehicle_row.html', v=v)


def _rows_response():
    vehicles = Vehicle.query.order_by(Vehicle.id).all()
    return render_template('_vehicle_rows.html', vehicles=vehicles)

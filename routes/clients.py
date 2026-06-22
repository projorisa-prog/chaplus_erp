from flask import Blueprint, render_template, request

from extensions import db
from models import Client
from utils import generate_id

clients_bp = Blueprint('clients', __name__)


# ── 페이지 ──────────────────────────────
@clients_bp.route('/clients')
def clients_page():
    clients = Client.query.order_by(Client.id).all()
    return render_template('clients.html', clients=clients)


# ── 목록 조회 / 추가 ─────────────────────
@clients_bp.route('/api/clients/', methods=['GET', 'POST'])
def clients_api():
    if request.method == 'POST':
        data = request.form
        c = Client(
            id=generate_id('C', Client),
            name=data.get('name'),
            business_no=data.get('business_no') or None,
            ceo_name=data.get('ceo_name') or None,
            business_type=data.get('business_type') or None,
            business_item=data.get('business_item') or None,
            manager_name=data.get('manager_name') or None,
            phone=data.get('phone') or None,
            email=data.get('email') or None,
            tax_invoice_email=data.get('tax_invoice_email') or None,
            vat_type=data.get('vat_type'),
        )
        db.session.add(c)
        db.session.commit()
        return _rows_response()

    # GET (검색)
    name = request.args.get('name', '').strip()
    vat_type = request.args.get('vat_type_filter', '').strip()

    query = Client.query
    if name:
        query = query.filter(Client.name.contains(name))
    if vat_type:
        query = query.filter(Client.vat_type == vat_type)

    clients = query.order_by(Client.id).all()
    return render_template('_client_rows.html', clients=clients)


# ── 수정 / 삭제 ──────────────────────────
@clients_bp.route('/api/clients/<id>', methods=['PUT', 'DELETE'])
def client_detail(id):
    c = Client.query.get_or_404(id)

    if request.method == 'DELETE':
        db.session.delete(c)
        db.session.commit()
        return _rows_response()

    # PUT
    data = request.form
    c.name = data.get('name')
    c.business_no = data.get('business_no') or None
    c.ceo_name = data.get('ceo_name') or None
    c.business_type = data.get('business_type') or None
    c.business_item = data.get('business_item') or None
    c.manager_name = data.get('manager_name') or None
    c.phone = data.get('phone') or None
    c.email = data.get('email') or None
    c.tax_invoice_email = data.get('tax_invoice_email') or None
    c.vat_type = data.get('vat_type')
    db.session.commit()
    return _rows_response()


# ── 인라인 수정 폼 토글 ───────────────────
@clients_bp.route('/api/clients/<id>/edit')
def client_edit_form(id):
    c = Client.query.get_or_404(id)
    return render_template('_client_row_edit.html', c=c)


@clients_bp.route('/api/clients/<id>/cancel')
def client_edit_cancel(id):
    c = Client.query.get_or_404(id)
    return render_template('_client_row.html', c=c)


def _rows_response():
    clients = Client.query.order_by(Client.id).all()
    return render_template('_client_rows.html', clients=clients)

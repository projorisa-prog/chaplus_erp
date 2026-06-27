from flask import Blueprint, render_template, request
from extensions import db
from models import PaymentAccount
from utils import generate_id

payment_accounts_bp = Blueprint('payment_accounts', __name__)


@payment_accounts_bp.route('/payment_accounts')
def payment_accounts_page():
    accounts = PaymentAccount.query.order_by(PaymentAccount.id).all()
    return render_template('payment_accounts.html', accounts=accounts)


@payment_accounts_bp.route('/api/payment_accounts/', methods=['GET', 'POST'])
def payment_accounts_api():
    if request.method == 'POST':
        data = request.form
        a = PaymentAccount(
            id=generate_id('PA', PaymentAccount),
            type=data.get('type'),
            name=data.get('name'),
            number=data.get('number') or None,
            bank_name=data.get('bank_name') or None,
            holder=data.get('holder') or None,
            is_active=data.get('is_active') == 'true',
            memo=data.get('memo') or None,
        )
        db.session.add(a)
        db.session.commit()
    return _rows_response()


@payment_accounts_bp.route('/api/payment_accounts/<id>', methods=['PUT', 'DELETE'])
def payment_account_detail(id):
    a = PaymentAccount.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(a)
        db.session.commit()
        return _rows_response()
    data = request.form
    a.type      = data.get('type')
    a.name      = data.get('name')
    a.number    = data.get('number') or None
    a.bank_name = data.get('bank_name') or None
    a.holder    = data.get('holder') or None
    a.is_active = data.get('is_active') == 'true'
    a.memo      = data.get('memo') or None
    db.session.commit()
    return _rows_response()


@payment_accounts_bp.route('/api/payment_accounts/<id>/edit')
def payment_account_edit_form(id):
    a = PaymentAccount.query.get_or_404(id)
    return render_template('_payment_account_row_edit.html', a=a)


@payment_accounts_bp.route('/api/payment_accounts/<id>/cancel')
def payment_account_edit_cancel(id):
    a = PaymentAccount.query.get_or_404(id)
    return render_template('_payment_account_row.html', a=a)


def _rows_response():
    accounts = PaymentAccount.query.order_by(PaymentAccount.id).all()
    return render_template('_payment_account_rows.html', accounts=accounts)

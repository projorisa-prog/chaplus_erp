from flask import Blueprint, render_template, request
from extensions import db
from models import AccountSubject

account_subjects_bp = Blueprint('account_subjects', __name__)


@account_subjects_bp.route('/account_subjects')
def account_subjects_page():
    subjects = AccountSubject.query.order_by(AccountSubject.sort_order, AccountSubject.id).all()
    return render_template('account_subjects.html', subjects=subjects)


@account_subjects_bp.route('/api/account_subjects/', methods=['GET', 'POST'])
def account_subjects_api():
    if request.method == 'POST':
        data = request.form
        s = AccountSubject(
            name=data.get('name'),
            type=data.get('type'),
            is_fixed=data.get('is_fixed') == 'true',
            fixed_amount=int(data.get('fixed_amount') or 0),
            sort_order=int(data.get('sort_order') or 0),
        )
        db.session.add(s)
        db.session.commit()
    return _rows_response()


@account_subjects_bp.route('/api/account_subjects/<int:id>', methods=['PUT', 'DELETE'])
def account_subject_detail(id):
    s = AccountSubject.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(s)
        db.session.commit()
        return _rows_response()
    data = request.form
    s.name         = data.get('name')
    s.type         = data.get('type')
    s.is_fixed     = data.get('is_fixed') == 'true'
    s.fixed_amount = int(data.get('fixed_amount') or 0)
    s.sort_order   = int(data.get('sort_order') or 0)
    db.session.commit()
    return _rows_response()


@account_subjects_bp.route('/api/account_subjects/<int:id>/edit')
def account_subject_edit_form(id):
    s = AccountSubject.query.get_or_404(id)
    return render_template('_account_subject_row_edit.html', s=s)


@account_subjects_bp.route('/api/account_subjects/<int:id>/cancel')
def account_subject_edit_cancel(id):
    s = AccountSubject.query.get_or_404(id)
    return render_template('_account_subject_row.html', s=s)


def _rows_response():
    subjects = AccountSubject.query.order_by(AccountSubject.sort_order, AccountSubject.id).all()
    return render_template('_account_subject_rows.html', subjects=subjects)

from flask import Blueprint, render_template, request
from datetime import datetime, date, date as date_type

from extensions import db
from models import Ledger, AccountSubject, PaymentAccount, Client, Driver
from utils import generate_id

ledger_bp = Blueprint('ledger', __name__)


def _form_data():
    return {
        'subjects': AccountSubject.query.order_by(AccountSubject.sort_order, AccountSubject.id).all(),
        'accounts': PaymentAccount.query.filter_by(is_active=True).order_by(PaymentAccount.id).all(),
        'clients':  Client.query.order_by(Client.id).all(),
        'drivers':  Driver.query.order_by(Driver.id).all(),
    }


def _build_query(year, month, q, ledger_type, subject_id):
    prefix = f"{year}-{month:02d}"
    query = Ledger.query.filter(
        db.func.strftime('%Y-%m', Ledger.date) == prefix
    )
    if ledger_type:
        query = query.filter(Ledger.type == ledger_type)
    if subject_id:
        query = query.filter(Ledger.account_subject_id == subject_id)
    if q:
        query = query.join(Client, isouter=True).join(Driver, isouter=True).filter(
            db.or_(
                Client.name.contains(q),
                Driver.name.contains(q),
                Ledger.memo.contains(q)
            )
        )
    return query.order_by(Ledger.date, Ledger.id)


# ── 입출금 목록 페이지 ────────────────────
@ledger_bp.route('/ledger')
def ledger_page():
    today = datetime.today()
    year  = int(request.args.get('year',  today.year))
    month = int(request.args.get('month', today.month))
    q           = request.args.get('q', '').strip()
    ledger_type = request.args.get('ledger_type', '').strip()
    subject_id  = request.args.get('subject_id', '').strip()

    entries = _build_query(year, month, q, ledger_type, subject_id).all()

    income  = sum(e.amount for e in entries if e.type == '입금')
    expense = sum(e.amount for e in entries if e.type == '출금')

    years = list(range(today.year - 1, today.year + 2))
    fd    = _form_data()

    return render_template('ledger.html',
                           entries=entries,
                           income=income, expense=expense,
                           year=year, month=month, years=years,
                           q=q, ledger_type=ledger_type, subject_id=subject_id,
                           months=range(1, 13), **fd)


# ── 입출금 추가 ───────────────────────────
@ledger_bp.route('/api/ledger/', methods=['POST'])
def ledger_create():
    data = request.form
    raw_date = data.get('date')
    try:
        parsed_date = datetime.strptime(raw_date, '%Y-%m-%d').date() if raw_date else date.today()
    except ValueError:
        parsed_date = date.today()

    e = Ledger(
        id=generate_id('L', Ledger),
        date=parsed_date,
        type=data.get('type'),
        amount=int(data.get('amount') or 0),
        payment_account_id=data.get('payment_account_id') or None,
        account_subject_id=int(data.get('account_subject_id')) if data.get('account_subject_id') else None,
        client_id=data.get('client_id') or None,
        driver_id=data.get('driver_id') or None,
        receipt_type=data.get('receipt_type') or None,
        memo=data.get('memo') or None,
    )
    db.session.add(e)
    db.session.commit()
    return _rows_response(data)


# ── 입출금 수정 / 삭제 ────────────────────
@ledger_bp.route('/api/ledger/<id>', methods=['PUT', 'DELETE'])
def ledger_detail(id):
    e = Ledger.query.get_or_404(id)
    data = request.form

    if request.method == 'DELETE':
        db.session.delete(e)
        db.session.commit()
        return _rows_response(data)

    raw_date2 = data.get('date')
    try:
        e.date = datetime.strptime(raw_date2, '%Y-%m-%d').date() if raw_date2 else e.date
    except ValueError:
        pass
    e.type               = data.get('type')
    e.amount             = int(data.get('amount') or 0)
    e.payment_account_id = data.get('payment_account_id') or None
    e.account_subject_id = int(data.get('account_subject_id')) if data.get('account_subject_id') else None
    e.client_id          = data.get('client_id') or None
    e.driver_id          = data.get('driver_id') or None
    e.receipt_type       = data.get('receipt_type') or None
    e.memo               = data.get('memo') or None
    db.session.commit()
    return _rows_response(data)


# ── 인라인 수정 토글 ──────────────────────
@ledger_bp.route('/api/ledger/<id>/edit')
def ledger_edit_form(id):
    e = Ledger.query.get_or_404(id)
    return render_template('_ledger_row_edit.html', e=e, **_form_data())


@ledger_bp.route('/api/ledger/<id>/cancel')
def ledger_edit_cancel(id):
    e = Ledger.query.get_or_404(id)
    return render_template('_ledger_row.html', e=e)


# ── 이번달 고정지출 생성 ──────────────────
@ledger_bp.route('/api/ledger/generate_fixed', methods=['POST'])
def generate_fixed():
    today = date.today()
    subjects = AccountSubject.query.filter_by(is_fixed=True).all()
    for s in subjects:
        exists = Ledger.query.filter(
            Ledger.account_subject_id == s.id,
            db.func.strftime('%Y-%m', Ledger.date) == today.strftime('%Y-%m')
        ).first()
        if not exists:
            e = Ledger(
                id=generate_id('L', Ledger),
                date=today,
                type='출금',
                amount=s.fixed_amount,
                account_subject_id=s.id,
                memo=f'{today.month}월 고정지출 자동생성',
            )
            db.session.add(e)
    db.session.commit()
    return _rows_response({})


# ── 결제수단 선택 시 증빙유형 반환 ──────────
@ledger_bp.route('/api/payment_accounts/<id>/receipt_type')
def payment_account_receipt_type(id):
    pa = PaymentAccount.query.get_or_404(id)
    if pa.type == '카드':
        return '카드영수증'
    return ''   # 계좌/현금은 프론트에서 선택


def _rows_response(data):
    today = datetime.today()
    year   = int(data.get('year',  today.year))
    month  = int(data.get('month', today.month))
    q           = data.get('q', '')
    ledger_type = data.get('ledger_type', '')
    subject_id  = data.get('subject_id', '')
    entries = _build_query(year, month, q, ledger_type, subject_id).all()
    income  = sum(e.amount for e in entries if e.type == '입금')
    expense = sum(e.amount for e in entries if e.type == '출금')
    return render_template('_ledger_rows.html',
                           entries=entries,
                           income=income, expense=expense)

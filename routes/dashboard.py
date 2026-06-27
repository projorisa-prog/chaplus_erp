from flask import Blueprint, render_template
from datetime import datetime, date

from extensions import db
from models import (Quote, OperationOrder, OperationDetail,
                    Ledger, Client, Driver)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    today  = date.today()
    year   = today.year
    month  = today.month
    prefix = f"{year}-{month:02d}"

    # ── 이달 운행 건수 / 청구합계 ──────────
    orders = (OperationOrder.query
              .filter(OperationOrder.start_datetime.like(f"{prefix}%"))
              .all())
    month_order_count = len(orders)
    month_bill = sum(
        od.unit_price + od.region_surcharge + od.time_surcharge + od.lodging_fee
        for o in orders for od in o.details
    )

    # ── 이달 견적 건수 ────────────────────
    month_quote_count = (Quote.query
                         .filter(Quote.created_date >= date(year, month, 1))
                         .count())

    # ── 예약확정 대기 ─────────────────────
    pending_count = OperationOrder.query.filter_by(status='예약확정').count()

    # ── 이달 입출금 ───────────────────────
    ledger_entries = (Ledger.query
                      .filter(db.func.strftime('%Y-%m', Ledger.date) == prefix)
                      .all())
    month_income  = sum(e.amount for e in ledger_entries if e.type == '입금')
    month_expense = sum(e.amount for e in ledger_entries if e.type == '출금')

    # ── 최근 운행 5건 ─────────────────────
    recent_orders = (OperationOrder.query
                     .order_by(OperationOrder.id.desc())
                     .limit(5).all())

    # ── 최근 견적 5건 ─────────────────────
    recent_quotes = (Quote.query
                     .order_by(Quote.id.desc())
                     .limit(5).all())

    # ── 미수금 TOP5 거래처 ────────────────
    clients = Client.query.all()
    client_unpaid = []
    for c in clients:
        orders_c = (OperationOrder.query
                    .filter_by(client_id=c.id)
                    .filter(OperationOrder.start_datetime.like(f"{prefix}%"))
                    .all())
        bill = sum(
            od.unit_price + od.region_surcharge + od.time_surcharge + od.lodging_fee
            for o in orders_c for od in o.details
        )
        income = sum(
            e.amount for e in Ledger.query
            .filter_by(client_id=c.id, type='입금')
            .filter(db.func.strftime('%Y-%m', Ledger.date) == prefix).all()
        )
        unpaid = bill - income
        if unpaid > 0:
            client_unpaid.append({'name': c.name, 'unpaid': unpaid})
    client_unpaid.sort(key=lambda x: x['unpaid'], reverse=True)

    return render_template('index.html',
                           today=today,
                           year=year, month=month,
                           month_order_count=month_order_count,
                           month_bill=month_bill,
                           month_quote_count=month_quote_count,
                           pending_count=pending_count,
                           month_income=month_income,
                           month_expense=month_expense,
                           month_profit=month_income - month_expense,
                           recent_orders=recent_orders,
                           recent_quotes=recent_quotes,
                           client_unpaid=client_unpaid[:5])

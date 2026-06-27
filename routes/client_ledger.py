from flask import Blueprint, render_template, request
from datetime import datetime

from extensions import db
from models import OperationOrder, OperationDetail, Ledger, Client

client_ledger_bp = Blueprint('client_ledger', __name__)


@client_ledger_bp.route('/client_ledger')
def client_ledger_page():
    today = datetime.today()
    year      = int(request.args.get('year',  today.year))
    month     = int(request.args.get('month', today.month))
    client_id = request.args.get('client_id', '').strip()

    clients = Client.query.order_by(Client.id).all()
    prefix  = f"{year}-{month:02d}"

    # 운행 청구 (운행명세 기준)
    bill_rows = []
    bill_total = 0
    if client_id:
        orders = (OperationOrder.query
                  .filter_by(client_id=client_id)
                  .filter(OperationOrder.start_datetime.like(f"{prefix}%"))
                  .order_by(OperationOrder.id).all())
        for o in orders:
            for od in o.details:
                sub = od.unit_price + od.region_surcharge + od.time_surcharge + od.lodging_fee
                bill_rows.append({
                    'order_id':    o.id,
                    'run_date':    od.run_date,
                    'product_type': od.product_type or '',
                    'vehicle':     f"{od.vehicle.name}({od.vehicle.plate_number})" if od.vehicle and od.vehicle.plate_number
                                   else (od.vehicle.name if od.vehicle else ''),
                    'unit_price':  od.unit_price,
                    'region_surcharge': od.region_surcharge,
                    'time_surcharge':   od.time_surcharge,
                    'lodging_fee': od.lodging_fee,
                    'sub':         sub,
                })
                bill_total += sub

    # 입금 내역 (ledger 기준)
    income_rows = []
    income_total = 0
    if client_id:
        entries = (Ledger.query
                   .filter_by(client_id=client_id, type='입금')
                   .filter(db.func.strftime('%Y-%m', Ledger.date) == prefix)
                   .order_by(Ledger.date, Ledger.id).all())
        for e in entries:
            income_rows.append({
                'date':    e.date,
                'amount':  e.amount,
                'account': e.payment_account.name if e.payment_account else '',
                'receipt': e.receipt_type or '',
                'memo':    e.memo or '',
            })
            income_total += e.amount

    balance = income_total - bill_total
    years = list(range(today.year - 1, today.year + 2))

    return render_template('client_ledger.html',
                           clients=clients,
                           client_id=client_id,
                           selected_client=Client.query.get(client_id) if client_id else None,
                           bill_rows=bill_rows, bill_total=bill_total,
                           income_rows=income_rows, income_total=income_total,
                           balance=balance,
                           year=year, month=month, years=years,
                           months=range(1, 13))

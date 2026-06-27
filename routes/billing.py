from flask import Blueprint, render_template, request
from sqlalchemy import extract
from datetime import datetime

from extensions import db
from models import OperationOrder, OperationDetail, Client

billing_bp = Blueprint('billing', __name__)


@billing_bp.route('/billing')
def billing_page():
    today = datetime.today()
    year  = int(request.args.get('year',  today.year))
    month = int(request.args.get('month', today.month))
    q     = request.args.get('q', '').strip()

    # 운행명세를 운행시작일 기준 월 필터
    prefix = f"{year}-{month:02d}"
    query = (OperationOrder.query
             .join(Client)
             .filter(OperationOrder.start_datetime.like(f"{prefix}%")))
             
    if q:
        query = query.filter(Client.name.contains(q))

    orders = query.order_by(OperationOrder.id.desc()).all()

    # 거래처별 집계
    client_totals = {}
    grand_bill = 0
    for o in orders:
        bill = sum(
            od.unit_price + od.region_surcharge + od.time_surcharge + od.lodging_fee
            for od in o.details
        )
        cname = o.client.name
        client_totals[cname] = client_totals.get(cname, 0) + bill
        grand_bill += bill

    years = list(range(today.year - 1, today.year + 2))

    return render_template('billing.html',
                           orders=orders,
                           client_totals=client_totals,
                           grand_bill=grand_bill,
                           year=year, month=month,
                           years=years, q=q,
                           months=range(1, 13))

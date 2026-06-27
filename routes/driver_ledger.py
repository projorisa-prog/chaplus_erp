from flask import Blueprint, render_template, request
from datetime import datetime

from extensions import db
from models import OperationOrder, OperationDetail, Ledger, Driver

driver_ledger_bp = Blueprint('driver_ledger', __name__)


@driver_ledger_bp.route('/driver_ledger')
def driver_ledger_page():
    today     = datetime.today()
    year      = int(request.args.get('year',  today.year))
    month     = int(request.args.get('month', today.month))
    driver_id = request.args.get('driver_id', '').strip()

    drivers = Driver.query.order_by(Driver.id).all()
    prefix  = f"{year}-{month:02d}"

    # 운행 지급 (운행명세 기준)
    pay_rows  = []
    pay_total = 0
    pay_sums  = {k: 0 for k in ['base_pay','driver_time_surcharge',
                                  'fuel_cost','toll_fee','parking_fee',
                                  'meal_fee','lodging_pay']}
    if driver_id:
        details = (OperationDetail.query
                   .filter_by(driver_id=driver_id)
                   .filter(OperationDetail.run_date.like(f"{prefix}%"))
                   .order_by(OperationDetail.run_date, OperationDetail.id).all())
        for od in details:
            sub = ((od.base_pay or 0) + (od.driver_time_surcharge or 0) +
                   (od.fuel_cost or 0) + (od.toll_fee or 0) +
                   (od.parking_fee or 0) + (od.meal_fee or 0) + (od.lodging_pay or 0))
            o = od.order
            pay_rows.append({
                'order_id':    o.id,
                'client':      o.client.name,
                'run_date':    od.run_date,
                'product_type': od.product_type or '',
                'base_pay':    od.base_pay or 0,
                'driver_time_surcharge': od.driver_time_surcharge or 0,
                'fuel_cost':   od.fuel_cost or 0,
                'toll_fee':    od.toll_fee or 0,
                'parking_fee': od.parking_fee or 0,
                'meal_fee':    od.meal_fee or 0,
                'lodging_pay': od.lodging_pay or 0,
                'sub':         sub,
            })
            pay_total += sub
            for k in pay_sums:
                pay_sums[k] += getattr(od, k) or 0

    # 출금 내역 (ledger 기준 - 기사 출금)
    payment_rows  = []
    payment_total = 0
    if driver_id:
        entries = (Ledger.query
                   .filter_by(driver_id=driver_id, type='출금')
                   .filter(db.func.strftime('%Y-%m', Ledger.date) == prefix)
                   .order_by(Ledger.date, Ledger.id).all())
        for e in entries:
            payment_rows.append({
                'date':    e.date,
                'amount':  e.amount,
                'account': e.payment_account.name if e.payment_account else '',
                'memo':    e.memo or '',
            })
            payment_total += e.amount

    unpaid = pay_total - payment_total
    years  = list(range(today.year - 1, today.year + 2))

    return render_template('driver_ledger.html',
                           drivers=drivers,
                           driver_id=driver_id,
                           selected_driver=Driver.query.get(driver_id) if driver_id else None,
                           pay_rows=pay_rows, pay_total=pay_total, pay_sums=pay_sums,
                           payment_rows=payment_rows, payment_total=payment_total,
                           unpaid=unpaid,
                           year=year, month=month, years=years,
                           months=range(1, 13))

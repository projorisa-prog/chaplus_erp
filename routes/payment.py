from flask import Blueprint, render_template, request
from sqlalchemy import extract
from datetime import datetime

from extensions import db
from models import OperationOrder, OperationDetail, Driver, Client

payment_bp = Blueprint('payment', __name__)


@payment_bp.route('/payment')
def payment_page():
    today = datetime.today()
    year  = int(request.args.get('year',  today.year))
    month = int(request.args.get('month', today.month))
    q     = request.args.get('q', '').strip()
    team  = request.args.get('team', '').strip()

    # 운행명세를 운행시작일 기준 월 필터
    prefix = f"{year}-{month:02d}"
    query = (OperationOrder.query
             .join(Client)
             .filter(OperationOrder.start_datetime.like(f"{prefix}%")))

    if q:
        query = query.filter(Client.name.contains(q))

    orders = query.order_by(OperationOrder.id.desc()).all()

    # 기사별 집계
    driver_totals = {}   # driver_id → {name, type, team_leader, pay합계항목들}
    grand_pay = 0

    for o in orders:
        for od in o.details:
            if not od.driver_id:
                continue
            driver = od.driver
            if team and (driver.team_leader or '') != team:
                continue
            if q and q not in o.client.name:
                continue

            did = od.driver_id
            if did not in driver_totals:
                driver_totals[did] = {
                    'name': driver.name,
                    'type': driver.type,
                    'team_leader': driver.team_leader or '',
                    'base_pay': 0,
                    'driver_time_surcharge': 0,
                    'fuel_cost': 0,
                    'toll_fee': 0,
                    'parking_fee': 0,
                    'meal_fee': 0,
                    'lodging_pay': 0,
                    'total': 0,
                    'details': [],
                }
            t = driver_totals[did]
            t['base_pay']              += od.base_pay or 0
            t['driver_time_surcharge'] += od.driver_time_surcharge or 0
            t['fuel_cost']             += od.fuel_cost or 0
            t['toll_fee']              += od.toll_fee or 0
            t['parking_fee']           += od.parking_fee or 0
            t['meal_fee']              += od.meal_fee or 0
            t['lodging_pay']           += od.lodging_pay or 0
            sub = ((od.base_pay or 0) + (od.driver_time_surcharge or 0) +
                   (od.fuel_cost or 0) + (od.toll_fee or 0) +
                   (od.parking_fee or 0) + (od.meal_fee or 0) + (od.lodging_pay or 0))
            t['total'] += sub
            grand_pay  += sub
            t['details'].append({
                'order_id': o.id,
                'run_date': od.run_date,
                'client': o.client.name,
                'product_type': od.product_type or '',
                'base_pay': od.base_pay or 0,
                'driver_time_surcharge': od.driver_time_surcharge or 0,
                'fuel_cost': od.fuel_cost or 0,
                'toll_fee': od.toll_fee or 0,
                'parking_fee': od.parking_fee or 0,
                'meal_fee': od.meal_fee or 0,
                'lodging_pay': od.lodging_pay or 0,
                'sub': sub,
            })

    # 팀장별 집계
    team_totals = {}
    for did, t in driver_totals.items():
        tl = t['team_leader'] or '(팀장없음)'
        team_totals[tl] = team_totals.get(tl, 0) + t['total']

    years = list(range(today.year - 1, today.year + 2))
    team_leaders = sorted(set(
        d.team_leader for d in Driver.query.all() if d.team_leader
    ))

    return render_template('payment.html',
                           driver_totals=driver_totals,
                           team_totals=team_totals,
                           grand_pay=grand_pay,
                           year=year, month=month,
                           years=years, q=q, team=team,
                           months=range(1, 13),
                           team_leaders=team_leaders)

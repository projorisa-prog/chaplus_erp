from extensions import db
from datetime import datetime


# ─────────────────────────────────────────
# 2.1 vehicles (차종)
# ─────────────────────────────────────────
class Vehicle(db.Model):
    __tablename__ = 'vehicles'

    id = db.Column(db.String(10), primary_key=True)         # V26001
    name = db.Column(db.String(50), nullable=False)         # 차종명
    capacity = db.Column(db.Integer)                        # 인승
    vehicle_type = db.Column(db.String(10), nullable=False) # 자차 / 타사
    plate_number = db.Column(db.String(20))                 # 자차만 입력


# ─────────────────────────────────────────
# 2.2 clients (거래처)
# ─────────────────────────────────────────
class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.String(10), primary_key=True)         # C26001
    name = db.Column(db.String(100), nullable=False)
    business_no = db.Column(db.String(20))                  # 사업자번호
    ceo_name = db.Column(db.String(50))                     # 대표자
    business_type = db.Column(db.String(50))                # 업태
    business_item = db.Column(db.String(50))                # 종목
    manager_name = db.Column(db.String(50))                 # 담당자
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    tax_invoice_email = db.Column(db.String(100))           # 세금계산서 이메일
    vat_type = db.Column(db.String(10))                     # 포함 / 별도 / 면세


# ─────────────────────────────────────────
# 2.3 drivers (기사)
# ─────────────────────────────────────────
class Driver(db.Model):
    __tablename__ = 'drivers'

    id = db.Column(db.String(10), primary_key=True)         # D26001
    type = db.Column(db.String(10), nullable=False)         # 대리 / 용역
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    team_leader = db.Column(db.String(50))                  # 팀장
    base_pay = db.Column(db.Integer, default=0)             # 기본급
    ot_pay = db.Column(db.Integer, default=0)                # 추가시간당 단가

    # 용역기사만 사용
    vehicle_id = db.Column(db.String(10), db.ForeignKey('vehicles.id'))
    plate_number = db.Column(db.String(20))                 # 용역 고정 차량번호
    incheon_airport_fee = db.Column(db.Integer, default=0)
    gimpo_airport_fee = db.Column(db.Integer, default=0)

    vehicle = db.relationship('Vehicle')


# ─────────────────────────────────────────
# 2.4 quotes (견적 부모)
# ─────────────────────────────────────────
class Quote(db.Model):
    __tablename__ = 'quotes'

    id = db.Column(db.String(10), primary_key=True)         # Q26001
    client_id = db.Column(db.String(10), db.ForeignKey('clients.id'), nullable=False)
    created_date = db.Column(db.Date, default=datetime.today)
    start_datetime = db.Column(db.String(20))                # YYYY-MM-DD HH:MM
    end_datetime = db.Column(db.String(20))                  # YYYY-MM-DD
    status = db.Column(db.String(10), default='견적')        # 견적 / 확정 / 취소

    client = db.relationship('Client')
    details = db.relationship(
        'QuoteDetail',
        backref='quote',
        cascade='all, delete-orphan',
        order_by='QuoteDetail.run_date'
    )


# ─────────────────────────────────────────
# 2.5 quote_details (견적 자식)
# ─────────────────────────────────────────
class QuoteDetail(db.Model):
    __tablename__ = 'quote_details'

    id = db.Column(db.String(10), primary_key=True)         # QD26001
    quote_id = db.Column(db.String(10), db.ForeignKey('quotes.id'), nullable=False)
    run_date = db.Column(db.String(10))                      # YYYY-MM-DD
    product_type = db.Column(db.String(20))                  # Full-Day/Half-Day/DropOff/PickUp
    vehicle_id = db.Column(db.String(10), db.ForeignKey('vehicles.id'))
    includes = db.Column(db.String(100))                     # 포함내역
    qty = db.Column(db.Integer, default=1)                   # 대(수량)
    unit_price = db.Column(db.Integer, default=0)
    region = db.Column(db.String(50))                        # 서울외지역
    region_surcharge = db.Column(db.Integer, default=0)
    use_time = db.Column(db.String(20))                      # 예: 10:00-25:00
    extra_time = db.Column(db.Integer, default=0)
    time_surcharge = db.Column(db.Integer, default=0)
    lodging_fee = db.Column(db.Integer, default=0)

    vehicle = db.relationship('Vehicle')


# ─────────────────────────────────────────
# 2.6 operation_orders (운행 부모)
# ─────────────────────────────────────────
class OperationOrder(db.Model):
    __tablename__ = 'operation_orders'

    id = db.Column(db.String(10), primary_key=True)         # O26001
    quote_id = db.Column(db.String(10), db.ForeignKey('quotes.id'))  # 없을 수 있음
    client_id = db.Column(db.String(10), db.ForeignKey('clients.id'), nullable=False)
    start_datetime = db.Column(db.String(20))                 # YYYY-MM-DD HH:MM
    end_datetime = db.Column(db.String(20))                   # YYYY-MM-DD
    departure = db.Column(db.String(100))                     # 출발지
    product_type = db.Column(db.String(20))
    status = db.Column(db.String(10), default='예약확정')      # 예약확정 / 운행

    client = db.relationship('Client')
    quote = db.relationship('Quote')
    details = db.relationship(
        'OperationDetail',
        backref='order',
        cascade='all, delete-orphan',
        order_by='OperationDetail.run_date'
    )


# ─────────────────────────────────────────
# 2.7 operation_details (운행 자식 - 기사 1명 = 1행)
# ─────────────────────────────────────────
class OperationDetail(db.Model):
    __tablename__ = 'operation_details'

    id = db.Column(db.String(10), primary_key=True)          # OD26001
    order_id = db.Column(db.String(10), db.ForeignKey('operation_orders.id'), nullable=False)
    run_date = db.Column(db.String(10))                       # YYYY-MM-DD
    vehicle_id = db.Column(db.String(10), db.ForeignKey('vehicles.id'))

    # ── 청구 ──
    unit_price = db.Column(db.Integer, default=0)
    region = db.Column(db.String(50))
    region_surcharge = db.Column(db.Integer, default=0)
    start_time = db.Column(db.String(10))                     # HH:MM (25:00 허용)
    end_time = db.Column(db.String(10))
    extra_time = db.Column(db.Integer, default=0)
    time_surcharge = db.Column(db.Integer, default=0)
    lodging_fee = db.Column(db.Integer, default=0)            # 숙식비(청구)

    # ── 지급 ──
    driver_id = db.Column(db.String(10), db.ForeignKey('drivers.id'))
    plate_number = db.Column(db.String(20))                   # 자동 or 직접입력
    base_pay = db.Column(db.Integer, default=0)
    driver_extra_time = db.Column(db.Integer, default=0)
    driver_time_surcharge = db.Column(db.Integer, default=0)

    fuel_cost = db.Column(db.Integer, default=0)
    fuel_card = db.Column(db.String(10))                      # 회사카드 / 본인카드
    toll_fee = db.Column(db.Integer, default=0)
    toll_card = db.Column(db.String(10))
    parking_fee = db.Column(db.Integer, default=0)
    parking_card = db.Column(db.String(10))
    meal_fee = db.Column(db.Integer, default=0)
    meal_card = db.Column(db.String(10))
    lodging_pay = db.Column(db.Integer, default=0)             # 숙식비(지급)
    lodging_card = db.Column(db.String(10))

    vehicle = db.relationship('Vehicle')
    driver = db.relationship('Driver')


# ─────────────────────────────────────────
# 2.8 account_subjects (계정과목)
# ─────────────────────────────────────────
class AccountSubject(db.Model):
    __tablename__ = 'account_subjects'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10), nullable=False)           # 수입 / 지출
    is_fixed = db.Column(db.Boolean, default=False)           # 고정지출 여부
    fixed_amount = db.Column(db.Integer, default=0)
    sort_order = db.Column(db.Integer, default=0)


# ─────────────────────────────────────────
# 2.9 payment_accounts (결제수단)
# ─────────────────────────────────────────
class PaymentAccount(db.Model):
    __tablename__ = 'payment_accounts'

    id = db.Column(db.String(10), primary_key=True)           # PA26001
    type = db.Column(db.String(10), nullable=False)           # 카드 / 계좌 / 현금
    name = db.Column(db.String(50), nullable=False)           # 별칭
    number = db.Column(db.String(50))                         # 카드/계좌번호
    bank_name = db.Column(db.String(50))                      # 은행명/카드사명
    holder = db.Column(db.String(50))                         # 예금주/명의자
    is_active = db.Column(db.Boolean, default=True)
    memo = db.Column(db.String(200))


# ─────────────────────────────────────────
# 2.10 ledger (입출금 장부)
# ─────────────────────────────────────────
class Ledger(db.Model):
    __tablename__ = 'ledger'

    id = db.Column(db.String(10), primary_key=True)           # L26001
    date = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(10), nullable=False)           # 입금 / 출금
    amount = db.Column(db.Integer, nullable=False)
    payment_account_id = db.Column(db.String(10), db.ForeignKey('payment_accounts.id'))
    account_subject_id = db.Column(db.Integer, db.ForeignKey('account_subjects.id'))
    client_id = db.Column(db.String(10), db.ForeignKey('clients.id'))   # 입금시
    driver_id = db.Column(db.String(10), db.ForeignKey('drivers.id'))   # 출금시
    receipt_type = db.Column(db.String(20))                    # 카드영수증/세금계산서/현금영수증/없음
    memo = db.Column(db.String(200))

    payment_account = db.relationship('PaymentAccount')
    account_subject = db.relationship('AccountSubject')
    client = db.relationship('Client')
    driver = db.relationship('Driver')


# ─────────────────────────────────────────
# 2.11 settings (설정)
# ─────────────────────────────────────────
class Settings(db.Model):
    __tablename__ = 'settings'

    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.Text)

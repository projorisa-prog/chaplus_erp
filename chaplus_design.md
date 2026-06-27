# 차플러스 ERP 완전 설계서

> 작성일: 2026-06-18  
> 스택: Flask + SQLite + HTMX + Tailwind CSS  
> 목적: 기사포함렌터카 차플러스 업무 전산화

---

## 1. 시스템 아키텍처

```
[Browser]
  ↕ HTMX (HTML 부분 업데이트)
[Flask Backend]
  ↕ SQLAlchemy ORM
[SQLite DB]
  ↕ 스케줄러 (APScheduler)
[Google Drive API] ← 매일 자동 백업
```

### 디렉토리 구조
```
chaplus_erp/
├── app.py                    ← Flask 앱 진입점
├── models.py                 ← DB 모델 전체
├── extensions.py             ← db, migrate, cors
├── scheduler.py              ← 백업 스케줄러
├── requirements.txt
├── reset_db.py               ← DB 초기화 (개발용)
├── fonts/                    ← NanumGothic.ttf 등
├── credentials/              ← Google Drive API 인증파일
│   └── google_credentials.json
├── routes/
│   ├── vehicles.py
│   ├── clients.py
│   ├── drivers.py
│   ├── quotes.py
│   ├── operations.py
│   ├── reports.py
│   ├── ledger.py             ← 입출금 장부
│   ├── account_subjects.py   ← 계정과목
│   ├── payment_accounts.py   ← 결제수단(카드/계좌)
│   ├── pdf.py                ← PDF 다운로드
│   └── settings.py           ← 설정
├── services/
│   ├── time_calc_service.py  ← 시간할증 계산
│   ├── pdf_service.py        ← PDF 생성
│   └── backup_service.py     ← 구글드라이브 백업
├── templates/
│   ├── base.html             ← 사이드바 레이아웃
│   ├── index.html            ← 대시보드
│   ├── vehicles.html
│   ├── clients.html
│   ├── drivers.html
│   ├── quotes.html
│   ├── operations.html
│   ├── billing.html
│   ├── payment.html
│   ├── ledger.html           ← 입출금 관리
│   ├── client_ledger.html    ← 거래처 원장
│   ├── driver_ledger.html    ← 기사 원장
│   ├── receipt.html          ← 지출증빙
│   ├── account_subjects.html ← 계정과목 관리
│   ├── payment_accounts.html ← 결제수단 관리
│   └── settings.html         ← 설정
├── static/
│   └── stamp.png             ← 도장 이미지
└── instance/
    └── chaplus.db
```

---

## 2. DB 스키마 (테이블 11개)

### ID 체계
```
형식: prefix + 년도2자리 + 순번3자리
예시: Q26001, C26001, V26001, D26001
     O26001, OD26001, QD26001, L26001
매년 자동 리셋: 26→27 자동
```

---

### 2.1 vehicles (차종)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | TEXT PK | V26001 |
| name | TEXT | 차종명 |
| capacity | INTEGER | 인승 |
| vehicle_type | TEXT | **자차** / **타사** |
| plate_number | TEXT | 자차만 입력 (타사 NULL) |

**차량번호 자동입력 규칙:**
```
자차 + 대리기사 → vehicles.plate_number (자동, 읽기전용)
타사 + 용역기사 → drivers.plate_number  (자동, 읽기전용)
타사 + 대리기사 → 직접입력 (운행당일 번호)
```

---

### 2.2 clients (거래처)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | TEXT PK | C26001 |
| name | TEXT | 거래처명 |
| business_no | TEXT | 사업자번호 |
| ceo_name | TEXT | 대표자 |
| business_type | TEXT | 업태 |
| business_item | TEXT | 종목 |
| manager_name | TEXT | 담당자 |
| phone | TEXT | 전화 |
| email | TEXT | 이메일 |
| tax_invoice_email | TEXT | 세금계산서 이메일 |
| vat_type | TEXT | **포함** / **별도** / **면세** |

---

### 2.3 drivers (기사)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | TEXT PK | D26001 |
| type | TEXT | **대리** / **용역** |
| name | TEXT | 기사명 |
| phone | TEXT | 연락처 |
| team_leader | TEXT | 팀장 (팀/지사별 지급합계용) |
| base_pay | INTEGER | 기본급 |
| ot_pay | INTEGER | 추가시간당 단가 |
| vehicle_id | TEXT FK | 차종 (용역만, 타사만 조회) |
| plate_number | TEXT | 용역 고정 차량번호 |
| incheon_airport_fee | INTEGER | 인천공항요금 |
| gimpo_airport_fee | INTEGER | 김포공항요금 |

**구분별 입력 필드:**
```
대리: id ~ ot_pay
용역: + vehicle_id, plate_number
```

---

### 2.4 quotes (견적 부모)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | TEXT PK | Q26001 |
| client_id | TEXT FK | 거래처 |
| created_date | DATE | 견적일 (자동, 오늘) |
| start_datetime | TEXT | 운행시작 YYYY-MM-DD HH:MM |
| end_datetime | TEXT | 운행종료 YYYY-MM-DD (날짜만) |
| status | TEXT | **견적** / **확정** / **취소** |

---

### 2.5 quote_details (견적 자식)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | TEXT PK | QD26001 |
| quote_id | TEXT FK | 견적ID |
| run_date | TEXT | 날짜 YYYY-MM-DD |
| product_type | TEXT | Full-Day / Half-Day / DropOff / PickUp |
| vehicle_id | TEXT FK | 차종ID |
| includes | TEXT | 포함내역 (상품구분별 자동생성) |
| qty | INTEGER | 대 (수량) |
| unit_price | INTEGER | 단가 |
| region | TEXT | 서울외지역 (예: 서울-부산) |
| region_surcharge | INTEGER | 지역할증 |
| use_time | TEXT | 이용시간 (예: 10:00-25:00) |
| extra_time | INTEGER | 추가시간 (자동계산) |
| time_surcharge | INTEGER | 시간할증 = 단가/10 × 추가시간 |
| lodging_fee | INTEGER | 숙식 |

**포함내역 자동생성:**
```
Full-Day → 서울/기사/10시간/유류비
Half-Day → 서울/기사/5시간/유류비
DropOff  → 서울/기사/유류비
PickUp   → 서울/기사/유류비
```

**합계 계산:**
```
(단가 × 대 × 1일) + 지역할증 + 시간할증 + 숙식
※ 자식 행은 날짜별 1행 = 1일 기준
```

---

### 2.6 operation_orders (운행 부모)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | TEXT PK | O26001 |
| quote_id | TEXT FK | 견적ID (없을 수 있음) |
| client_id | TEXT FK | 거래처 |
| start_datetime | TEXT | 운행시작 YYYY-MM-DD HH:MM |
| end_datetime | TEXT | 운행종료 YYYY-MM-DD (날짜만) |
| departure | TEXT | 출발지 |
| product_type | TEXT | 상품구분 |
| status | TEXT | **예약확정** / **운행** |

---

### 2.7 operation_details (운행 자식 - 기사 1명 = 1행)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | TEXT PK | OD26001 |
| order_id | TEXT FK | 운행ID |
| run_date | TEXT | 날짜 YYYY-MM-DD |
| vehicle_id | TEXT FK | 차종 |
| **[청구]** | | |
| unit_price | INTEGER | 단가 |
| region | TEXT | 지역 |
| region_surcharge | INTEGER | 지역할증 |
| start_time | TEXT | 시작시간 HH:MM (25:00 허용) |
| end_time | TEXT | 종료시간 HH:MM |
| extra_time | INTEGER | 추가시간 (자동계산) |
| time_surcharge | INTEGER | 단가/10 × extra_time |
| lodging_fee | INTEGER | 숙식비(청구) |
| **[지급]** | | |
| driver_id | TEXT FK | 기사 |
| plate_number | TEXT | 차량번호 (자동 or 직접입력) |
| base_pay | INTEGER | 기본급 (기사테이블 자동) |
| driver_extra_time | INTEGER | 기사추가시간 (= extra_time 기본값) |
| driver_time_surcharge | INTEGER | ot_pay × driver_extra_time |
| fuel_cost | INTEGER | 유류대 |
| fuel_card | TEXT | 회사카드 / 본인카드 |
| toll_fee | INTEGER | 통행료 |
| toll_card | TEXT | 회사카드 / 본인카드 |
| parking_fee | INTEGER | 주차료 |
| parking_card | TEXT | 회사카드 / 본인카드 |
| meal_fee | INTEGER | 식대 |
| meal_card | TEXT | 회사카드 / 본인카드 |
| lodging_pay | INTEGER | 숙식비(지급) |
| lodging_card | TEXT | 회사카드 / 본인카드 |

---

### 2.8 account_subjects (계정과목)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | INTEGER PK | 자동증가 |
| name | TEXT | 계정과목명 |
| type | TEXT | **수입** / **지출** |
| is_fixed | BOOLEAN | 고정지출 여부 |
| fixed_amount | INTEGER | 고정지출 기본금액 |
| sort_order | INTEGER | 정렬순서 |

**기본 계정과목:**
```
[수입]
매출, 기타수입

[지출]
기사지급, 용역지급, 임대료, 보험료,
유류대, 통신비, 소모품, 기타지출
```

---

### 2.9 payment_accounts (결제수단 - 카드/계좌/현금)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | TEXT PK | PA26001 |
| type | TEXT | **카드** / **계좌** / **현금** |
| name | TEXT | 별칭 (예: 국민카드, 기업은행 주거래) |
| number | TEXT | 카드번호 or 계좌번호 (현금은 빈값) |
| bank_name | TEXT | 은행명(계좌) / 카드사명(카드) |
| holder | TEXT | 예금주 / 명의자 |
| is_active | BOOLEAN | 사용여부 |
| memo | TEXT | 비고 |

> 현금은 고정 1개 항목 자동 등록 (번호 없음)  
> 잔액 관리 안함 (단순 결제수단 식별용)  
> 예상 등록 개수: 5개 내외 (확장 가능)

---

### 2.10 ledger (입출금 장부)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | TEXT PK | L26001 |
| date | DATE | 날짜 |
| type | TEXT | **입금** / **출금** |
| amount | INTEGER | 금액 |
| payment_account_id | TEXT FK | 결제수단 (payment_accounts 참조) |
| account_subject_id | INTEGER FK | 계정과목 |
| client_id | TEXT FK | 거래처 (입금시) |
| driver_id | TEXT FK | 기사 (출금시) |
| receipt_type | TEXT | 카드영수증 / 세금계산서 / 현금영수증 / 없음 |
| memo | TEXT | 비고 |

**결제수단 type → 증빙 자동처리:**
```
payment_accounts.type = 카드 → 증빙: 카드영수증 (자동고정, 선택불가)
payment_accounts.type = 계좌 → 증빙: 세금계산서 / 현금영수증 / 없음 (선택)
payment_accounts.type = 현금 → 증빙: 세금계산서 / 현금영수증 / 없음 (선택)
```

---

### 2.11 settings (설정)

| 필드 | 타입 | 설명 |
|------|------|------|
| key | TEXT PK | 설정키 |
| value | TEXT | 설정값 |

**설정 키 목록:**
```
회사정보:
  company_name       상호
  company_ceo        대표자
  company_address    주소
  company_biz_type   업태
  company_biz_item   업종
  company_phone      연락처
  company_email      이메일

PDF NOTE:
  note_quote         견적서 NOTE
  note_bill          청구서 NOTE

백업:
  backup_time        백업 실행시간 (예: 23:00)
  backup_folder_id   구글드라이브 폴더ID
```

---

## 3. 비즈니스 로직

### 3.1 시간할증 계산

```
[Half-Day 기준: 5시간]
총 운행시간 >= 5시간 30분(330분) → Full-Day 자동 전환

[Full-Day 기준: 10시간]
over_min = 총운행분 - 600
over_min <= 29  → extra_time = 0
over_min >= 30  → extra_time = ceil(over_min / 60)

[청구 시간할증]
time_surcharge = 단가 / 10 × extra_time

[기사 시간할증]
driver_time_surcharge = ot_pay × driver_extra_time

[DropOff / PickUp]
추가시간 없음
```

### 3.2 지급 계산

```
[대리기사]
지급 = 기본급 + 기사시간할증
     + 본인카드 항목만 (유류대 + 통행료 + 주차료 + 식대 + 숙박)
※ 회사카드 항목은 지급 제외

[용역기사]
지급 = 기본급 + 지역할증 + 기사시간할증 + 주차료 + 숙박
※ 유류대, 통행료, 식대는 기본급에 포함 (별도 지급 없음)
```

### 3.3 청구 합계

```
(단가 × 일수) + 지역할증 + 시간할증 + 숙식
※ 견적 자식은 1행 = 1일 기준
```

---

## 4. 화면 구성 (15개)

### 4.1 공통 툴바 구조 (견적/운행/청구/지급/입출금)

```
┌─────────────────────────────────────────────────────────────────┐
│ [2026▼] [1][2][3][4][5][6][7][8][9][10][11][12]                │
│ 시작일[________] ~ 종료일[________]  [검색어____]  [조회][초기화]│
├─────────────────────────────────────────────────────────────────┤
│ [전체N] [상태1 N] [상태2 N] ...  ← 상태 탭                      │
├─────────────────────────────────────────────────────────────────┤
│ [+추가] [✎수정] [🗑삭제] [📋복사] [📄PDF]      [☐전체선택]     │
└─────────────────────────────────────────────────────────────────┘
```

**월 버튼 기준:** 운행시작일  
**연도 기본값:** 올해, 선택 가능 (올해-1 ~ 올해+1)

### 4.2 버튼 활성/비활성 규칙

| 버튼 | 0개 | 1개 | 2개+ |
|------|-----|-----|------|
| 추가 | ✅ | ✅ (선택초기화) | ✅ (선택초기화) |
| 수정 | ❌ | ✅ | ❌ |
| 삭제 | ❌ | ✅ | ✅ |
| 복사 | ❌ | ✅ | ❌ |
| 운행확정 | ❌ | ✅ | ❌ |
| PDF | ❌ | ✅ | ❌ |

**삭제:** "N건을 삭제하시겠습니까?" 재확인  
**행 클릭:** 체크박스 토글 + 하이라이트

### 4.3 페이지별 상세

#### 대시보드 (index.html)
```
상단 요약 카드 4개:
이달 운행 건수 / 이달 견적 건수 / 예약확정 대기 / 이달 청구 합계

하단 2분할:
좌: 최근 운행 목록 (8건)
우: 최근 견적 목록 (8건)
```

#### 견적관리 (quotes.html)
```
검색: 년도+월, 기간, 거래처명
상태탭: [전체] [견적중] [확정] [취소]
버튼: 추가 / 수정 / 삭제 / 복사추가 / 운행확정 / 📄견적서PDF

[상단 - 견적 목록]
☐ | 견적ID | 거래처 | 견적일 | 운행시작 | 운행종료 | 상태

[하단 - 선택된 견적의 자식 목록]
날짜 | 상품구분 | 차종(구분) | 대 | 단가 | 포함내역 |
서울외지역 | 지역할증 | 이용시간 | 추가시간 | 시간할증 | 숙식 | 합계
```

**복사추가 동작:**
```
부모: 거래처, 상품구분 복사 / 날짜 오늘로 / 상태 = 견적
자식: 차종, 단가, 지역할증, 포함내역 복사 / 날짜 원본 유지
→ 새 ID 발급 후 편집창 열림
```

#### 운행관리 (operations.html)
```
검색: 년도+월, 기간, 거래처명
상태탭: [전체] [예약확정] [운행]
버튼: 추가 / 수정 / 삭제 / 복사추가 / 📄청구서PDF

[상단 - 운행 목록]
☐ | 운행ID | 견적ID | 거래처 | 운행시작 | 운행종료 | 출발지 | 상품구분 | 상태

[하단 - 선택된 운행의 자식 목록 (기사별)]
날짜 | 차종 | 단가 | 지역 | 지역할증 | 시작 | 종료 | 추가 | 시간할증 |
숙식(청구) | 기사 | 차량번호 | 기본급 | 기사추가 | 기사할증 |
유류대 | 통행료 | 주차료 | 식대 | 숙식(지급) | 📋메시지복사
```

**복사추가 동작:**
```
부모: 거래처, 출발지, 상품구분 복사 / 날짜 오늘로 / 상태 = 예약확정
자식: 차종, 단가, 지역할증 복사 / 기사 초기화 / 날짜 원본 유지
→ 새 ID 발급 후 편집창 열림
```

#### 청구관리 (billing.html)
```
검색: 년도+월, 기간, 거래처명
버튼: 없음 (조회/집계 전용, PDF는 운행관리에서)

운행ID별 소계 + Grand Total 표시
```

#### 지급관리 (payment.html)
```
검색: 년도+월, 기간, 기사명, 팀장명
버튼: 📄지급명세서PDF (기사 1명 선택)

기사별 소계 + 팀장별 소계 + Grand Total 표시
대리: 본인카드 항목만 경비 표시
용역: 주차료, 숙박만 표시
```

#### 차량관리 (vehicles.html)
```
검색: 차종명, 구분(자차/타사)
버튼: 추가 / 수정 / 삭제
```

#### 기사관리 (drivers.html)
```
검색: 기사명, 구분(대리/용역), 팀장명
버튼: 추가 / 수정 / 삭제
```

#### 거래처관리 (clients.html)
```
검색: 거래처명, 부가세구분
버튼: 추가 / 수정 / 삭제
```

#### 입출금관리 (ledger.html)
```
검색: 년도+월, 기간, 입출금구분, 계정과목, 거래처/기사
버튼: 추가 / 수정 / 삭제
고정지출: [이번달 고정지출 생성] 버튼 별도

[목록]
☐ | 날짜 | 입출금 | 금액 | 결제수단 | 계정과목 | 거래처/기사 | 증빙 | 메모

하단: 입금합계 / 출금합계 / 차액
```

**입력 UI 결제수단-증빙 연동:**
```
결제수단 드롭다운 (payment_accounts에서 is_active=true만 표시)
  예: 국민카드 / 신한카드 / 기업은행 주거래 / 농협 예비 / 현금

선택한 결제수단의 type 자동판별:
  type=카드 → 증빙: 카드영수증 (자동고정)
  type=계좌 → 증빙: [세금계산서 / 현금영수증 / 없음]
  type=현금 → 증빙: [세금계산서 / 현금영수증 / 없음]
```

#### 결제수단 관리 (payment_accounts.html)
```
버튼: 추가 / 수정 / 삭제

구분 | 별칭 | 카드/계좌번호 | 은행/카드사 | 명의자 | 사용여부 | 비고

예시:
카드 | 국민카드     | 1234-****-****-5678 | 국민카드 | 차플러스 | ✅
카드 | 신한카드     | 9876-****-****-1234 | 신한카드 | 차플러스 | ✅
계좌 | 주거래       | 123-456-789012       | 기업은행 | 차플러스 | ✅
계좌 | 예비계좌     | 987-654-321098       | 농협     | 차플러스 | ✅
현금 | 현금         | -                    | -        | -        | ✅
```
> 잔액 관리 안함 (단순 결제수단 식별용)  
> 최소 5개 내외, 확장 가능

#### 거래처 원장 (client_ledger.html)
```
거래처 선택 + 기간

☐ | 날짜 | 구분 | 청구금액 | 입금금액 | 잔액(누계)

하단: 청구합계 / 입금합계 / 미수잔액
```

**데이터 소스:**
```
청구: ledger 테이블 (수입 + 해당 거래처)
입금: ledger 테이블 (입금 + 해당 거래처)
잔액: 청구누계 - 입금누계 (행별 실시간)
```

#### 기사 원장 (driver_ledger.html)
```
기사 선택 + 기간

☐ | 날짜 | 구분 | 지급금액 | 출금금액 | 잔액(누계)

하단: 지급합계 / 출금합계 / 미지급잔액
```

#### 지출증빙 (receipt.html)
```
검색: 기간, 증빙유형, 계정과목
버튼: 📄PDF출력

날짜 | 금액 | 수단 | 계정과목 | 증빙유형 | 메모

하단: 합계
```

#### 계정과목 관리 (account_subjects.html)
```
버튼: 추가 / 수정 / 삭제

ID | 계정과목명 | 구분(수입/지출) | 고정여부 | 고정금액
```

#### 설정 (settings.html)
```
회사정보: 상호, 대표자, 주소, 업태, 업종, 연락처, 이메일
견적서 NOTE
청구서 NOTE
백업설정: 백업시간, 구글드라이브 폴더ID
```

---

## 5. API 엔드포인트

### 마스터 데이터
```
GET/POST        /api/vehicles/
GET/PUT/DELETE  /api/vehicles/<id>

GET/POST        /api/clients/
GET/PUT/DELETE  /api/clients/<id>

GET/POST        /api/drivers/
GET/PUT/DELETE  /api/drivers/<id>

GET/POST        /api/account_subjects/
GET/PUT/DELETE  /api/account_subjects/<id>

GET/POST        /api/payment_accounts/
GET/PUT/DELETE  /api/payment_accounts/<id>
```

### 견적
```
GET/POST        /api/quotes/
GET/PUT/DELETE  /api/quotes/<id>
POST            /api/quotes/<id>/confirm   ← 운행확정
POST            /api/quotes/<id>/copy      ← 복사추가
GET             /api/quotes/hint/unit-price?client_id=&vehicle_id=
```

### 운행
```
GET/POST        /api/operations/
GET/PUT/DELETE  /api/operations/<id>
POST            /api/operations/<id>/copy  ← 복사추가
POST/PUT/DELETE /api/operations/<id>/details
GET             /api/operations/details/<id>/message ← 배차메시지
```

### 리포트
```
GET /api/reports/billing?client_id=&from=&to=
GET /api/reports/payment?driver_id=&from=&to=
GET /api/reports/client_ledger?client_id=&from=&to=
GET /api/reports/driver_ledger?driver_id=&from=&to=
```

### 경리
```
GET/POST        /api/ledger/
GET/PUT/DELETE  /api/ledger/<id>
POST            /api/ledger/fixed_monthly  ← 고정지출 생성
```

### PDF
```
GET /pdf/quote/<id>         → 거래처명_견적일_시작일_견적서.pdf
GET /pdf/bill/<id>          → 거래처명_청구일_시작일_청구서.pdf
GET /pdf/payment/<driver_id>?from=&to= → 기사명_기간_지급명세서.pdf
GET /pdf/receipt?from=&to=  → 기간_지출증빙.pdf
```

### 설정
```
GET/POST /api/settings/
POST     /api/backup/now   ← 수동 즉시 백업
```

---

## 6. PDF 출력물

### 6.1 견적서 (A4 가로)
```
헤더: CHAPLUS 로고 + 견적서 제목
      수신(거래처) + 발신(회사정보) + 도장
금액배너: 일금 OOO원정 (₩X,XXX,XXX)
명세표: 날짜/상품/차종/대/인승/포함/지역/지역할증/이용시간/OT/시간할증/숙식/소계
NOTE: 설정에서 입력한 견적서 NOTE
파일명: 거래처명_견적일_운행시작일_견적서.pdf
```

### 6.2 청구서 (A4 가로)
```
헤더: CHAPLUS 로고 + 청구서 제목
      수신(거래처) + 발신(회사정보) + 도장
금액배너: 일금 OOO원정 (₩X,XXX,XXX)
명세표: 날짜/상품/차종/대/인승/포함/지역/지역할증/이용시간/OT/시간할증/숙식/소계
NOTE: 설정에서 입력한 청구서 NOTE
파일명: 거래처명_청구일_운행시작일_청구서.pdf
```

### 6.3 지급명세서 (A4 가로)
```
헤더: CHAPLUS 로고 + 지급명세서 제목
      수신(기사명/구분) + 팀장 + 지급기간

[메인 테이블]
날짜 | 거래처 | 차종 | 기본급 | 추가h | 기사할증 | 경비합계 | 소계
합계행

[경비 상세 - 본인카드만]
날짜 | 거래처 | 유류대 | 통행료 | 주차료 | 식대 | 숙식
(해당 항목 없으면 섹션 생략)

파일명: 기사명_기간_지급명세서.pdf
```

### 6.4 지출증빙 (A4 세로)
```
헤더: CHAPLUS 로고 + 지출증빙 제목 + 기간
명세표: 날짜 | 금액 | 수단 | 계정과목 | 증빙유형 | 메모
합계행
파일명: 기간_지출증빙.pdf
```

**공통 PDF 규칙:**
```
폰트: NanumGothic (fonts/ 폴더 자동탐색)
도장: static/stamp.png (18×18mm, 없으면 [인] 텍스트)
빈 행: 데이터 있는 행만 출력 (빈 행 없음)
면세: vat_type = 면세 → 부가가치세 행 생략
```

---

## 7. 배차 메시지 복사

운행 자식 행의 📋 버튼 클릭 시 클립보드 복사:

```
안녕하세요. 기사포함렌터카 차플러스입니다.
예약확정 안내드립니다.
[날짜+시간], [출발지], [차종], [차번호], [기사명], [기사전화번호]으로
확정 배차하였습니다.
운행시작 10분전까지 출발지에 도착해 대기하며,
운행중이라도 불편한 사항은 언제든지 연락주세요.
차플러스 02-429-0456
```

---

## 8. 구글드라이브 자동 백업

### 구성
```
라이브러리: google-api-python-client, APScheduler
인증파일: credentials/google_credentials.json (서비스 계정)
백업대상: instance/chaplus.db
백업형식: chaplus_20260618_2300.db
보관: 최근 30개 유지 (오래된 파일 자동 삭제)
```

### 설정 항목 (settings 메뉴)
```
백업 실행시간: 매일 23:00 (변경 가능)
구글드라이브 폴더ID: 백업 저장 폴더
```

### 백업 흐름
```
APScheduler (매일 설정시간)
  → chaplus.db 복사
  → 파일명: chaplus_YYYYMMDD_HHMM.db
  → 구글드라이브 업로드
  → 30개 초과 시 가장 오래된 파일 삭제
  → 성공/실패 로그 기록
```

### 수동 백업
```
설정 메뉴 → [지금 백업] 버튼
→ 즉시 실행 후 결과 토스트 알림
```

### 구글드라이브 설정 방법 (README)
```
1. Google Cloud Console에서 프로젝트 생성
2. Google Drive API 활성화
3. 서비스 계정 생성 → JSON 키 다운로드
4. credentials/google_credentials.json 으로 저장
5. 백업 폴더 생성 → 폴더ID 복사 → 설정에 입력
6. 서비스 계정 이메일을 폴더 공유에 추가
```

---

## 9. 사이드바 메뉴 구성

```
📊 대시보드

[영업]
📋 견적관리
🚗 운행관리

[정산]
💰 청구관리
💳 지급관리

[경리]
💵 입출금관리
📒 거래처원장
📒 기사원장
🧾 지출증빙

[마스터]
🚙 차량관리
👤 기사관리
🏢 거래처관리
📂 계정과목
💳 결제수단관리

[시스템]
⚙️ 설정
```

---

## 10. 기술 스택

| 항목 | 기술 | 비고 |
|------|------|------|
| Backend | Flask 3.x | Python |
| DB | SQLite | SQLAlchemy ORM |
| Frontend | HTMX | JS 최소화 |
| CSS | Tailwind CSS | CDN |
| PDF | ReportLab | A4 가로/세로 |
| 폰트 | NanumGothic | fonts/ 폴더 |
| 백업 | Google Drive API | APScheduler |
| 스케줄러 | APScheduler | 매일 자동 백업 |

---

## 11. 개발 순서

```
1단계: 기반
  - models.py (11개 테이블)
  - extensions.py, app.py
  - base.html (Tailwind + HTMX)
  - main.js (최소화)

2단계: 마스터 데이터
  - 차량, 기사, 거래처, 계정과목 CRUD

3단계: 영업
  - 견적관리 (부모+자식, 복사, 확정)
  - 운행관리 (부모+자식, 복사, 메시지)

4단계: 정산
  - 청구관리 (집계)
  - 지급관리 (집계)

5단계: 경리
  - 입출금관리
  - 거래처원장, 기사원장
  - 지출증빙

6단계: PDF
  - 견적서, 청구서
  - 지급명세서
  - 지출증빙

7단계: 백업
  - 구글드라이브 연동
  - APScheduler 설정

8단계: 마무리
  - 대시보드
  - 설정
  - 통합 테스트
```

---

## 12. 알려진 주의사항

```
1. main.js는 반드시 <head>에서 로드 (body 끝에 두면 HTMX 충돌)
2. const/let 대신 var 사용 (템플릿 스코프 이슈)
3. operation_details.run_date 컬럼은 DB Browser로 수동 추가 필요
   (또는 flask db migrate 실행)
4. 차량번호 우선순위: 자차→vehicles.plate_number,
   타사+용역→drivers.plate_number, 타사+대리→직접입력
5. 견적 자식 합계: days=1 고정 (행마다 1일 기준)
6. PDF 빈 행 없음: 데이터 있는 행만 출력
```

---

## 13. 미구현 / 추후 예정

```
[ ] 전자세금계산서 연동 (홈택스 직접 입력 후 번호만 기록)
[ ] 경리장부 잔액 실시간 계산
[ ] 모바일 반응형 (Tailwind로 추후 대응)
[ ] 다중 사업장 (공간클리닉 별도 포트 5001로 구축)
```
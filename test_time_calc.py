"""
시간할증 계산 로직 빠른 검증 스크립트
실행: python test_time_calc.py (venv 활성화 상태)
"""
from services.time_calc_service import calc_extra_time, calc_time_surcharge, calc_driver_time_surcharge, generate_includes

print("=== 1. Full-Day 정확히 10시간 (09:00-19:00) ===")
ftype, extra = calc_extra_time('Full-Day', '09:00', '19:00')
print(f"최종구분={ftype}, 추가시간={extra}h  (기대값: Full-Day, 0)")
assert (ftype, extra) == ('Full-Day', 0)

print("\n=== 2. Full-Day 10시간 29분 (경계값, 09:00-19:29) ===")
ftype, extra = calc_extra_time('Full-Day', '09:00', '19:29')
print(f"최종구분={ftype}, 추가시간={extra}h  (기대값: Full-Day, 0)")
assert (ftype, extra) == ('Full-Day', 0)

print("\n=== 3. Full-Day 10시간 30분 (경계값, 09:00-19:30) ===")
ftype, extra = calc_extra_time('Full-Day', '09:00', '19:30')
print(f"최종구분={ftype}, 추가시간={extra}h  (기대값: Full-Day, 1)")
assert (ftype, extra) == ('Full-Day', 1)

print("\n=== 4. Full-Day 자정넘어 (10:00-25:00 = 다음날 01:00) ===")
ftype, extra = calc_extra_time('Full-Day', '10:00', '25:00')
print(f"최종구분={ftype}, 추가시간={extra}h  (기대값: Full-Day, 5)")
assert (ftype, extra) == ('Full-Day', 5)

print("\n=== 5. Half-Day 4시간 (09:00-13:00) - 전환 안됨 ===")
ftype, extra = calc_extra_time('Half-Day', '09:00', '13:00')
print(f"최종구분={ftype}, 추가시간={extra}h  (기대값: Half-Day, 0)")
assert (ftype, extra) == ('Half-Day', 0)

print("\n=== 6. Half-Day 5시간30분 (09:00-14:30) - Full-Day 자동전환 ===")
ftype, extra = calc_extra_time('Half-Day', '09:00', '14:30')
print(f"최종구분={ftype}, 추가시간={extra}h  (기대값: Full-Day, 0)")
assert (ftype, extra) == ('Full-Day', 0)

print("\n=== 7. DropOff - 추가시간 없음 ===")
ftype, extra = calc_extra_time('DropOff', '09:00', '11:00')
print(f"최종구분={ftype}, 추가시간={extra}h  (기대값: DropOff, 0)")
assert (ftype, extra) == ('DropOff', 0)

print("\n=== 8. 시간할증 금액 계산 (단가 200,000 / 추가 5시간) ===")
surcharge = calc_time_surcharge(200000, 5)
print(f"청구 시간할증={surcharge}원  (기대값: 100,000)")
assert surcharge == 100000

print("\n=== 9. 기사 시간할증 (OT단가 15,000 / 기사추가 5시간) ===")
d_surcharge = calc_driver_time_surcharge(15000, 5)
print(f"기사 시간할증={d_surcharge}원  (기대값: 75,000)")
assert d_surcharge == 75000

print("\n=== 10. 포함내역 자동생성 ===")
for pt in ('Full-Day', 'Half-Day', 'DropOff', 'PickUp'):
    print(f"{pt} → {generate_includes(pt)}")

print("\n✅ 모든 테스트 통과!")

import math

HALF_DAY_CONVERT_THRESHOLD_MIN = 330   # 5시간30분 → Full-Day 자동전환 기준
FULL_DAY_BASE_MIN = 600                # 10시간


def parse_time_to_minutes(time_str):
    """'HH:MM' 형식. HH는 24 이상도 허용 (예: '25:00' = 다음날 01:00, 30분 단위 가정)"""
    h, m = time_str.split(':')
    return int(h) * 60 + int(m)


def calc_duration_minutes(start_time, end_time):
    """
    start_time, end_time: 'HH:MM' 문자열
    end가 start보다 작은 시각이면 다음날로 간주하여 24시간을 더함
    (단, end_time이 25:00처럼 이미 24+ 표기면 그대로 계산됨)
    """
    start_min = parse_time_to_minutes(start_time)
    end_min = parse_time_to_minutes(end_time)
    if end_min < start_min:
        end_min += 24 * 60
    return end_min - start_min


def calc_extra_time(product_type, start_time, end_time):
    """
    상품구분 + 시작/종료시간으로 (최종 상품구분, 추가시간[시간단위]) 반환

    - DropOff / PickUp        : 추가시간 없음
    - Half-Day (5시간 기준)    : 운행시간이 330분 이상이면 Full-Day로 자동전환
    - Full-Day (10시간 기준)   : over_min = 총운행분 - 600
                                 over_min <= 29  → extra_time = 0
                                 over_min >= 30  → extra_time = ceil(over_min / 60)
    """
    if product_type in ('DropOff', 'PickUp'):
        return product_type, 0

    if not start_time or not end_time:
        return product_type, 0

    duration = calc_duration_minutes(start_time, end_time)

    final_type = product_type
    if product_type == 'Half-Day' and duration >= HALF_DAY_CONVERT_THRESHOLD_MIN:
        final_type = 'Full-Day'

    if final_type == 'Full-Day':
        over_min = duration - FULL_DAY_BASE_MIN
        extra_time = 0 if over_min <= 29 else math.ceil(over_min / 60)
    else:
        # Half-Day 그대로 유지된 경우 추가시간 없음
        extra_time = 0

    return final_type, extra_time


def calc_time_surcharge(unit_price, extra_time):
    """청구 시간할증 = 단가 / 10 × 추가시간"""
    return round((unit_price or 0) / 10) * (extra_time or 0)


def calc_driver_time_surcharge(ot_pay, driver_extra_time):
    """기사 시간할증 = ot_pay × 기사추가시간"""
    return (ot_pay or 0) * (driver_extra_time or 0)


def generate_includes(product_type):
    """포함내역 자동생성"""
    mapping = {
        'Full-Day': '서울/기사/10시간/유류비',
        'Half-Day': '서울/기사/5시간/유류비',
        'DropOff': '서울/기사/유류비',
        'PickUp': '서울/기사/유류비',
    }
    return mapping.get(product_type, '')

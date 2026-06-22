from datetime import datetime
from extensions import db


def generate_id(prefix, model, id_field='id'):
    """
    ID 자동생성: PREFIX + 연도2자리 + 순번3자리
    예: V26001, C26001, Q26001, QD26001 ...
    연도가 바뀌면 순번이 001부터 자동 리셋됨 (prefix+YY 패턴으로 검색하기 때문)

    prefix   : 'V', 'C', 'D', 'Q', 'QD', 'O', 'OD', 'L', 'PA' 등
    model    : SQLAlchemy 모델 클래스 (예: Vehicle)
    id_field : PK 컬럼명 (기본 'id')
    """
    yy = datetime.now().strftime('%y')
    pattern = f"{prefix}{yy}"

    column = getattr(model, id_field)
    last = (
        db.session.query(model)
        .filter(column.like(f"{pattern}%"))
        .order_by(column.desc())
        .first()
    )

    if last:
        last_id = getattr(last, id_field)
        last_seq = int(last_id[len(pattern):])
        new_seq = last_seq + 1
    else:
        new_seq = 1

    return f"{pattern}{new_seq:03d}"

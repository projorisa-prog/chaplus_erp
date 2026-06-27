from flask import Blueprint, render_template, request, jsonify
from extensions import db
from models import Settings

settings_bp = Blueprint('settings', __name__)

SETTING_KEYS = [
    ('company_name',       '회사명',              '차플러스'),
    ('ceo_name',           '대표자',              ''),
    ('business_no',        '사업자번호',           ''),
    ('address',            '주소',                ''),
    ('phone',              '전화번호',             ''),
    ('email',              '이메일',              ''),
    ('bank_name',          '입금계좌 은행',         ''),
    ('bank_account',       '입금계좌 번호',         ''),
    ('bank_holder',        '예금주',              ''),
    ('fullday_base_hours', 'Full-Day 기준시간(분)', '600'),
    ('halfday_threshold',  'Half-Day 전환기준(분)', '330'),
    ('default_vat_type',   '기본 부가세구분',       '별도'),
]


@settings_bp.route('/settings')
def settings_page():
    rows = {s.key: s.value for s in Settings.query.all()}
    return render_template('settings.html', keys=SETTING_KEYS, rows=rows)


@settings_bp.route('/api/settings', methods=['POST'])
def settings_save():
    for key, _, _ in SETTING_KEYS:
        val = request.form.get(key, '')
        s = Settings.query.get(key)
        if s:
            s.value = val
        else:
            db.session.add(Settings(key=key, value=val))
    db.session.commit()
    rows = {s.key: s.value for s in Settings.query.all()}
    return render_template('_settings_form.html', keys=SETTING_KEYS, rows=rows,
                           saved=True)


@settings_bp.route('/api/settings/<key>')
def setting_get(key):
    s = Settings.query.get(key)
    return jsonify({'value': s.value if s else ''})

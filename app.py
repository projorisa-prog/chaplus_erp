import os
from flask import Flask, render_template
from dotenv import load_dotenv

from extensions import db, migrate, cors

load_dotenv()


def create_app():
    app = Flask(__name__)

    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_dir = os.path.join(basedir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        'sqlite:///' + os.path.join(instance_dir, 'chaplus.db')
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    # models.py를 반드시 import 해야 flask db migrate 가 테이블을 인식함
    import models  # noqa: F401

    from routes.vehicles import vehicles_bp
    app.register_blueprint(vehicles_bp)

    from routes.drivers import drivers_bp
    app.register_blueprint(drivers_bp)

    from routes.clients import clients_bp
    app.register_blueprint(clients_bp)

    from routes.quotes import quotes_bp
    app.register_blueprint(quotes_bp)

    from routes.operations import operations_bp
    app.register_blueprint(operations_bp)

    from routes.billing import billing_bp
    app.register_blueprint(billing_bp)

    from routes.payment import payment_bp
    app.register_blueprint(payment_bp)

    from routes.ledger import ledger_bp
    app.register_blueprint(ledger_bp)

    from routes.account_subjects import account_subjects_bp
    app.register_blueprint(account_subjects_bp)

    from routes.payment_accounts import payment_accounts_bp
    app.register_blueprint(payment_accounts_bp)

    from routes.client_ledger import client_ledger_bp
    app.register_blueprint(client_ledger_bp)

    from routes.driver_ledger import driver_ledger_bp
    app.register_blueprint(driver_ledger_bp)

    from routes.receipt import receipt_bp
    app.register_blueprint(receipt_bp)

    from routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from routes.settings import settings_bp
    app.register_blueprint(settings_bp)

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)

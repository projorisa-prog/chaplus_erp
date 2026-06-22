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

    @app.route('/')
    def index():
        return render_template('index.html')

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)

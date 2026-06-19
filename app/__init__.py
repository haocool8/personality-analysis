from flask import Flask
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from app.routes.main import main_bp
    from app.routes.assessment import assessment_bp
    from app.routes.report import report_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(assessment_bp, url_prefix="/assessment")
    app.register_blueprint(report_bp, url_prefix="/report")

    return app

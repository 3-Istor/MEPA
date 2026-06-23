from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config, PROJECT_ROOT
from .db import init_app as init_db_app
from .routes import bp
from .security import add_security_headers, csrf_protect


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "templates"),
        static_folder=str(PROJECT_ROOT / "static"),
    )
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    if app.config.get("TRUST_PROXY"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    init_db_app(app)
    app.before_request(csrf_protect)
    app.after_request(add_security_headers)
    app.register_blueprint(bp)

    if not app.testing and app.config["SECRET_KEY"] == "dev-only-change-before-deploy":
        app.logger.warning("SECRET_KEY utilise la valeur de développement. Changez-la avant tout déploiement.")
    return app

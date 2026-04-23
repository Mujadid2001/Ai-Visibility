"""Flask application factory."""
import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name: str = None) -> Flask:
    """Create and configure Flask application.
    
    Args:
        config_name: Configuration environment (development, testing, production)
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Configuration
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
    
    # Load config from environment
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///dev.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_SORT_KEYS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-key-change-in-production")
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import and register models
    from app.models import profile, query, recommendation, pipeline_run
    
    # Register blueprints
    from app.api import profiles_bp, queries_bp
    app.register_blueprint(profiles_bp.bp)
    app.register_blueprint(queries_bp.bp)
    
    # Setup logging
    if not app.debug and not app.testing:
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            "logs/api.log", maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
    
    # Context processor to make db available in shell
    @app.shell_context_processor
    def make_shell_context():
        return {"db": db}
    
    # Register CLI commands
    from app.cli import register_cli
    register_cli(app)
    
    # Health check endpoint
    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok"}, 200
    
    return app

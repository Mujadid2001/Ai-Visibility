"""API package."""
from app.api.profiles import bp as profiles_bp
from app.api.queries import bp as queries_bp

__all__ = ["profiles_bp", "queries_bp"]

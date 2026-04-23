"""Query API endpoints."""
import logging
from flask import Blueprint, jsonify
from app import db
from app.models import DiscoveredQuery
from app.services.pipeline import PipelineOrchestrator

logger = logging.getLogger(__name__)
bp = Blueprint("queries", __name__, url_prefix="/api/v1/queries")


@bp.route("/<query_uuid>/recheck", methods=["POST"])
def recheck_query(query_uuid: str):
    """Re-run visibility scoring on a single query."""
    try:
        query = DiscoveredQuery.query.filter_by(uuid=query_uuid).first()
        if not query:
            return {"error": f"Query {query_uuid} not found"}, 404
        
        logger.info(f"Rechecking query {query_uuid}")
        orchestrator = PipelineOrchestrator()
        result = orchestrator.recheck_query(query_uuid)
        
        if "error" in result:
            return result, 500
        
        return result, 200
    
    except Exception as e:
        logger.error(f"Error rechecking query: {e}")
        return {"error": str(e)}, 500

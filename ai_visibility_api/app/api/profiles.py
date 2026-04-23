"""Business profile API endpoints."""
import logging
from flask import Blueprint, request, jsonify
from app import db
from app.models import BusinessProfile, PipelineRun, DiscoveredQuery, ContentRecommendation
from app.services.pipeline import PipelineOrchestrator

logger = logging.getLogger(__name__)
bp = Blueprint("profiles", __name__, url_prefix="/api/v1/profiles")


@bp.route("", methods=["POST"])
def create_profile():
    """Register a new business profile."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ["name", "domain", "industry"]
        if not all(f in data for f in required):
            return {
                "error": f"Missing required fields: {', '.join(required)}"
            }, 400
        
        # Check if domain already exists
        if BusinessProfile.query.filter_by(domain=data["domain"]).first():
            return {"error": "Domain already registered"}, 409
        
        # Create profile
        profile = BusinessProfile(
            name=data["name"],
            domain=data["domain"],
            industry=data["industry"],
            description=data.get("description"),
            competitors=data.get("competitors", []),
            status="created",
        )
        
        db.session.add(profile)
        db.session.commit()
        
        logger.info(f"Created profile {profile.uuid} for {profile.domain}")
        
        return profile.to_dict(), 201
    
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        return {"error": str(e)}, 500


@bp.route("/<profile_uuid>", methods=["GET"])
def get_profile(profile_uuid: str):
    """Retrieve a profile and its summary stats."""
    try:
        profile = BusinessProfile.query.filter_by(uuid=profile_uuid).first()
        if not profile:
            return {"error": f"Profile {profile_uuid} not found"}, 404
        
        return profile.to_dict_with_stats(), 200
    
    except Exception as e:
        logger.error(f"Error retrieving profile: {e}")
        return {"error": str(e)}, 500


@bp.route("/<profile_uuid>/run", methods=["POST"])
def trigger_pipeline(profile_uuid: str):
    """Trigger the full 3-agent pipeline for a profile."""
    try:
        profile = BusinessProfile.query.filter_by(uuid=profile_uuid).first()
        if not profile:
            return {"error": f"Profile {profile_uuid} not found"}, 404
        
        # Check if pipeline is already running
        running_run = PipelineRun.query.filter_by(
            profile_uuid=profile_uuid,
            status="running"
        ).first()
        
        if running_run:
            return {
                "error": "Pipeline already running for this profile",
                "run_uuid": running_run.uuid,
            }, 409
        
        # Run pipeline
        logger.info(f"Triggering pipeline for profile {profile_uuid}")
        orchestrator = PipelineOrchestrator()
        result = orchestrator.run_pipeline(profile_uuid)
        
        if result.get("status") == "failed":
            return result, 500
        
        return result, 200
    
    except Exception as e:
        logger.error(f"Error triggering pipeline: {e}")
        return {"error": str(e)}, 500


@bp.route("/<profile_uuid>/queries", methods=["GET"])
def get_profile_queries(profile_uuid: str):
    """Get all queries for a profile with filtering and pagination."""
    try:
        profile = BusinessProfile.query.filter_by(uuid=profile_uuid).first()
        if not profile:
            return {"error": f"Profile {profile_uuid} not found"}, 404
        
        # Get filters
        min_score = request.args.get("min_score", type=float, default=0.0)
        status_filter = request.args.get("status")  # visible, not_visible, unknown
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        
        # Build query
        query = DiscoveredQuery.query.filter_by(profile_uuid=profile_uuid)
        
        # Apply filters
        if min_score > 0:
            query = query.filter(DiscoveredQuery.opportunity_score >= min_score)
        
        if status_filter == "visible":
            query = query.filter(DiscoveredQuery.domain_visible == True)
        elif status_filter == "not_visible":
            query = query.filter(DiscoveredQuery.domain_visible == False)
        
        # Sort by opportunity score descending
        query = query.order_by(DiscoveredQuery.opportunity_score.desc())
        
        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            "queries": [q.to_dict() for q in paginated.items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": paginated.total,
                "pages": paginated.pages,
            },
        }, 200
    
    except Exception as e:
        logger.error(f"Error retrieving queries: {e}")
        return {"error": str(e)}, 500


@bp.route("/<profile_uuid>/recommendations", methods=["GET"])
def get_profile_recommendations(profile_uuid: str):
    """Get content recommendations for a profile."""
    try:
        profile = BusinessProfile.query.filter_by(uuid=profile_uuid).first()
        if not profile:
            return {"error": f"Profile {profile_uuid} not found"}, 404
        
        # Get recommendations for this profile, sorted by priority
        priority_order = {"high": 1, "medium": 2, "low": 3}
        recommendations = ContentRecommendation.query.filter_by(
            profile_uuid=profile_uuid
        ).all()
        
        recommendations.sort(
            key=lambda r: (priority_order.get(r.priority, 4), -r.created_at.timestamp())
        )
        
        return {
            "recommendations": [r.to_dict() for r in recommendations],
            "total": len(recommendations),
        }, 200
    
    except Exception as e:
        logger.error(f"Error retrieving recommendations: {e}")
        return {"error": str(e)}, 500

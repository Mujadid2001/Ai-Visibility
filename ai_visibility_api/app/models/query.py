"""Discovered query model."""
import uuid
from datetime import datetime
from app import db


class DiscoveredQuery(db.Model):
    """Represents a query discovered by Agent 1 and scored by Agent 2."""
    
    __tablename__ = "discovered_queries"
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    profile_uuid = db.Column(db.String(36), db.ForeignKey("business_profiles.uuid"), nullable=False)
    run_uuid = db.Column(db.String(36), db.ForeignKey("pipeline_runs.uuid"), nullable=False)
    query_text = db.Column(db.Text, nullable=False)
    estimated_search_volume = db.Column(db.Integer, nullable=True, default=0)
    competitive_difficulty = db.Column(db.Integer, nullable=True, default=50)  # 0-100
    opportunity_score = db.Column(db.Float, nullable=True, default=0.0)  # 0.0-1.0
    domain_visible = db.Column(db.Boolean, nullable=True, default=False)
    visibility_position = db.Column(db.Integer, nullable=True)  # Position in AI answer if visible
    discovered_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    profile = db.relationship("BusinessProfile", back_populates="queries")
    run = db.relationship("PipelineRun", back_populates="queries")
    recommendations = db.relationship("ContentRecommendation", back_populates="query", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert model to dictionary."""
        result = {
            "query_uuid": self.uuid,
            "query_text": self.query_text,
            "estimated_search_volume": self.estimated_search_volume,
            "competitive_difficulty": self.competitive_difficulty,
            "opportunity_score": round(self.opportunity_score, 3) if self.opportunity_score else 0.0,
            "domain_visible": self.domain_visible,
            "visibility_position": self.visibility_position,
            "discovered_at": self.discovered_at.isoformat() + "Z",
        }
        return result

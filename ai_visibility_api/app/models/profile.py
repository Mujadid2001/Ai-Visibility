"""Business profile model."""
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from app import db


class BusinessProfile(db.Model):
    """Represents a business profile for which to track AI visibility."""
    
    __tablename__ = "business_profiles"
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(255), nullable=False, unique=True)
    industry = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    competitors = db.Column(db.JSON, nullable=False, default=list)  # List of competitor domains
    status = db.Column(db.String(50), nullable=False, default="created")  # created, active, archived
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pipeline_runs = db.relationship("PipelineRun", back_populates="profile", cascade="all, delete-orphan")
    queries = db.relationship("DiscoveredQuery", back_populates="profile", cascade="all, delete-orphan")
    recommendations = db.relationship("ContentRecommendation", back_populates="profile", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "profile_uuid": self.uuid,
            "name": self.name,
            "domain": self.domain,
            "industry": self.industry,
            "description": self.description,
            "competitors": self.competitors,
            "status": self.status,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
        }
    
    def to_dict_with_stats(self):
        """Convert model to dictionary with summary stats."""
        result = self.to_dict()
        result["total_queries_discovered"] = len(self.queries)
        result["total_recommendations"] = len(self.recommendations)
        if self.queries:
            avg_score = sum(q.opportunity_score for q in self.queries) / len(self.queries)
            result["avg_opportunity_score"] = round(avg_score, 3)
        else:
            result["avg_opportunity_score"] = 0.0
        return result

"""Pipeline run model."""
import uuid
from datetime import datetime
from app import db


class PipelineRun(db.Model):
    """Represents a single run of the 3-agent pipeline."""
    
    __tablename__ = "pipeline_runs"
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    profile_uuid = db.Column(db.String(36), db.ForeignKey("business_profiles.uuid"), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="pending")  # pending, running, completed, failed
    queries_discovered = db.Column(db.Integer, default=0)
    queries_scored = db.Column(db.Integer, default=0)
    tokens_used = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    profile = db.relationship("BusinessProfile", back_populates="pipeline_runs")
    queries = db.relationship("DiscoveredQuery", back_populates="run", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert model to dictionary."""
        result = {
            "run_uuid": self.uuid,
            "profile_uuid": self.profile_uuid,
            "status": self.status,
            "queries_discovered": self.queries_discovered,
            "queries_scored": self.queries_scored,
            "started_at": self.started_at.isoformat() + "Z",
        }
        if self.completed_at:
            result["completed_at"] = self.completed_at.isoformat() + "Z"
        if self.tokens_used:
            result["tokens_used"] = self.tokens_used
        if self.error_message:
            result["error_message"] = self.error_message
        return result

"""Integration test for API endpoints."""
import pytest
from app import create_app, db
from app.models import BusinessProfile


@pytest.fixture
def client():
    """Create test client with in-memory database."""
    app = create_app("testing")
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


class TestProfileEndpoints:
    """Test profile management endpoints."""
    
    def test_create_profile(self, client):
        """Test creating a new profile."""
        response = client.post(
            "/api/v1/profiles",
            json={
                "name": "Test Company",
                "domain": "test.com",
                "industry": "SaaS",
                "description": "A test company",
                "competitors": ["comp1.com", "comp2.com"],
            },
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Test Company"
        assert data["domain"] == "test.com"
        assert "profile_uuid" in data
    
    def test_create_profile_missing_required_field(self, client):
        """Test creating profile without required field."""
        response = client.post(
            "/api/v1/profiles",
            json={
                "name": "Test Company",
                # Missing 'domain' and 'industry'
            },
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
    
    def test_get_profile(self, client):
        """Test retrieving a profile."""
        # Create profile first
        create_response = client.post(
            "/api/v1/profiles",
            json={
                "name": "Test Company",
                "domain": "test.com",
                "industry": "SaaS",
            },
        )
        profile_uuid = create_response.get_json()["profile_uuid"]
        
        # Get profile
        get_response = client.get(f"/api/v1/profiles/{profile_uuid}")
        
        assert get_response.status_code == 200
        data = get_response.get_json()
        assert data["name"] == "Test Company"
        assert data["profile_uuid"] == profile_uuid
        assert "total_queries_discovered" in data
        assert "avg_opportunity_score" in data
    
    def test_get_nonexistent_profile(self, client):
        """Test retrieving a nonexistent profile."""
        response = client.get("/api/v1/profiles/nonexistent-uuid")
        
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

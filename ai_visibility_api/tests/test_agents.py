"""Tests for AI agents."""
import pytest
from unittest.mock import patch, MagicMock
from app.agents.discovery import QueryDiscoveryAgent
from app.agents.scoring import VisibilityScoringAgent
from app.agents.recommendation import ContentRecommendationAgent
from app.utils.scoring import calculate_opportunity_score


class TestQueryDiscoveryAgent:
    """Test the Query Discovery Agent."""
    
    @patch('app.agents.base.BaseAgent.call_llm')
    def test_discovery_returns_valid_queries(self, mock_call_llm):
        """Test that discovery agent returns valid query list."""
        mock_call_llm.return_value = '''
        {
            "queries": [
                {"query": "What is the best SEO tool?", "intent": "best_of"},
                {"query": "How does Surfer SEO compare to Clearscope?", "intent": "comparison"}
            ]
        }
        '''
        
        agent = QueryDiscoveryAgent(provider="openai")
        result = agent.run({
            "name": "Test Business",
            "domain": "test.com",
            "industry": "SEO",
            "description": "Test",
            "competitors": ["comp1.com"],
        })
        
        assert "queries" in result
        assert len(result["queries"]) == 2
        assert result["queries"][0]["query_text"] == "What is the best SEO tool?"
    
    @patch('app.agents.base.BaseAgent.call_llm')
    def test_discovery_handles_malformed_json(self, mock_call_llm):
        """Test that discovery agent handles malformed JSON."""
        mock_call_llm.return_value = "```json\n{\"queries\": []}\n```"
        
        agent = QueryDiscoveryAgent(provider="openai")
        result = agent.run({
            "name": "Test",
            "domain": "test.com",
            "industry": "SEO",
            "description": "",
            "competitors": [],
        })
        
        assert "queries" in result
        assert isinstance(result["queries"], list)


class TestVisibilityScoringAgent:
    """Test the Visibility Scoring Agent."""
    
    @patch('app.agents.base.BaseAgent.call_llm')
    def test_scoring_returns_valid_scores(self, mock_call_llm):
        """Test that scoring agent returns valid score data."""
        mock_call_llm.return_value = '''
        {
            "estimated_search_volume": 1500,
            "competitive_difficulty": 65,
            "domain_would_appear": true,
            "visibility_position": 2,
            "reasoning": "High relevance"
        }
        '''
        
        agent = VisibilityScoringAgent(provider="openai")
        result = agent.run(
            query_text="best SEO tool",
            target_domain="test.com",
            industry="SEO",
            competitors=["comp1.com"]
        )
        
        assert result["estimated_search_volume"] == 1500
        assert result["competitive_difficulty"] == 65
        assert result["domain_would_appear"] is True
    
    @patch('app.agents.base.BaseAgent.call_llm')
    def test_scoring_normalizes_values(self, mock_call_llm):
        """Test that scoring agent normalizes out-of-range values."""
        mock_call_llm.return_value = '''
        {
            "estimated_search_volume": 5000,
            "competitive_difficulty": 150,
            "domain_would_appear": false,
            "visibility_position": null
        }
        '''
        
        agent = VisibilityScoringAgent(provider="openai")
        result = agent.run(
            query_text="test query",
            target_domain="test.com",
            industry="SEO",
            competitors=[]
        )
        
        # Difficulty should be capped at 100
        assert result["competitive_difficulty"] == 100


class TestContentRecommendationAgent:
    """Test the Content Recommendation Agent."""
    
    @patch('app.agents.base.BaseAgent.call_llm')
    def test_recommendation_returns_valid_recommendations(self, mock_call_llm):
        """Test that recommendation agent returns valid recommendations."""
        mock_call_llm.return_value = '''
        {
            "recommendations": [
                {
                    "content_type": "blog_post",
                    "title": "The Ultimate Guide to SEO",
                    "rationale": "Covers the query comprehensively",
                    "target_keywords": ["seo", "content optimization"],
                    "priority": "high"
                }
            ]
        }
        '''
        
        agent = ContentRecommendationAgent(provider="openai")
        result = agent.run(
            query_text="how to do seo",
            target_domain="test.com",
            industry="SEO",
            profile_name="Test"
        )
        
        assert "recommendations" in result
        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0]["content_type"] == "blog_post"
    
    @patch('app.agents.base.BaseAgent.call_llm')
    def test_recommendation_handles_missing_fields(self, mock_call_llm):
        """Test that recommendation agent handles incomplete recommendations."""
        mock_call_llm.return_value = '''
        {
            "recommendations": [
                {
                    "content_type": "blog_post",
                    "title": "Guide"
                }
            ]
        }
        '''
        
        agent = ContentRecommendationAgent(provider="openai")
        result = agent.run(
            query_text="test",
            target_domain="test.com",
            industry="SEO"
        )
        
        # Should filter out incomplete recommendations
        assert "recommendations" in result


class TestOpportunityScoring:
    """Test the opportunity score calculation."""
    
    def test_score_increases_with_volume(self):
        """Test that score increases with search volume."""
        low_volume = calculate_opportunity_score(100, 50, False, "other")
        high_volume = calculate_opportunity_score(5000, 50, False, "other")
        
        assert high_volume > low_volume
    
    def test_score_decreases_with_difficulty(self):
        """Test that score decreases with competitive difficulty."""
        easy = calculate_opportunity_score(1000, 30, False, "other")
        hard = calculate_opportunity_score(1000, 80, False, "other")
        
        assert easy > hard
    
    def test_score_higher_when_not_visible(self):
        """Test that score is higher when domain is not visible."""
        visible = calculate_opportunity_score(1000, 50, True, "other")
        not_visible = calculate_opportunity_score(1000, 50, False, "other")
        
        assert not_visible > visible
    
    def test_commercial_intent_increases_score(self):
        """Test that commercial intents have higher scores."""
        comparison_score = calculate_opportunity_score(1000, 50, False, "comparison")
        info_score = calculate_opportunity_score(1000, 50, False, "how_to")
        
        assert comparison_score > info_score
    
    def test_score_in_valid_range(self):
        """Test that scores are always between 0 and 1."""
        scores = [
            calculate_opportunity_score(100, 10, True, "best_of"),
            calculate_opportunity_score(10000, 100, False, "comparison"),
            calculate_opportunity_score(0, 0, False, "best_of"),
            calculate_opportunity_score(5000, 50, True, "other"),
        ]
        
        for score in scores:
            assert 0.0 <= score <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

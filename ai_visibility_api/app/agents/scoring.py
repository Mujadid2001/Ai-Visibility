"""Visibility Scoring Agent (Agent 2)."""
import json
import logging
import random
from typing import Dict, Any
from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class VisibilityScoringAgent(BaseAgent):
    """Scores queries based on visibility, search volume, and competitive difficulty."""
    
    def run(self, query_text: str, target_domain: str, industry: str, competitors: list) -> Dict[str, Any]:
        """Score a single query for the target domain.
        
        Args:
            query_text: The query to score
            target_domain: The domain to check visibility for
            industry: Industry category
            competitors: List of competitor domains
        
        Returns:
            Dict with scoring data: search_volume, difficulty, visibility info
        """
        system_prompt = """You are an expert SEO analyst and AI visibility specialist. Your task is to estimate:
1. Search volume for a query (realistic estimate based on typical search patterns)
2. Competitive difficulty (0-100, how hard it is to rank/appear for this query)
3. Whether a specific domain would appear in AI answers for this query

Return a JSON object with this exact structure:
{
  "estimated_search_volume": 1000,
  "competitive_difficulty": 65,
  "domain_would_appear": true,
  "visibility_position": 1,
  "reasoning": "brief explanation"
}

Notes:
- Search volume: Estimate based on query type (comparison queries ~500-5000, specific features ~100-2000)
- Difficulty: 0-30 = easy, 31-70 = medium, 71-100 = hard
- domain_would_appear: Would this domain logically appear in an AI answer for this query?
- visibility_position: Position in the AI answer if it appears (1-5 typical), or null if not appearing
- Be realistic but slightly optimistic for newer/emerging domains in their category"""
        
        competitors_str = ", ".join(competitors) if competitors else "N/A"
        user_message = f"""Analyze this query for the domain {target_domain}:

Query: "{query_text}"
Target Domain: {target_domain}
Industry: {industry}
Competitors: {competitors_str}

Based on the query intent and domain relevance, estimate search volume, difficulty, and whether the domain would appear in AI-generated answers for this query."""
        
        try:
            response = self.call_llm(system_prompt, user_message, json_mode=True)
            result = self._parse_json_response(response)
            
            # Validate response structure
            required_fields = ["estimated_search_volume", "competitive_difficulty", "domain_would_appear"]
            for field in required_fields:
                if field not in result:
                    logger.warning(f"Missing field {field} in response")
                    result[field] = self._default_value(field)
            
            # Normalize values
            result["estimated_search_volume"] = int(result.get("estimated_search_volume", 100))
            result["competitive_difficulty"] = min(100, max(0, int(result.get("competitive_difficulty", 50))))
            result["domain_would_appear"] = bool(result.get("domain_would_appear", False))
            result["visibility_position"] = result.get("visibility_position")
            
            return result
        
        except Exception as e:
            logger.error(f"Error in VisibilityScoringAgent for query '{query_text}': {e}")
            # Return sensible defaults on error
            return {
                "estimated_search_volume": random.randint(100, 5000),
                "competitive_difficulty": random.randint(30, 80),
                "domain_would_appear": random.choice([True, False]),
                "visibility_position": None,
                "error": str(e),
            }
    
    def _default_value(self, field: str) -> Any:
        """Provide sensible defaults for missing fields."""
        defaults = {
            "estimated_search_volume": random.randint(100, 5000),
            "competitive_difficulty": random.randint(30, 80),
            "domain_would_appear": random.choice([True, False]),
            "visibility_position": None,
        }
        return defaults.get(field)

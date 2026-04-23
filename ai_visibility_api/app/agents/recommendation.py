"""Content Recommendation Agent (Agent 3)."""
import json
import logging
from typing import List, Dict, Any
from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class ContentRecommendationAgent(BaseAgent):
    """Generates actionable content recommendations for high-opportunity queries."""
    
    def run(self, query_text: str, target_domain: str, industry: str, profile_name: str = None) -> Dict[str, Any]:
        """Generate content recommendations for a query where domain is not visible.
        
        Args:
            query_text: The query to generate recommendations for
            target_domain: The domain for which to recommend content
            industry: Industry category
            profile_name: Name of the business profile (optional)
        
        Returns:
            Dict with 'recommendations' key containing list of recommendations
        """
        system_prompt = """You are an expert content strategist and SEO content specialist. Your task is to generate specific, actionable content recommendations that will help a domain appear in AI-generated answers for a given query.

Each recommendation should:
- Be highly specific and actionable
- Suggest realistic content (blog post, landing page, guide, FAQ, comparison, case study)
- Include 3-5 target keywords that should be covered
- Explain WHY this content addresses the query gap
- Be prioritized as high/medium/low based on impact and effort

Return a JSON object with this exact structure:
{
  "recommendations": [
    {
      "content_type": "blog_post|landing_page|guide|faq|comparison|case_study",
      "title": "Suggested content title",
      "rationale": "Why this content will help appear for the query",
      "target_keywords": ["keyword1", "keyword2", "keyword3"],
      "priority": "high|medium|low"
    }
  ]
}

Generate 3-5 diverse recommendations. Prioritize high-impact content that directly addresses the query intent."""
        
        profile_name_str = f" ({profile_name})" if profile_name else ""
        user_message = f"""Generate content recommendations for this domain to capture a high-opportunity query.

Query: "{query_text}"
Target Domain: {target_domain}{profile_name_str}
Industry: {industry}

This domain is NOT currently appearing in AI answers for this query. What content should be created to improve visibility?

Focus on:
1. Content that directly answers the user's question
2. Content that establishes authority and relevance
3. Content optimized for the specific query intent
4. Content that other AI visibility leaders might create"""
        
        try:
            response = self.call_llm(system_prompt, user_message, json_mode=True)
            result = self._parse_json_response(response)
            
            # Validate response structure
            if not isinstance(result, dict) or "recommendations" not in result:
                logger.warning(f"Unexpected response structure: {result}")
                return {"recommendations": []}
            
            recommendations = result.get("recommendations", [])
            if not isinstance(recommendations, list):
                logger.warning(f"Recommendations not a list: {type(recommendations)}")
                return {"recommendations": []}
            
            # Validate each recommendation
            validated = []
            for rec in recommendations:
                if isinstance(rec, dict) and all(k in rec for k in ["content_type", "title", "rationale"]):
                    validated.append({
                        "content_type": rec.get("content_type", "blog_post"),
                        "title": rec.get("title", "").strip(),
                        "rationale": rec.get("rationale", "").strip(),
                        "target_keywords": rec.get("target_keywords", [])[:5],  # Limit to 5
                        "priority": rec.get("priority", "medium"),
                    })
            
            return {"recommendations": validated}
        
        except Exception as e:
            logger.error(f"Error in ContentRecommendationAgent for query '{query_text}': {e}")
            return {"recommendations": [], "error": str(e)}

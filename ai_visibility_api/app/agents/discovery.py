"""Query Discovery Agent (Agent 1)."""
import json
import logging
from typing import List, Dict, Any
from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class QueryDiscoveryAgent(BaseAgent):
    """Discovers high-value queries for a business in its competitive space."""
    
    def run(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Discover queries for the given business profile.
        
        Args:
            profile_data: Dict with keys: domain, industry, description, competitors
        
        Returns:
            Dict with 'queries' key containing list of discovered queries
        """
        system_prompt = """You are an expert AI visibility researcher and SEO strategist. Your task is to discover realistic, commercially-relevant questions that users ask AI assistants (like ChatGPT, Claude, Perplexity) when searching for products or services in a specific industry.

Focus on:
- Comparison queries ("X vs Y", "Which is better")
- Best-of queries ("best tool for", "top SEO tools")
- How-to and educational queries that relate to the product category
- Problem-solution queries ("how to improve", "how to reduce")
- Evaluation queries ("is this good for", "does this work for")

Return a JSON object with this exact structure:
{
  "queries": [
    {
      "query": "the full natural language question",
      "intent": "comparison|best_of|how_to|evaluation|other"
    }
  ]
}

Generate 15-20 realistic queries. Ensure variety in intent types. Make queries natural and conversational."""
        
        competitors_str = ", ".join(profile_data.get("competitors", []))
        user_message = f"""Business Profile:
Name: {profile_data.get('name', 'Unknown')}
Domain: {profile_data.get('domain', 'unknown.com')}
Industry: {profile_data.get('industry', 'Unknown')}
Description: {profile_data.get('description', '')}
Competitors: {competitors_str}

Generate realistic queries that target customers in this space would ask AI assistants. These should be commercially valuable queries where the business wants to appear."""
        
        try:
            response = self.call_llm(system_prompt, user_message, json_mode=True)
            result = self._parse_json_response(response)
            
            # Validate and normalize response
            if not isinstance(result, dict) or "queries" not in result:
                logger.warning(f"Unexpected response structure: {result}")
                return {"queries": []}
            
            queries = result.get("queries", [])
            if not isinstance(queries, list):
                logger.warning(f"Queries not a list: {type(queries)}")
                return {"queries": []}
            
            # Validate each query has required fields
            validated_queries = []
            for q in queries:
                if isinstance(q, dict) and "query" in q:
                    validated_queries.append({
                        "query_text": q.get("query", "").strip(),
                        "intent": q.get("intent", "other"),
                    })
            
            return {"queries": validated_queries}
        
        except Exception as e:
            logger.error(f"Error in QueryDiscoveryAgent: {e}")
            return {"queries": [], "error": str(e)}

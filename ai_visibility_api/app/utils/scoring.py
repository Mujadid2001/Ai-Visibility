"""Opportunity score calculation utilities."""
from typing import Dict, Any


def calculate_opportunity_score(
    search_volume: int,
    competitive_difficulty: int,
    domain_visible: bool,
    intent_type: str = "other",
) -> float:
    """Calculate opportunity score for a query (0.0 - 1.0).
    
    Scoring formula considers:
    - Search volume (higher = higher opportunity)
    - Competitive difficulty (lower = easier to capture)
    - Domain visibility (not visible = max gap = higher opportunity)
    - Query intent (commercial intents score higher)
    
    Args:
        search_volume: Estimated monthly searches (integer)
        competitive_difficulty: Competitive difficulty 0-100
        domain_visible: Whether domain appears in AI answers
        intent_type: Query intent (best_of, comparison, how_to, evaluation, other)
    
    Returns:
        Opportunity score from 0.0 to 1.0
    """
    # Normalize search volume to 0-1 scale (cap at 10000)
    volume_score = min(search_volume / 10000.0, 1.0)
    
    # Difficulty inverse score (lower difficulty = higher score)
    difficulty_score = 1.0 - (competitive_difficulty / 100.0)
    
    # Visibility bonus: if not visible, we have a gap to fill
    visibility_bonus = 0.3 if not domain_visible else -0.1
    
    # Intent multiplier: commercial intents are more valuable
    intent_multipliers = {
        "comparison": 1.3,
        "best_of": 1.3,
        "evaluation": 1.2,
        "how_to": 1.1,
        "other": 1.0,
    }
    intent_mult = intent_multipliers.get(intent_type, 1.0)
    
    # Combined score with weighted components
    # Formula: (60% volume + 30% difficulty + 10% visibility) × intent multiplier
    base_score = (volume_score * 0.6) + (difficulty_score * 0.3) + (visibility_bonus * 0.1)
    final_score = base_score * intent_mult
    
    # Clamp to 0.0-1.0 range
    return max(0.0, min(1.0, final_score))


def score_query_batch(queries: list) -> list:
    """Score multiple queries efficiently.
    
    Args:
        queries: List of query dicts with required scoring fields
    
    Returns:
        List of queries with added opportunity_score field
    """
    scored = []
    for query in queries:
        score = calculate_opportunity_score(
            search_volume=query.get("estimated_search_volume", 0),
            competitive_difficulty=query.get("competitive_difficulty", 50),
            domain_visible=query.get("domain_visible", False),
            intent_type=query.get("intent", "other"),
        )
        query["opportunity_score"] = score
        scored.append(query)
    
    return sorted(scored, key=lambda q: q.get("opportunity_score", 0), reverse=True)

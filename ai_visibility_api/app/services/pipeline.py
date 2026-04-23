"""Pipeline orchestrator service."""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from app import db
from app.models import BusinessProfile, PipelineRun, DiscoveredQuery, ContentRecommendation
from app.agents import QueryDiscoveryAgent, VisibilityScoringAgent, ContentRecommendationAgent
from app.utils.scoring import calculate_opportunity_score

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the 3-agent AI pipeline for discovering and scoring queries."""
    
    def __init__(self, ai_provider: str = None):
        """Initialize orchestrator with AI provider."""
        self.discovery_agent = QueryDiscoveryAgent(provider=ai_provider)
        self.scoring_agent = VisibilityScoringAgent(provider=ai_provider)
        self.recommendation_agent = ContentRecommendationAgent(provider=ai_provider)
    
    def run_pipeline(self, profile_uuid: str) -> Dict[str, Any]:
        """Run the complete 3-agent pipeline for a profile.
        
        Args:
            profile_uuid: UUID of the business profile
        
        Returns:
            Dict with pipeline results including discovered queries and recommendations
        """
        # Get profile
        profile = BusinessProfile.query.filter_by(uuid=profile_uuid).first()
        if not profile:
            return {"error": f"Profile {profile_uuid} not found"}
        
        # Create pipeline run record
        run = PipelineRun(profile_uuid=profile_uuid, status="running")
        db.session.add(run)
        db.session.commit()
        
        try:
            logger.info(f"Starting pipeline for profile {profile_uuid}")
            
            # Agent 1: Discover Queries
            logger.info("Running Agent 1: Query Discovery")
            profile_data = {
                "name": profile.name,
                "domain": profile.domain,
                "industry": profile.industry,
                "description": profile.description,
                "competitors": profile.competitors,
            }
            
            discovery_result = self.discovery_agent.run(profile_data)
            if "error" in discovery_result:
                raise Exception(f"Discovery Agent failed: {discovery_result['error']}")
            
            discovered_queries = discovery_result.get("queries", [])
            run.queries_discovered = len(discovered_queries)
            logger.info(f"Discovered {len(discovered_queries)} queries")
            
            # Agent 2: Score Queries
            logger.info("Running Agent 2: Visibility Scoring")
            scored_queries = []
            for query_item in discovered_queries:
                query_text = query_item.get("query_text", "")
                intent = query_item.get("intent", "other")
                
                try:
                    score_result = self.scoring_agent.run(
                        query_text=query_text,
                        target_domain=profile.domain,
                        industry=profile.industry,
                        competitors=profile.competitors,
                    )
                    
                    # Calculate opportunity score
                    opportunity_score = calculate_opportunity_score(
                        search_volume=score_result.get("estimated_search_volume", 0),
                        competitive_difficulty=score_result.get("competitive_difficulty", 50),
                        domain_visible=score_result.get("domain_would_appear", False),
                        intent_type=intent,
                    )
                    
                    scored_item = {
                        "query_text": query_text,
                        "estimated_search_volume": score_result.get("estimated_search_volume", 0),
                        "competitive_difficulty": score_result.get("competitive_difficulty", 50),
                        "domain_visible": score_result.get("domain_would_appear", False),
                        "visibility_position": score_result.get("visibility_position"),
                        "opportunity_score": opportunity_score,
                        "intent": intent,
                    }
                    scored_queries.append(scored_item)
                
                except Exception as e:
                    logger.error(f"Error scoring query '{query_text}': {e}")
                    # Continue processing other queries
                    continue
            
            run.queries_scored = len(scored_queries)
            logger.info(f"Scored {len(scored_queries)} queries")
            
            # Save discovered queries to database
            for scored_query in scored_queries:
                query_obj = DiscoveredQuery(
                    profile_uuid=profile_uuid,
                    run_uuid=run.uuid,
                    query_text=scored_query["query_text"],
                    estimated_search_volume=scored_query["estimated_search_volume"],
                    competitive_difficulty=scored_query["competitive_difficulty"],
                    opportunity_score=scored_query["opportunity_score"],
                    domain_visible=scored_query["domain_visible"],
                    visibility_position=scored_query["visibility_position"],
                )
                db.session.add(query_obj)
            
            db.session.commit()
            
            # Agent 3: Generate Recommendations
            logger.info("Running Agent 3: Content Recommendations")
            
            # Focus on top opportunity queries where domain is not visible
            top_queries = sorted(
                [q for q in scored_queries if not q["domain_visible"]],
                key=lambda q: q["opportunity_score"],
                reverse=True,
            )[:5]  # Get top 5 opportunities
            
            for query_item in top_queries:
                try:
                    rec_result = self.recommendation_agent.run(
                        query_text=query_item["query_text"],
                        target_domain=profile.domain,
                        industry=profile.industry,
                        profile_name=profile.name,
                    )
                    
                    # Get the actual query object from database
                    query_obj = DiscoveredQuery.query.filter_by(
                        profile_uuid=profile_uuid,
                        query_text=query_item["query_text"],
                    ).first()
                    
                    if not query_obj:
                        logger.warning(f"Could not find query object for '{query_item['query_text']}'")
                        continue
                    
                    # Save recommendations
                    for rec in rec_result.get("recommendations", []):
                        rec_obj = ContentRecommendation(
                            profile_uuid=profile_uuid,
                            query_uuid=query_obj.uuid,
                            content_type=rec.get("content_type", "blog_post"),
                            title=rec.get("title", ""),
                            rationale=rec.get("rationale", ""),
                            target_keywords=rec.get("target_keywords", []),
                            priority=rec.get("priority", "medium"),
                        )
                        db.session.add(rec_obj)
                
                except Exception as e:
                    logger.error(f"Error generating recommendations for '{query_item['query_text']}': {e}")
                    # Continue with next query
                    continue
            
            db.session.commit()
            
            # Update run status
            run.status = "completed"
            run.completed_at = datetime.utcnow()
            db.session.commit()
            
            # Build response
            response = {
                "run_uuid": run.uuid,
                "profile_uuid": profile_uuid,
                "status": "completed",
                "queries_discovered": run.queries_discovered,
                "queries_scored": run.queries_scored,
                "top_opportunity_queries": self._get_top_queries(scored_queries, 3),
                "recommendations_generated": len(ContentRecommendation.query.filter_by(
                    profile_uuid=profile_uuid
                ).all()),
            }
            
            logger.info(f"Pipeline completed for profile {profile_uuid}")
            return response
        
        except Exception as e:
            logger.error(f"Pipeline failed for profile {profile_uuid}: {e}")
            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            db.session.commit()
            return {
                "run_uuid": run.uuid,
                "status": "failed",
                "error": str(e),
            }
    
    def recheck_query(self, query_uuid: str) -> Dict[str, Any]:
        """Re-run visibility scoring on a single query.
        
        Args:
            query_uuid: UUID of the query to recheck
        
        Returns:
            Updated query scoring data
        """
        query = DiscoveredQuery.query.filter_by(uuid=query_uuid).first()
        if not query:
            return {"error": f"Query {query_uuid} not found"}
        
        profile = query.profile
        
        try:
            logger.info(f"Rechecking query {query_uuid}: '{query.query_text}'")
            
            # Re-run Agent 2
            score_result = self.scoring_agent.run(
                query_text=query.query_text,
                target_domain=profile.domain,
                industry=profile.industry,
                competitors=profile.competitors,
            )
            
            # Recalculate opportunity score
            opportunity_score = calculate_opportunity_score(
                search_volume=score_result.get("estimated_search_volume", query.estimated_search_volume),
                competitive_difficulty=score_result.get("competitive_difficulty", query.competitive_difficulty),
                domain_visible=score_result.get("domain_would_appear", query.domain_visible),
                intent_type="other",  # We don't have intent stored
            )
            
            # Update query record
            query.estimated_search_volume = score_result.get("estimated_search_volume", query.estimated_search_volume)
            query.competitive_difficulty = score_result.get("competitive_difficulty", query.competitive_difficulty)
            query.domain_visible = score_result.get("domain_would_appear", query.domain_visible)
            query.visibility_position = score_result.get("visibility_position")
            query.opportunity_score = opportunity_score
            db.session.commit()
            
            return query.to_dict()
        
        except Exception as e:
            logger.error(f"Error rechecking query {query_uuid}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def _get_top_queries(queries: List[Dict], limit: int = 3) -> List[Dict]:
        """Get top queries by opportunity score."""
        sorted_queries = sorted(
            queries,
            key=lambda q: q.get("opportunity_score", 0),
            reverse=True
        )
        result = []
        for q in sorted_queries[:limit]:
            result.append({
                "query_text": q["query_text"],
                "opportunity_score": round(q["opportunity_score"], 3),
                "search_volume": q["estimated_search_volume"],
                "difficulty": q["competitive_difficulty"],
                "domain_visible": q["domain_visible"],
            })
        return result

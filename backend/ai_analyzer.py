"""
AI Analyzer - Backend AI for analyzing candidate behavior and generating recruiter insights.
This AI never interacts with candidates directly.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from models import Event, AIInteraction, Session as SessionModel, EVENT_CATEGORIES
from langchain_config import get_ai_engine
import logging

logger = logging.getLogger(__name__)


class BehaviorAnalyzer:
    """Analyzes candidate events and generates recruiter insights using AI"""
    
    def __init__(self):
        self.ai_engine = None
        try:
            self.ai_engine = get_ai_engine()
        except:
            logger.warning("AI engine not initialized for BehaviorAnalyzer")
    
    async def analyze_session(
        self, 
        session_id: str, 
        db: Session
    ) -> Dict[str, Any]:
        """
        Analyze complete interview session and generate insights
        
        Args:
            session_id: Session to analyze
            db: Database session
        
        Returns:
            Comprehensive analysis with scores, insights, and recommendations
        """
        # Fetch session data
        session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
        if not session:
            return {"error": "Session not found"}
        
        # Fetch all events and AI interactions
        events = db.query(Event).filter(
            Event.session_id == session_id
        ).order_by(Event.sequence_number).all()
        
        ai_interactions = db.query(AIInteraction).filter(
            AIInteraction.session_id == session_id
        ).order_by(AIInteraction.timestamp).all()
        
        # Build analysis context
        analysis_context = self._build_analysis_context(
            session, events, ai_interactions
        )
        
        # Generate AI insights
        insights = await self._generate_insights(analysis_context)
        
        return insights
    
    def _build_analysis_context(
        self,
        session: SessionModel,
        events: List[Event],
        ai_interactions: List[AIInteraction]
    ) -> Dict[str, Any]:
        """Build structured context for AI analysis"""
        
        # Categorize events
        event_summary = {}
        for category, event_types in EVENT_CATEGORIES.items():
            event_summary[category] = [
                {
                    "type": e.event_type,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "metadata": e.event_metadata
                }
                for e in events if e.event_type in event_types
            ]
        
        # Analyze SQL queries
        sql_queries = [
            e.event_metadata for e in events 
            if e.event_type == "SQL_RUN" and e.event_metadata
        ]
        
        # AI interaction patterns
        ai_summary = {
            "total_prompts": len(ai_interactions),
            "intents": {},
            "escalations": 0,
            "code_copied": sum(1 for e in events if e.event_type == "AI_CODE_COPIED"),
            "code_modified": sum(1 for e in events if e.event_type == "AI_CODE_MODIFIED")
        }
        
        for interaction in ai_interactions:
            intent = interaction.intent_label or "UNKNOWN"
            ai_summary["intents"][intent] = ai_summary["intents"].get(intent, 0) + 1
        
        # Calculate session metrics
        duration = None
        if session.end_time:
            duration = (session.end_time - session.start_time).total_seconds() / 60
        
        # Interview phase data
        interview_qa = []
        if session.phase in ["interview", "completed"]:
            interview_qa = [
                {
                    "type": e.event_type,
                    "content": e.event_metadata.get("question") or e.event_metadata.get("answer", ""),
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None
                }
                for e in events 
                if e.event_type in ["INTERVIEW_QUESTION", "INTERVIEW_ANSWER"]
            ]
        
        return {
            "candidate_name": session.candidate_name,
            "session_duration_minutes": duration,
            "phase": session.phase,
            "total_events": len(events),
            "event_categories": event_summary,
            "sql_queries": sql_queries[:10],  # First 10 queries
            "ai_interaction_summary": ai_summary,
            "interview_qa": interview_qa,
            "problem_id": session.problem_id
        }
    
    async def _generate_insights(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to generate deep insights from context"""
        
        if not self.ai_engine:
            return self._generate_fallback_insights(context)
        
        system_prompt = """You are an expert recruiter analyzing a data analyst interview session.
You will receive structured data about the candidate's behavior, code, SQL queries, and AI usage.

Your task: Generate comprehensive hiring insights in JSON format.

Analyze:
1. SQL Query Quality - Complexity, efficiency, correctness
2. Problem-Solving Approach - Methodology, iteration, adaptability
3. AI Collaboration - Strategic vs. over-reliant usage
4. Code Quality - Structure, comments, best practices
5. Time Management - Pacing, productivity
6. Communication - Interview responses, explanations

Provide scores (0-100) and specific evidence for each dimension."""

        user_message = f"""Analyze this interview session:

Candidate: {context['candidate_name']}
Duration: {context.get('session_duration_minutes', 'N/A')} minutes
Phase: {context['phase']}
Total Events: {context['total_events']}

SQL Queries Executed: {len(context['sql_queries'])}
Sample Queries: {json.dumps(context['sql_queries'][:3], indent=2)}

AI Interactions: {context['ai_interaction_summary']['total_prompts']}
AI Intent Breakdown: {json.dumps(context['ai_interaction_summary']['intents'], indent=2)}
Code Copied from AI: {context['ai_interaction_summary']['code_copied']}
Code Modified After AI: {context['ai_interaction_summary']['code_modified']}

Event Categories Summary:
{json.dumps({k: len(v) for k, v in context['event_categories'].items()}, indent=2)}

Interview Q&A: {len(context['interview_qa'])} exchanges

Generate a JSON response with this exact structure:
{{
  "overall_score": <0-100>,
  "hire_recommendation": "<strong_yes|yes|maybe|no|strong_no>",
  "key_strengths": ["strength1", "strength2", "strength3"],
  "areas_for_improvement": ["area1", "area2"],
  "dimension_scores": {{
    "sql_quality": <0-100>,
    "problem_solving": <0-100>,
    "ai_collaboration": <0-100>,
    "code_quality": <0-100>,
    "time_management": <0-100>,
    "communication": <0-100>
  }},
  "detailed_insights": "2-3 paragraph narrative about the candidate's performance",
  "red_flags": ["flag1", "flag2"] or [],
  "standout_moments": ["moment1", "moment2"] or []
}}"""

        try:
            response = await self.ai_engine.generate(system_prompt, user_message)
            
            # Parse JSON response
            insights = json.loads(response)
            insights["generated_at"] = datetime.utcnow().isoformat()
            insights["ai_model"] = self.ai_engine.get_active_model_name()
            
            return insights
        
        except Exception as e:
            logger.error(f"AI insight generation failed: {e}")
            return self._generate_fallback_insights(context)
    
    def _generate_fallback_insights(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic insights without AI"""
        
        sql_count = len(context['sql_queries'])
        ai_usage = context['ai_interaction_summary']['total_prompts']
        events_count = context['total_events']
        
        # Simple heuristic scoring
        sql_score = min(100, (sql_count / 10) * 100)
        ai_score = max(20, 100 - (ai_usage * 5))  # Penalize heavy AI usage
        activity_score = min(100, (events_count / 50) * 100)
        
        overall = int((sql_score + ai_score + activity_score) / 3)
        
        return {
            "overall_score": overall,
            "hire_recommendation": "maybe" if overall >= 50 else "no",
            "key_strengths": [
                f"Executed {sql_count} SQL queries",
                f"Generated {events_count} total events"
            ],
            "areas_for_improvement": [
                "AI-generated insights unavailable - manual review recommended"
            ],
            "dimension_scores": {
                "sql_quality": int(sql_score),
                "problem_solving": int(activity_score),
                "ai_collaboration": int(ai_score),
                "code_quality": 50,
                "time_management": 50,
                "communication": 50
            },
            "detailed_insights": "Basic analysis completed. AI insights unavailable. Manual review recommended.",
            "red_flags": [],
            "standout_moments": [],
            "generated_at": datetime.utcnow().isoformat(),
            "ai_model": "Fallback (Rule-based)"
        }


# Global analyzer instance
_analyzer: Optional[BehaviorAnalyzer] = None


def get_analyzer() -> BehaviorAnalyzer:
    """Get global analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = BehaviorAnalyzer()
    return _analyzer

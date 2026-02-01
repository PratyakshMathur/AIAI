"""
AI Helper - Candidate-facing AI assistant with coding and interview modes.
Uses LangChain with Gemini for intelligent, context-aware responses.
"""

import asyncio
from typing import Dict, Any, Optional, List
from models import AI_INTENT_LABELS
from langchain_config import get_ai_engine
import logging

logger = logging.getLogger(__name__)


class AIHelper:
    """AI Assistant helper using Gemini via LangChain"""
    
    def __init__(self):
        self.ai_engine = None
        try:
            self.ai_engine = get_ai_engine()
        except:
            logger.warning("AI engine not initialized for AIHelper")
        
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
    
    def _get_coding_system_prompt(self, schema_info: Optional[Dict] = None) -> str:
        """System prompt for coding assistance mode"""
        schema_text = ""
        if schema_info:
            schema_text = f"\n\nAvailable Tables:\n{schema_info}"
        
        return f"""You are an AI assistant helping a candidate in a SQL coding interview.{schema_text}

IMPORTANT RULES:
1. You can EXPLAIN SQL concepts and syntax
2. You can GUIDE their thinking process
3. You can SUGGEST approaches and query structures
4. You can HELP DEBUG errors
5. You CANNOT write complete solutions
6. You CANNOT provide full working queries
7. Always encourage independent problem-solving

Your responses should:
- Be concise (2-4 sentences max)
- Ask clarifying questions
- Provide hints, not answers
- Explain errors clearly
- Suggest SQL syntax when needed
- Encourage best practices
- Help them learn, not copy

Example Good Response:
"To find the top customers, you'll want to use GROUP BY on customer_id and COUNT() or SUM() for their activity. Try ordering the results with ORDER BY DESC and LIMIT. What metric are you using to define 'top'?"

Example Bad Response:
"Here's the query: SELECT customer_id, COUNT(*) as orders FROM orders GROUP BY customer_id ORDER BY orders DESC LIMIT 5"

Remember: This evaluates how they collaborate with AI, not their ability to copy code."""
    
    def _get_interview_system_prompt(self) -> str:
        """System prompt for interview mode"""
        return """You are an AI interviewer conducting a post-coding interview for a data analyst role.

Your task: Ask thoughtful follow-up questions about their SQL queries and problem-solving approach.

Question Types:
1. **Approach**: "Walk me through your thought process"
2. **Insights**: "What patterns did you discover in the data?"
3. **Optimization**: "How would you optimize this query for larger datasets?"
4. **Trade-offs**: "Why did you choose JOIN over subquery here?"
5. **Business Impact**: "How would these insights help the business?"

Guidelines:
- Ask ONE question at a time
- Be conversational and encouraging
- Probe deeper on interesting points
- Evaluate their analytical thinking
- Keep questions relevant to their actual queries

Your tone should be:
- Professional but friendly
- Curious and engaged
- Supportive, not intimidating

Example Questions:
- "I see you used a LEFT JOIN here. Can you explain why you chose that over INNER JOIN?"
- "What was the most surprising insight you found in the data?"
- "If you had more time, how would you extend this analysis?"
"""
    
    async def process_prompt(
        self, 
        user_prompt: str, 
        context_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        mode: str = "coding"
    ) -> str:
        """
        Process user prompt with context-aware AI
        
        Args:
            user_prompt: User's question
            context_data: Additional context (code, errors, schema)
            session_id: Session ID for conversation history
            mode: 'coding' or 'interview'
        
        Returns:
            AI response
        """
        if not self.ai_engine:
            return "AI service temporarily unavailable. Please try again."
        
        # Get appropriate system prompt
        if mode == "interview":
            system_prompt = self._get_interview_system_prompt()
        else:
            schema_info = context_data.get("schema") if context_data else None
            system_prompt = self._get_coding_system_prompt(schema_info)
        
        # Build enhanced user message with context
        enhanced_message = self._build_context_message(user_prompt, context_data)
        
        # Get conversation history for this session
        history = self.conversation_history.get(session_id, []) if session_id else None
        
        try:
            # Generate response
            logger.info(f"🔍 AI Helper calling engine: mode={mode}, session={session_id}, prompt_len={len(user_prompt)}")
            response = await self.ai_engine.generate(
                system_prompt=system_prompt,
                user_message=enhanced_message,
                conversation_history=history
            )
            logger.info(f"✅ AI Helper got response: {response[:100]}...")
            
            # Update conversation history
            if session_id:
                if session_id not in self.conversation_history:
                    self.conversation_history[session_id] = []
                
                self.conversation_history[session_id].append({
                    "role": "user",
                    "content": user_prompt
                })
                self.conversation_history[session_id].append({
                    "role": "assistant",
                    "content": response
                })
                
                # Keep only last 10 exchanges
                if len(self.conversation_history[session_id]) > 20:
                    self.conversation_history[session_id] = self.conversation_history[session_id][-20:]
            
            return response
        
        except Exception as e:
            logger.error(f"AI Helper error: {e}")
            return "I encountered an error processing your request. Please try rephrasing your question."
    
    def _build_context_message(self, user_prompt: str, context_data: Optional[Dict[str, Any]]) -> str:
        """Build context-enhanced user message"""
        parts = []
        
        if context_data:
            if "code" in context_data and context_data["code"]:
                parts.append(f"Current SQL Query:\n```sql\n{context_data['code']}\n```\n")
            
            if "error" in context_data and context_data["error"]:
                parts.append(f"Error Message:\n{context_data['error']}\n")
            
            if "query_result" in context_data:
                parts.append(f"Query Result: {context_data['query_result']}\n")
        
        parts.append(f"Question: {user_prompt}")
        
        return "\n".join(parts)
    
    async def generate_interview_question(
        self,
        session_id: str,
        query_history: List[str],
        question_number: int = 1
    ) -> str:
        """
        Generate interview question based on candidate's queries
        
        Args:
            session_id: Session ID
            query_history: List of SQL queries executed
            question_number: Which question number (1-5)
        
        Returns:
            Interview question
        """
        if not self.ai_engine:
            return "What was your approach to solving this problem?"
        
        system_prompt = self._get_interview_system_prompt()
        
        user_message = f"""This is question #{question_number} of the interview.

Candidate's SQL Queries:
{chr(10).join([f"{i+1}. {q[:200]}" for i, q in enumerate(query_history[-5:])])}

Generate ONE thoughtful interview question about their approach, insights, or decision-making."""

        try:
            question = await self.ai_engine.generate(
                system_prompt=system_prompt,
                user_message=user_message
            )
            return question
        except:
            # Fallback questions
            fallback_questions = [
                "Walk me through your problem-solving approach for this task.",
                "What insights did you discover in the data?",
                "Why did you choose this particular query structure?",
                "How would you optimize your query for a larger dataset?",
                "What business recommendations would you make based on your findings?"
            ]
            return fallback_questions[min(question_number - 1, len(fallback_questions) - 1)]
    
    def classify_intent(self, user_prompt: str) -> str:
        """Classify the intent of user's prompt"""
        prompt_lower = user_prompt.lower()
        
        # Intent classification rules
        if any(word in prompt_lower for word in ["what is", "explain", "define", "how does", "concept"]):
            return "CONCEPT_HELP"
        
        elif any(word in prompt_lower for word in ["error", "bug", "debug", "fix", "wrong", "not working"]):
            return "DEBUG_HELP"
        
        elif any(word in prompt_lower for word in ["approach", "strategy", "how to", "method", "technique"]):
            return "APPROACH_HELP"
        
        elif any(word in prompt_lower for word in ["check", "validate", "correct", "verify", "review"]):
            return "VALIDATION"
        
        elif any(word in prompt_lower for word in ["solve", "solution", "answer", "complete", "finish"]):
            return "DIRECT_SOLUTION"
        
        else:
            return "EXPLANATION"
    
    def clear_history(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]

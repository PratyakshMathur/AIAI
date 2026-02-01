# AI System Testing Guide

## Overview
This guide will help you test the complete dual-AI system with phase transitions.

## Prerequisites

1. **Install Python Dependencies**
```bash
cd backend
pip install langchain==0.1.0 langchain-google-genai==0.0.6 google-generativeai==0.3.2
```

2. **Set Gemini API Key**
```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

3. **Start Backend**
```bash
cd backend
python main.py
```

4. **Start Frontend** (in another terminal)
```bash
cd frontend
npm start
```

## Test Scenarios

### 1. Test Coding Phase AI Helper

1. Create a new session as candidate
2. Open a SQL notebook cell
3. Write a simple query: `SELECT * FROM customers LIMIT 5;`
4. Click the AI Assistant panel (right side)
5. Ask: "How can I join customers with orders?"
6. Verify:
   - ✅ AI responds with SQL join guidance
   - ✅ Event logged: `AI_PROMPT`
   - ✅ Event logged: `AI_RESPONSE`

### 2. Test Phase Submission

1. While in coding mode, click **"Submit & Start Interview"** button
2. Verify:
   - ✅ Button changes to "Interview Mode" badge
   - ✅ AI chat updates to interview mode (🎤 icon)
   - ✅ Events logged: `PHASE_SUBMITTED`, `INTERVIEW_STARTED`
   - ✅ First interview question appears in AI chat
   - ✅ Database: `session.phase = 'interview'`

### 3. Test Interview Mode AI

1. After submitting, use the AI chat
2. Type an answer to the interview question
3. Verify:
   - ✅ AI asks follow-up questions about your code
   - ✅ Event logged: `INTERVIEW_ANSWER`
   - ✅ Event logged: `INTERVIEW_QUESTION`
   - ✅ Questions are contextual (reference your SQL queries)

### 4. Test SQL Complexity Tracking

1. Execute different SQL queries:
   ```sql
   -- Simple query
   SELECT * FROM customers;
   
   -- Complex query with JOIN and GROUP BY
   SELECT c.name, COUNT(o.id) as order_count
   FROM customers c
   LEFT JOIN orders o ON c.id = o.customer_id
   GROUP BY c.name
   HAVING COUNT(o.id) > 5;
   ```

2. Verify in backend logs:
   - ✅ Event `SQL_COMPLEXITY_DETECTED` with metadata showing:
     - `has_join: true`
     - `has_aggregation: true`
     - `has_subquery: false`
     - `complexity_score: ...`

### 5. Test Schema Exploration Tracking

1. Click "📋 Schema" button in notebook toolbar
2. Verify:
   - ✅ Schema popup appears
   - ✅ Event logged: `SCHEMA_EXPLORED`

### 6. Test AI Analyzer (Recruiter Side)

1. Switch to Recruiter Dashboard
2. Click on a completed session
3. Click **"✨ Generate AI Insights"** button
4. Wait for analysis (may take 10-15 seconds)
5. Verify insights displayed:
   - ✅ **Overall Score**: Number out of 100
   - ✅ **Hire Recommendation**: Strong Hire / Hire / Maybe / No Hire
   - ✅ **Dimension Scores**: SQL quality, problem solving, AI collaboration, etc.
   - ✅ **Key Strengths**: Bullet points
   - ✅ **Areas for Improvement**: Bullet points
   - ✅ **Red Flags**: Any concerning behaviors
   - ✅ **Standout Moments**: Impressive actions
   - ✅ **Detailed Insights**: Full analysis text

### 7. Test Database Persistence

```bash
# Check session phase
sqlite3 backend/ai_interview.db "SELECT session_id, phase, submitted_at FROM sessions WHERE phase = 'interview';"

# Check AI insights
sqlite3 backend/ai_interview.db "SELECT session_id, ai_insights FROM sessions WHERE ai_insights IS NOT NULL;"

# Check event counts
sqlite3 backend/ai_interview.db "SELECT event_type, COUNT(*) FROM events GROUP BY event_type ORDER BY COUNT(*) DESC;"
```

## Backend API Testing

### Test Submit Endpoint
```bash
# Replace SESSION_ID with actual session ID
curl -X POST http://localhost:8000/api/sessions/SESSION_ID/submit
```

Expected response:
```json
{
  "phase": "interview",
  "message": "Phase submitted successfully",
  "first_question": "Can you explain your approach to solving this problem?"
}
```

### Test Analyze Endpoint
```bash
curl -X POST http://localhost:8000/api/sessions/SESSION_ID/analyze
```

Expected response:
```json
{
  "overall_score": 0.75,
  "hire_recommendation": "Hire",
  "key_strengths": ["Strong SQL skills", "Good problem-solving approach"],
  "areas_for_improvement": ["Could optimize query performance"],
  "dimension_scores": {
    "sql_quality": 0.8,
    "problem_solving": 0.7,
    "ai_collaboration": 0.75
  },
  "red_flags": [],
  "standout_moments": ["Used complex JOIN efficiently"],
  "detailed_insights": "..."
}
```

## Troubleshooting

### Gemini API Issues
- **Error**: `Invalid API key`
  - Solution: Verify `GEMINI_API_KEY` environment variable is set
  - Test: `echo $GEMINI_API_KEY`

- **Error**: `Rate limit exceeded`
  - Solution: Free tier has 15 requests/min limit
  - Wait 1 minute and retry

### AI Response is Empty
- Check backend logs for initialization: `✅ AI Engine initialized`
- If not initialized, check API key
- Verify LangChain packages installed: `pip list | grep langchain`

### Events Not Tracking
- Check browser console for errors
- Verify event tracker initialized: Check for `eventTracker.initialize()` call
- Check backend `/api/events/{session_id}` endpoint returns events

### Insights Generation Fails
- Ensure session has events: Must have executed queries and used AI
- Check Gemini API quota (free tier limits)
- Fallback insights should still generate if AI fails

## Success Criteria

✅ **Phase 1 - Coding Mode**:
- AI provides SQL help without giving complete solutions
- Events track all interactions
- Conversation history maintained

✅ **Phase 2 - Submit Transition**:
- Button changes state
- Phase updates in database
- First interview question generated

✅ **Phase 3 - Interview Mode**:
- AI acts as interviewer
- Questions reference candidate's code
- Events properly categorized

✅ **Phase 4 - Analysis**:
- Analyzer generates comprehensive insights
- Scores calculated for all dimensions
- Strengths, improvements, and red flags identified

✅ **Phase 5 - Recruiter View**:
- Dashboard displays insights beautifully
- All data persisted correctly
- Visual feedback clear and actionable

## Expected Event Flow

```
SESSION_STARTED
  ↓
CODE_EDIT (multiple)
SQL_EXECUTION (multiple)
SQL_COMPLEXITY_DETECTED (auto)
AI_PROMPT (multiple)
AI_RESPONSE (multiple)
  ↓
PHASE_SUBMITTED
INTERVIEW_STARTED
  ↓
INTERVIEW_QUESTION
INTERVIEW_ANSWER (multiple)
INTERVIEW_QUESTION (multiple)
  ↓
SESSION_ENDED
  ↓
[Recruiter triggers analysis]
  ↓
AI insights stored in database
```

## Next Steps After Testing

1. Fine-tune AI prompts for better responses
2. Add more SQL complexity markers
3. Implement time-based analytics
4. Add export functionality for insights
5. Create comparison views for multiple candidates

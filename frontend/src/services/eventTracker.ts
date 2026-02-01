import { apiService } from './api';
import { v4 as uuidv4 } from 'uuid';

export type EventType = 
  // Session Lifecycle
  | 'SESSION_START'
  | 'SESSION_PAUSED'
  | 'SESSION_RESUMED'
  | 'PHASE_SUBMITTED'
  | 'INTERVIEW_STARTED'
  | 'SESSION_COMPLETED'
  | 'SESSION_ABANDONED'
  // Code Editing
  | 'CODE_EDIT'
  | 'CODE_RUN'
  | 'CODE_DELETED'
  | 'CODE_RESTORED'
  | 'COMMENT_ADDED'
  | 'COPY_PASTE_DETECTED'
  // SQL Operations
  | 'SQL_RUN'
  | 'QUERY_MODIFIED'
  | 'QUERY_OPTIMIZED'
  | 'QUERY_SUBMITTED'
  | 'SYNTAX_ERROR'
  | 'TABLE_JOINED'
  | 'AGGREGATE_USED'
  | 'SUBQUERY_USED'
  | 'GROUPING_APPLIED'
  | 'FILTER_APPLIED'
  | 'WINDOW_FUNCTION_USED'
  // Execution & Results
  | 'RUN_RESULT'
  | 'ERROR_OCCURRED'
  | 'ERROR_RESOLVED'
  | 'RESULT_VALIDATED'
  | 'RESULT_COMPARED'
  | 'OUTLIER_DETECTED'
  | 'NULL_HANDLED'
  // Data Exploration
  | 'DATA_VIEW'
  | 'SCHEMA_EXPLORED'
  | 'TABLE_PREVIEWED'
  | 'DATA_QUALITY_CHECKED'
  // AI Interaction
  | 'AI_PROMPT'
  | 'AI_RESPONSE'
  | 'AI_RESPONSE_USED'
  | 'AI_CODE_COPIED'
  | 'AI_CODE_MODIFIED'
  | 'AI_HINT_REQUESTED'
  | 'AI_HELP_ESCALATION'
  | 'HELP_DECLINED'
  // Interview Phase
  | 'INTERVIEW_QUESTION'
  | 'INTERVIEW_ANSWER'
  | 'INSIGHT_SHARED'
  | 'APPROACH_EXPLAINED'
  | 'FOLLOWUP_ANSWERED'
  // Problem Solving
  | 'APPROACH_CHANGED'
  | 'HYPOTHESIS_FORMED'
  | 'VALIDATION_ATTEMPT'
  | 'DEAD_END_REACHED'
  | 'BREAKTHROUGH'
  | 'BACKTRACKED'
  // Attention & Timing
  | 'IDLE_GAP'
  | 'FOCUS_LOST'
  | 'FOCUS_REGAINED'
  | 'PAUSE_DETECTED'
  | 'RUSH_DETECTED'
  | 'TIME_WARNING_SHOWN'
  // Workspace
  | 'NOTEBOOK_CELL_ADDED'
  | 'NOTEBOOK_CELL_DELETED'
  | 'CELL_REORDERED'
  | 'RESULT_EVALUATED'
  // Legacy
  | 'CHART_CREATED';

interface EventData {
  type: EventType;
  event_metadata?: Record<string, any>;
}

class EventTracker {
  private sessionId: string | null = null;
  private eventQueue: EventData[] = [];
  private isProcessing = false;
  private lastActivityTime = Date.now();
  private idleThreshold = 5000; // 5 seconds of inactivity
  private idleTimer?: NodeJS.Timeout;

  initialize(sessionId: string) {
    this.sessionId = sessionId;
    this.startIdleTracking();
    console.log('Event Tracker initialized for session:', sessionId);
  }

  async trackEvent(type: EventType, event_metadata: Record<string, any> = {}) {
    if (!this.sessionId) {
      console.warn('Event tracker not initialized');
      return;
    }

    const eventData: EventData = {
      type,
      event_metadata: {
        ...event_metadata,
        timestamp: new Date().toISOString(),
        client_id: uuidv4(),
      }
    };

    this.eventQueue.push(eventData);
    this.updateActivity();

    if (!this.isProcessing) {
      await this.processQueue();
    }
  }

  private async processQueue() {
    if (this.eventQueue.length === 0 || this.isProcessing) {
      return;
    }

    this.isProcessing = true;

    while (this.eventQueue.length > 0) {
      const event = this.eventQueue.shift();
      if (event && this.sessionId) {
        try {
          await apiService.logEvent({
            session_id: this.sessionId,
            event_type: event.type,
            event_metadata: event.event_metadata
          });
          console.log('Event logged:', event.type, event.event_metadata);
        } catch (error) {
          console.error('Failed to log event:', error);
          // Re-queue the event for retry
          this.eventQueue.unshift(event);
          break;
        }
      }
    }

    this.isProcessing = false;
  }

  private updateActivity() {
    this.lastActivityTime = Date.now();
    this.resetIdleTimer();
  }

  private startIdleTracking() {
    this.resetIdleTimer();
  }

  private resetIdleTimer() {
    if (this.idleTimer) {
      clearTimeout(this.idleTimer);
    }

    this.idleTimer = setTimeout(() => {
      this.trackEvent('IDLE_GAP', {
        idle_duration: Date.now() - this.lastActivityTime
      });
    }, this.idleThreshold);
  }

  // Specific event tracking methods
  trackCodeEdit(code: string, language: string) {
    this.trackEvent('CODE_EDIT', {
      code_length: code.length,
      language,
      lines: code.split('\n').length
    });
  }

  trackCodeRun(code: string, language: string) {
    this.trackEvent('CODE_RUN', {
      code_length: code.length,
      language,
      lines: code.split('\n').length
    });
  }

  trackRunResult(success: boolean, output?: string, error?: string) {
    this.trackEvent('RUN_RESULT', {
      success,
      output_length: output?.length || 0,
      has_error: !!error,
      error_message: error
    });
  }

  trackError(error: string, context?: Record<string, any>) {
    this.trackEvent('ERROR_OCCURRED', {
      error_message: error,
      ...context
    });
  }

  trackErrorResolved(resolution_method?: string) {
    this.trackEvent('ERROR_RESOLVED', {
      resolution_method
    });
  }

  trackDataView(data_info: Record<string, any>) {
    this.trackEvent('DATA_VIEW', data_info);
  }

  trackAIPrompt(prompt: string, intent?: string) {
    this.trackEvent('AI_PROMPT', {
      prompt_length: prompt.length,
      intent
    });
  }

  trackAIResponse(response: string, intent?: string, interactionId?: string) {
    this.trackEvent('AI_RESPONSE', {
      response_length: response.length,
      intent,
      interaction_id: interactionId
    });
  }

  trackAIResponseUsed(interactionId: string, usage_type: string) {
    this.trackEvent('AI_RESPONSE_USED', {
      interaction_id: interactionId,
      usage_type
    });
  }

  trackResultEvaluation(evaluation: Record<string, any>) {
    this.trackEvent('RESULT_EVALUATED', evaluation);
  }

  // ===== NEW: Session Lifecycle Tracking =====
  trackPhaseSubmitted() {
    this.trackEvent('PHASE_SUBMITTED', {
      timestamp: new Date().toISOString()
    });
  }

  trackInterviewStarted() {
    this.trackEvent('INTERVIEW_STARTED', {
      timestamp: new Date().toISOString()
    });
  }

  trackSessionCompleted() {
    this.trackEvent('SESSION_COMPLETED', {
      timestamp: new Date().toISOString()
    });
  }

  // ===== NEW: SQL Operation Tracking =====
  trackQueryModified(oldQuery: string, newQuery: string) {
    this.trackEvent('QUERY_MODIFIED', {
      old_length: oldQuery.length,
      new_length: newQuery.length,
      diff_chars: Math.abs(newQuery.length - oldQuery.length)
    });
  }

  trackQuerySubmitted(query: string, complexity?: Record<string, boolean>) {
    this.trackEvent('QUERY_SUBMITTED', {
      query_length: query.length,
      ...complexity
    });
  }

  trackSQLComplexity(query: string) {
    const upperQuery = query.toUpperCase();
    const complexity = {
      has_join: upperQuery.includes('JOIN'),
      has_aggregate: /COUNT|SUM|AVG|MAX|MIN/.test(upperQuery),
      has_subquery: (query.match(/SELECT/gi) || []).length > 1,
      has_groupby: upperQuery.includes('GROUP BY'),
      has_where: upperQuery.includes('WHERE'),
      has_window: /OVER|PARTITION BY/.test(upperQuery)
    };

    // Track specific complexity events
    if (complexity.has_join) this.trackEvent('TABLE_JOINED', { query_snippet: query.substring(0, 100) });
    if (complexity.has_aggregate) this.trackEvent('AGGREGATE_USED', { query_snippet: query.substring(0, 100) });
    if (complexity.has_subquery) this.trackEvent('SUBQUERY_USED', { query_snippet: query.substring(0, 100) });
    if (complexity.has_groupby) this.trackEvent('GROUPING_APPLIED', { query_snippet: query.substring(0, 100) });
    if (complexity.has_where) this.trackEvent('FILTER_APPLIED', { query_snippet: query.substring(0, 100) });
    if (complexity.has_window) this.trackEvent('WINDOW_FUNCTION_USED', { query_snippet: query.substring(0, 100) });

    return complexity;
  }

  // ===== NEW: Data Exploration Tracking =====
  trackSchemaExplored(tableName?: string) {
    this.trackEvent('SCHEMA_EXPLORED', {
      table_name: tableName,
      timestamp: new Date().toISOString()
    });
  }

  trackTablePreviewed(tableName: string, rowCount?: number) {
    this.trackEvent('TABLE_PREVIEWED', {
      table_name: tableName,
      row_count: rowCount
    });
  }

  // ===== NEW: AI Collaboration Tracking =====
  trackAICodeCopied(code: string, source: string = 'ai_response') {
    this.trackEvent('AI_CODE_COPIED', {
      code_length: code.length,
      source
    });
  }

  trackAICodeModified(originalCode: string, modifiedCode: string) {
    this.trackEvent('AI_CODE_MODIFIED', {
      original_length: originalCode.length,
      modified_length: modifiedCode.length,
      modification_ratio: modifiedCode.length / originalCode.length
    });
  }

  trackHintRequested() {
    this.trackEvent('AI_HINT_REQUESTED', {
      timestamp: new Date().toISOString()
    });
  }

  // ===== NEW: Interview Phase Tracking =====
  trackInterviewQuestion(question: string, questionNumber?: number) {
    this.trackEvent('INTERVIEW_QUESTION', {
      question_length: question.length,
      question_number: questionNumber
    });
  }

  trackInterviewAnswer(answer: string, questionNumber?: number) {
    this.trackEvent('INTERVIEW_ANSWER', {
      answer_length: answer.length,
      question_number: questionNumber
    });
  }

  trackInsightShared(insight: string) {
    this.trackEvent('INSIGHT_SHARED', {
      insight_length: insight.length
    });
  }

  trackApproachExplained(explanation: string) {
    this.trackEvent('APPROACH_EXPLAINED', {
      explanation_length: explanation.length
    });
  }

  // ===== NEW: Focus & Attention Tracking =====
  trackFocusLost() {
    this.trackEvent('FOCUS_LOST', {
      timestamp: new Date().toISOString()
    });
  }

  trackFocusRegained() {
    this.trackEvent('FOCUS_REGAINED', {
      timestamp: new Date().toISOString()
    });
  }

  trackTimeWarning(timeRemaining: number) {
    this.trackEvent('TIME_WARNING_SHOWN', {
      time_remaining_seconds: timeRemaining
    });
  }

  // ===== NEW: Workspace Tracking =====
  trackNotebookCellAdded(cellType: string = 'sql') {
    this.trackEvent('NOTEBOOK_CELL_ADDED', {
      cell_type: cellType
    });
  }

  trackNotebookCellDeleted(cellId: string) {
    this.trackEvent('NOTEBOOK_CELL_DELETED', {
      cell_id: cellId
    });
  }

  // ===== NEW: Copy/Paste Detection =====
  trackCopyPaste(code: string) {
    this.trackEvent('COPY_PASTE_DETECTED', {
      code_length: code.length,
      lines: code.split('\n').length
    });
  }

  cleanup() {
    if (this.idleTimer) {
      clearTimeout(this.idleTimer);
    }
    this.sessionId = null;
    this.eventQueue = [];
  }
}

export const eventTracker = new EventTracker();
export default EventTracker;
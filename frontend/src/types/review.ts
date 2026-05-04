export type Severity = 'low' | 'medium' | 'high' | 'critical';

export interface CheckerFinding {
  finding_id: string;
  project_id: string;
  source_object_id: string;
  source_object_kind: string;
  severity: Severity;
  summary: string;
  details: string;
  source_context?: string;
}

export type ReviewFinding = CheckerFinding;

export type DecisionAction = 'accept' | 'reject' | 'defer' | 'escalate' | 'refine';

export interface ReviewDecision {
  decision_id: string;
  project_id: string;
  target_kind: string;
  target_id: string;
  decision: DecisionAction;
  notes: string | null;
  source_context: string[];
  created_at: string;
  updated_at: string;
}

export interface ReviewDecisionCreateRequest {
  decision_id: string;
  project_id: string;
  target_kind: string;
  target_id: string;
  decision: DecisionAction;
  notes?: string;
  source_context?: string[];
}

export interface FindingsFilter {
  project_id: string;
  source_object_kind?: string;
  severity?: Severity[];
}

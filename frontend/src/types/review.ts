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

export type DecisionAction = 'accept' | 'reject' | 'defer' | 'escalate' | 'refine';

export interface ReviewDecision {
  decision_id: string;
  project_id: string;
  target_kind: string;
  target_id: string;
  decision_action: DecisionAction;
  rationale?: string;
  routed_to_stage?: string;
  notes: string | null;
  source_context: string[];
  created_at: string;
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

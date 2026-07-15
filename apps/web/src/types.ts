export interface EvidenceRef {
  id: string;
  source_id: string;
  label: string;
  locator: Record<string, string | number>;
  snapshot_sha256: string;
  coverage: number;
}

export interface ScoreFactors {
  goal_alignment: number;
  estimated_impact: number;
  evidence_coverage: number;
  urgency: number;
  feasibility: number;
  risk_penalty: number;
}

export interface Opportunity {
  id: string;
  title: string;
  subtitle: string;
  target_alignment: string;
  impact: number;
  factors: ScoreFactors;
  score: number;
  status: string;
  evidence: EvidenceRef[];
  rationale: string;
}

export interface GrowthDiagnostic {
  id: string;
  company: string;
  objective: string;
  generated_at: string;
  data_readiness: number;
  evidence_coverage: number;
  open_approvals: number;
  summary: string;
  counts: Record<string, number>;
  opportunities: Opportunity[];
  plan: Array<{ week: number; range: string; title: string; actions: string[] }>;
  data_gaps: string[];
  detected_planted_insights: string[];
  disclaimer: string;
}

export interface WorkflowNodeDto {
  id: string;
  kind: string;
  label: string;
  position: { x: number; y: number };
  config: Record<string, unknown>;
  output_type: string | null;
}

export interface WorkflowEdgeDto {
  id: string;
  source: string;
  target: string;
  data_type: string;
  branch?: "true" | "false" | null;
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  version: number;
  status: string;
  nodes: WorkflowNodeDto[];
  edges: WorkflowEdgeDto[];
}

export interface ModelProfileView {
  id: string;
  provider: string | null;
  model: string | null;
  local: boolean;
  enabled: boolean;
  configured: boolean;
  selected: boolean;
  available: boolean;
}

export interface WorkflowRunStart {
  run_id: string;
  status: string;
  current_step?: string | null;
  workflow_id: string;
  workflow_version: number;
  model_profile: string | null;
}

export interface WorkflowRunDetail extends WorkflowRunView {
  output: { diagnostic?: GrowthDiagnostic } | null;
  error: { code?: string; message?: string } | null;
}

export interface UserView {
  id: string;
  email: string;
  name: string;
  roles: string[];
}

export interface AuthSession {
  user: UserView | null;
  csrf_token: string | null;
}

export interface SetupStatus {
  steps: string[];
  demo_available: boolean;
  bootstrap_required: boolean;
  auth_enabled: boolean;
  cloud_models_enabled: boolean;
}

export interface SetupProgress {
  current_step: number;
  completed_steps: number[];
  configuration: Record<string, string | boolean | number>;
  status: "in_progress" | "completed";
  updated_at: string | null;
}

export interface WorkflowRunView {
  id: string;
  workflow_id: string;
  workflow_version: number;
  status: string;
  current_step: string | null;
  model_profile: string | null;
  token_usage: Record<string, number> | null;
  started_at: string;
  completed_at: string | null;
}

export interface ApprovalView {
  id: string;
  run_id: string;
  kind: string;
  status: string;
  artifact_uri: string;
  requested_role: string;
  candidate_id: string | null;
  decision_by: string | null;
  decision_reason: string | null;
  expires_at: string;
  decided_at: string | null;
}

export interface OKFCandidateView {
  id: string;
  run_id: string | null;
  status: string;
  base_revision: string;
  candidate_revision: string | null;
  validation_report: { errors?: unknown[]; warnings?: unknown[] };
  created_at: string;
  expires_at: string;
  decision_reason: string | null;
}

export interface DataSourceView {
  id: string;
  name: string;
  connector_type: string;
  read_only: boolean;
  status: string;
  updated_at: string;
}

export interface SourceSyncRunView {
  id: string;
  source_id: string;
  status: string;
  records_seen: number;
  records_persisted: number;
  warnings: string[];
  started_at: string;
  completed_at: string | null;
}

export interface FilePreview {
  source_id: string;
  filename: string;
  bytes: number;
  schema: { source_id: string; entities: Record<string, string[]> };
  preview: Array<{
    entity_type: string;
    external_id: string;
    data: Record<string, unknown>;
    locator: Record<string, unknown>;
  }>;
  warnings: string[];
}

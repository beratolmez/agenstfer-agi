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

export interface AgentDefinitionView {
  id: string;
  name: string;
  version: number;
  model_profile: "local-balanced" | "local-strong" | "cloud-balanced";
  output_type: "CompanyAnalysis" | "OpportunityHypotheses" | "EvidenceReview" | "OKFChangeSet";
  capabilities: string[];
  timeout_seconds: number;
  max_output_tokens: number;
  data_classification: "public" | "internal" | "confidential" | "restricted";
  approval_risk: "low" | "medium" | "high";
  system_prompt?: string;
  status: "draft" | "published";
  created_at?: string;
  updated_at?: string;
}

export interface CapabilityDefinitionView {
  id: string;
  version: number;
  name: string;
  status: string;
  definition: Record<string, unknown>;
}

export interface WorkflowSummary {
  id: string;
  version: number;
  name: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface WorkflowScheduleView {
  id: string;
  workflow_id: string;
  workflow_version: number;
  cron: string;
  timezone: string;
  enabled: boolean;
  last_fire_key: string | null;
}

export interface WorkflowRunStart {
  run_id: string;
  status: string;
  current_step?: string | null;
  workflow_id: string;
  workflow_version: number;
  model_profile: string | null;
}

export interface WorkflowRunStepDetail {
  id: string;
  step_id: string;
  sequence: number;
  kind: string;
  agent_id?: string | null;
  agent_version?: number | null;
  model_profile?: string | null;
  model_provider?: string | null;
  model_name?: string | null;
  data_classification?: string | null;
  redaction_applied?: boolean;
  status: string;
  input_hash?: string | null;
  output?: Record<string, unknown> | null;
  error?: Record<string, unknown> | null;
  token_usage?: { prompt_tokens?: number; completion_tokens?: number; total_tokens?: number } | null;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface WorkflowRunArtifactDetail {
  id: string;
  kind: string;
  summary: string;
  created_at: string;
}

export interface WorkflowRunDetail extends WorkflowRunView {
  idempotency_key?: string | null;
  evidence_ids?: string[];
  agent_versions?: Record<string, number>;
  output: { diagnostic?: GrowthDiagnostic } | null;
  error: { code?: string; message?: string } | null;
  steps?: WorkflowRunStepDetail[];
  artifacts?: WorkflowRunArtifactDetail[];
}

export interface UserView {
  id: string;
  email: string;
  name: string;
  roles: string[];
}

export interface ManagedUserView extends UserView {
  active: boolean;
  created_at: string;
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
  setup_completed?: boolean;
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

export interface TriggerRuleView {
  id: string;
  name: string;
  event_type: string;
  target_workflow_id: string;
  description: string;
  enabled: boolean;
}

export interface TriggerEventView {
  id: string;
  source_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  status: string;
  timestamp: string;
}

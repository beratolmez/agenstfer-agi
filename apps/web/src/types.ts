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
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  version: number;
  status: string;
  nodes: WorkflowNodeDto[];
  edges: WorkflowEdgeDto[];
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

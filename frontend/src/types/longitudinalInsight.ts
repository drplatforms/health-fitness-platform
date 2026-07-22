export type LongitudinalInsightDomain =
  | "recovery"
  | "training"
  | "nutrition"
  | "body_weight"
  | "cross_domain";

export interface LongitudinalInsightWindow {
  start_date: string;
  end_date: string;
  days: number;
  observation_count: number;
  label: string;
}

export interface LongitudinalInsightEvidence {
  metric: string;
  label: string;
  value: string;
  source: string;
  source_fields: string[];
}

export interface LongitudinalInsightCoverage {
  status: "sparse" | "limited" | "sufficient" | "strong";
  observation_count: number;
  comparison_observation_count: number | null;
  expected_observation_count: number | null;
  observation_rate: number | null;
  limitations: string[];
}

export interface LongitudinalInsight {
  stable_id: string;
  domain: LongitudinalInsightDomain;
  insight_type: string;
  title: string;
  explanation: string;
  observation_window: LongitudinalInsightWindow;
  comparison_window: LongitudinalInsightWindow | null;
  evidence: LongitudinalInsightEvidence[];
  evidence_strength: "moderate" | "strong";
  data_coverage: LongitudinalInsightCoverage;
  direction:
    | "improving"
    | "worsening"
    | "stable"
    | "increasing"
    | "decreasing"
    | "recurring"
    | "associated";
  status: "notable" | "supportive" | "attention" | "consistent" | "plateau";
}

export interface LongitudinalInsightResponse {
  success: boolean;
  user_id: number;
  as_of_date: string;
  target_date: string;
  engine_version: string;
  insights: LongitudinalInsight[];
}

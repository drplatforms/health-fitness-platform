import { AIRunTelemetry } from "@/types/aiRunTelemetry";

export type CoachProvider = "local" | "openai";
export type CoachConfidence = "Limited" | "Low" | "Moderate" | "High";

export interface CoachEvidenceItem {
  reference_id: string;
  domain: string;
  label: string;
  fact: string;
  confidence: CoachConfidence;
  observed_at: string | null;
}

export interface CoachEvidencePack {
  pack_version: string;
  as_of_date: string;
  question_topics: string[];
  matched_exercise_name: string | null;
  matched_exercise_context: Record<string, unknown>;
  evidence: CoachEvidenceItem[];
  limitations: string[];
  confidence: CoachConfidence;
}

export interface CoachKnowledgePassage {
  reference_id: string;
  source_id: string;
  source_title: string;
  chunk_id: string;
  heading: string;
  passage: string;
  provenance: string;
  corpus_version: string;
  related_exercises: string[];
}

export interface CoachKnowledgeContext {
  retrieval_version: string;
  corpus_version: string;
  corpus_digest: string;
  question_intents: string[];
  matched_exercise_name: string | null;
  passages: CoachKnowledgePassage[];
}

export interface CoachSuggestedAction {
  action_type: "progression_decision";
  decision: "hold" | "increase_load" | "decrease_load" | "build_baseline";
  evidence_reference: string;
}

export interface CoachAnswerResponse {
  success: true;
  user_id: number;
  answer: string;
  supporting_evidence_references: string[];
  supporting_evidence: CoachEvidenceItem[];
  supporting_knowledge_references: string[];
  supporting_knowledge: CoachKnowledgePassage[];
  confidence: CoachConfidence;
  uncertainty: string | null;
  suggested_action: CoachSuggestedAction | null;
  evidence_pack: CoachEvidencePack;
  knowledge_context: CoachKnowledgeContext;
  provider_run: {
    configured_provider: CoachProvider;
    selected_provider: CoachProvider;
    configured_model: string;
    selected_model: string;
    actual_model: string;
  };
  telemetry: AIRunTelemetry;
}

export interface CoachModelOption {
  id: string;
  label: string;
}

export interface CoachProviderModelOptions {
  models: CoachModelOption[];
  default_model: string;
  source: "ollama" | "configured_fallback" | "curated";
  message: string | null;
}

export interface CoachModelOptionsResponse {
  configured_provider: CoachProvider;
  providers: Record<CoachProvider, CoachProviderModelOptions>;
}

export interface CoachConversationContextTurn {
  role: "user" | "assistant";
  content: string;
}

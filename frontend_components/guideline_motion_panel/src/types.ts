export type GuidanceStatus = "Current" | "Superseded" | "Historical" | "Draft";

export interface Citation {
  document_id: string;
  title: string;
  document_type: string;
  version: string;
  status: GuidanceStatus;
  effective_date: string;
  section?: string | null;
  chunk_id: string;
  source_url?: string | null;
  relevance_explanation: string;
  excerpt?: string | null;
}

export interface RetrievalDiagnostics {
  candidates_considered: number;
  candidates_returned: number;
  top_similarity_score?: number | null;
  current_candidates_found: number;
  superseded_or_historical_candidates_found: number;
  used_historical_override: boolean;
}

export interface MotionPanelPayload {
  question: string;
  answer_text: string;
  is_abstention: boolean;
  confidence_label: "High" | "Medium" | "Low";
  current_guidance_found: boolean;
  generation_mode: "llm" | "extractive_fallback";
  safety_notice: string;
  citations: Citation[];
  retrieval_diagnostics: RetrievalDiagnostics;
}

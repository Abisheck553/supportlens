export type Source = {
  id: string;
  document_id: string;
  title: string;
  filename: string;
  position: number;
  text: string;
  score: number;
  similarity: number;
};
export type Answer = {
  id: string;
  question: string;
  answer: string;
  sources: Source[];
  citation_ids: number[];
  needs_review: boolean;
  mode: string;
  notice: string | null;
  classification: { label: string; model_score: number; model: string };
  method: string;
  latency_ms: number;
  feedback: string | null;
  created_at?: string;
};
export type Doc = {
  id: string;
  title: string;
  filename: string;
  chunk_count: number;
  word_count: number;
  created_at: string;
  content?: string;
};
export type Health = {
  status: string;
  answer_provider: string;
  retrieval_mode: string;
  semantic_enabled: boolean;
  model: string | null;
};
export type Stats = {
  documents: number;
  chunks: number;
  questions: number;
  supported: number;
  helpful: number;
};
export type Case = {
  question: string;
  expected_source: string | null;
  retrieved: string[];
  rank: number | null;
  abstained: boolean;
  passed: boolean;
  latency_ms: number;
};
export type Run = {
  method: string;
  recall_at_3: number;
  mrr_at_3: number;
  unknown_abstention_rate: number;
  mean_latency_ms: number;
  cases: Case[];
};
export type Report = {
  created_at: string;
  dataset: string;
  question_count: number;
  answerable_count: number;
  unknown_count: number;
  retrieval_mode: string;
  limitations: string;
  retrieval: Run[];
  classifier: {
    test_examples: number;
    accuracy: number;
    macro_f1: number;
    majority_baseline_accuracy: number;
  };
};

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, options);
  } catch {
    throw new Error(
      "Cannot reach SupportLens. Check that the local server is running.",
    );
  }
  if (!response.ok) {
    let message = `Request failed (${response.status}). Please try again.`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
      else if (Array.isArray(body.detail))
        message = body.detail
          .map((item: { msg: string }) => item.msg)
          .join(" ");
    } catch {
      /* A proxy may return a non-JSON error. */
    }
    throw new Error(message);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
export const json = (body: unknown, method = "POST"): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

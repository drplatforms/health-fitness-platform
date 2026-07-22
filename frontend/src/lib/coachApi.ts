import {
  CoachAnswerResponse,
  CoachConversationContextTurn,
  CoachModelOptionsResponse,
  CoachProvider,
} from "@/types/coach";

export async function fetchCoachModelOptions(): Promise<CoachModelOptionsResponse> {
  const response = await fetch("/api/coach-models", {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  const payload = (await response.json().catch(() => null)) as
    | CoachModelOptionsResponse
    | { detail?: string }
    | null;
  if (!response.ok) {
    throw new Error(
      payload && "detail" in payload && typeof payload.detail === "string"
        ? payload.detail
        : "Coach models are unavailable.",
    );
  }
  return payload as CoachModelOptionsResponse;
}

export async function askCoach({
  userId,
  question,
  provider,
  model,
  conversationContext,
}: {
  userId: number;
  question: string;
  provider: CoachProvider;
  model: string;
  conversationContext: CoachConversationContextTurn[];
}): Promise<CoachAnswerResponse> {
  const response = await fetch("/api/coach-ask", {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      user_id: userId,
      question,
      provider,
      model,
      conversation_context: conversationContext,
    }),
  });
  const payload = (await response.json().catch(() => null)) as
    | CoachAnswerResponse
    | { detail?: string | { code?: string; message?: string } }
    | null;
  if (!response.ok) {
    const detail = payload && "detail" in payload ? payload.detail : null;
    throw new Error(
      typeof detail === "string"
        ? detail
        : typeof detail?.message === "string"
          ? detail.message
          : "Coach could not answer. Retry or switch providers.",
    );
  }
  return payload as CoachAnswerResponse;
}

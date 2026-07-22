"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { AIRunTelemetrySummary } from "@/components/AIRunTelemetrySummary";
import { askCoach, fetchCoachModelOptions } from "@/lib/coachApi";
import {
  CoachAnswerResponse,
  CoachConversationContextTurn,
  CoachModelOptionsResponse,
  CoachProvider,
  CoachSuggestedAction,
} from "@/types/coach";

const STARTER_QUESTIONS = [
  "Am I making progress?",
  "What should I focus on during an RDL?",
  "How is a Pendlay Row different from a regular Barbell Row?",
  "What common squat mistakes should I watch for?",
];
const MAX_CONTEXT_TURNS = 6;

type ConversationMessage =
  | { id: string; role: "user"; content: string }
  | { id: string; role: "assistant"; result: CoachAnswerResponse };

export function CoachWorkspace({ userId }: { userId: number }) {
  const [options, setOptions] = useState<CoachModelOptionsResponse | null>(null);
  const [provider, setProvider] = useState<CoachProvider>("local");
  const [modelsByProvider, setModelsByProvider] = useState<Record<CoachProvider, string>>({
    local: "",
    openai: "",
  });
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [answerError, setAnswerError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void fetchCoachModelOptions()
      .then((response) => {
        if (cancelled) return;
        setOptions(response);
        setProvider(response.configured_provider);
        setModelsByProvider({
          local: response.providers.local.default_model,
          openai: response.providers.openai.default_model,
        });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setModelsError(
          error instanceof Error ? error.message : "Coach models are unavailable.",
        );
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedModel = modelsByProvider[provider];
  const providerOptions = options?.providers[provider];
  const conversationContext = useMemo(
    () => buildConversationContext(messages),
    [messages],
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || !selectedModel || isAsking) return;

    const userMessage: ConversationMessage = {
      id: messageId("user"),
      role: "user",
      content: trimmedQuestion,
    };
    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setAnswerError(null);
    setIsAsking(true);
    try {
      const result = await askCoach({
        userId,
        question: trimmedQuestion,
        provider,
        model: selectedModel,
        conversationContext,
      });
      setMessages((current) => [
        ...current,
        { id: messageId("assistant"), role: "assistant", result },
      ]);
    } catch (error) {
      setAnswerError(
        error instanceof Error
          ? error.message
          : "Coach could not answer. Retry or switch providers.",
      );
    } finally {
      setIsAsking(false);
    }
  }

  function chooseProvider(nextProvider: CoachProvider) {
    setProvider(nextProvider);
    setAnswerError(null);
  }

  return (
    <section className="space-y-3 sm:space-y-4" aria-label="Coach conversation">
      <div className="rounded-2xl border border-border-subtle bg-surface p-3 shadow-sm sm:p-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-base font-semibold text-text-strong">Grounded Coach</h2>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-text-body">
              Ask about your logged patterns or how an exercise works.
            </p>
          </div>
          {messages.length > 0 ? (
            <button
              type="button"
              onClick={() => {
                setMessages([]);
                setAnswerError(null);
              }}
              className="self-start rounded-lg border border-border px-3 py-2 text-xs font-semibold text-text-body sm:self-auto"
            >
              Clear conversation
            </button>
          ) : null}
        </div>

        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          <label className="text-xs font-semibold text-text-muted">
            Provider
            <select
              value={provider}
              onChange={(event) => chooseProvider(event.target.value as CoachProvider)}
              disabled={!options || isAsking}
              className="mt-1.5 w-full rounded-xl border border-border bg-surface px-3 py-2.5 text-sm font-normal text-text-strong disabled:opacity-60"
            >
              <option value="local">Local / Ollama</option>
              <option value="openai">OpenAI</option>
            </select>
          </label>
          <label className="text-xs font-semibold text-text-muted">
            Model
            <select
              value={selectedModel}
              onChange={(event) =>
                setModelsByProvider((current) => ({
                  ...current,
                  [provider]: event.target.value,
                }))
              }
              disabled={!providerOptions || isAsking}
              className="mt-1.5 w-full rounded-xl border border-border bg-surface px-3 py-2.5 text-sm font-normal text-text-strong disabled:opacity-60"
            >
              {(providerOptions?.models ?? []).map((model) => (
                <option key={model.id} value={model.id}>
                  {model.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        {providerOptions?.message ? (
          <p role="status" className="mt-2 text-xs text-text-muted">
            {providerOptions.message}
          </p>
        ) : null}
        {modelsError ? (
          <p role="alert" className="mt-2 text-sm text-danger-foreground">
            {modelsError}
          </p>
        ) : null}
      </div>

      {messages.length === 0 ? (
        <div className="rounded-2xl border border-border-subtle bg-surface p-3 sm:p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-text-muted">
            Try asking
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {STARTER_QUESTIONS.map((starter) => (
              <button
                key={starter}
                type="button"
                onClick={() => setQuestion(starter)}
                className="rounded-xl border border-border bg-surface-muted/50 px-3 py-2 text-left text-sm text-text-body hover:border-border-accent"
              >
                {starter}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="space-y-3" aria-live="polite">
          {messages.map((message) =>
            message.role === "user" ? (
              <article
                key={message.id}
                className="ml-auto max-w-2xl rounded-2xl bg-action-primary px-4 py-3 text-sm leading-6 text-action-primary-foreground"
              >
                {message.content}
              </article>
            ) : (
              <CoachAnswer key={message.id} result={message.result} />
            ),
          )}
          {isAsking ? (
            <div role="status" className="max-w-3xl rounded-2xl border border-border-subtle bg-surface px-4 py-3 text-sm text-text-muted">
              Asking {providerLabel(provider)}…
            </div>
          ) : null}
        </div>
      )}

      {answerError ? (
        <div role="alert" className="rounded-xl bg-danger-surface px-3 py-2.5 text-sm text-danger-foreground">
          {answerError}
        </div>
      ) : null}

      <form
        onSubmit={(event) => void handleSubmit(event)}
        className="sticky bottom-[4.75rem] rounded-2xl border border-border bg-surface/95 p-3 shadow-[0_18px_45px_-26px_rgba(15,23,42,0.55)] backdrop-blur md:bottom-3 sm:p-4"
      >
        <label htmlFor="coach-question" className="sr-only">
          Ask Coach a question
        </label>
        <textarea
          id="coach-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          maxLength={1000}
          rows={3}
          placeholder="Ask about a change or pattern in your logged data…"
          className="w-full resize-none rounded-xl border border-border bg-surface px-3 py-2.5 text-sm leading-6 text-text-strong placeholder:text-text-muted focus:border-focus focus:outline-none"
        />
        <div className="mt-2 flex items-center justify-between gap-3">
          <p className="text-xs text-text-muted">
            Personal evidence and curated exercise knowledge stay separate. Answers do not change your plan or logs.
          </p>
          <button
            type="submit"
            disabled={isAsking || !question.trim() || !selectedModel}
            className="shrink-0 rounded-xl bg-action-primary px-4 py-2.5 text-sm font-semibold text-action-primary-foreground hover:bg-action-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
          >
            Ask Coach
          </button>
        </div>
      </form>
    </section>
  );
}

function CoachAnswer({ result }: { result: CoachAnswerResponse }) {
  return (
    <article className="max-w-3xl rounded-2xl border border-border-subtle bg-surface p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent-text">
          Coach
        </p>
        <span className="rounded-full bg-surface-muted px-2.5 py-1 text-[0.68rem] font-semibold text-text-muted">
          {result.confidence} confidence
        </span>
      </div>
      <p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-text-strong">
        {result.answer}
      </p>
      {result.uncertainty ? (
        <p className="mt-2 text-xs leading-5 text-text-muted">
          Uncertainty: {result.uncertainty}
        </p>
      ) : null}
      {result.suggested_action ? (
        <div className="mt-3 rounded-xl border border-border-accent bg-surface-muted/40 px-3 py-2.5">
          <p className="text-xs font-semibold text-text-strong">
            Validated progression guidance
          </p>
          <p className="mt-0.5 text-xs text-text-body">
            {progressionDecisionLabel(result.suggested_action.decision)}
          </p>
        </div>
      ) : null}

      <details className="mt-3 rounded-xl border border-border-subtle bg-surface-muted/40 px-3 py-2.5">
        <summary className="cursor-pointer text-sm font-semibold text-text-body">
          Sources used ({result.supporting_evidence.length + result.supporting_knowledge.length})
        </summary>
        <p className="mt-2 text-xs font-semibold uppercase tracking-[0.1em] text-text-muted">
          Your data and application observations
        </p>
        {result.supporting_evidence.length > 0 ? (
          <ul className="mt-2 space-y-2">
            {result.supporting_evidence.map((item) => (
              <li key={item.reference_id} className="border-l-2 border-border-accent pl-3">
                <p className="text-xs font-semibold text-text-strong">{item.label}</p>
                <p className="mt-0.5 text-xs leading-5 text-text-body">{item.fact}</p>
                <p className="mt-0.5 text-[0.68rem] text-text-muted">
                  {humanize(item.domain)} · {item.confidence}
                  {item.observed_at ? ` · ${item.observed_at}` : ""}
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-xs text-text-muted">
            No personal evidence was used for this answer.
          </p>
        )}
        <div className="mt-3 border-t border-border-subtle pt-2">
          <p className="text-xs font-semibold uppercase tracking-[0.1em] text-text-muted">
            Curated exercise knowledge
          </p>
          {result.supporting_knowledge.length > 0 ? (
            <ul className="mt-2 space-y-2">
              {result.supporting_knowledge.map((item) => (
                <li key={item.reference_id} className="border-l-2 border-border-accent pl-3">
                  <p className="text-xs font-semibold text-text-strong">
                    {item.heading}
                  </p>
                  <p className="mt-0.5 text-xs leading-5 text-text-body">
                    {item.passage}
                  </p>
                  <p className="mt-0.5 text-[0.68rem] text-text-muted">
                    {item.source_title} · {item.reference_id}
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-xs text-text-muted">
              No exercise-knowledge passage was used for this answer.
            </p>
          )}
        </div>
        {result.evidence_pack.limitations.length > 0 ? (
          <div className="mt-3 border-t border-border-subtle pt-2">
            <p className="text-xs font-semibold text-text-muted">Data limits</p>
            <ul className="mt-1 list-disc space-y-1 pl-4 text-xs text-text-muted">
              {result.evidence_pack.limitations.map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </details>

      <AIRunTelemetrySummary
        telemetry={result.telemetry}
        className="mt-3 rounded-xl border border-border-subtle bg-surface-muted/30 px-3 py-2.5"
      />
      <details className="mt-2 text-xs text-text-muted">
        <summary className="w-fit cursor-pointer select-none">Provider run</summary>
        <p className="mt-1 leading-5">
          Configured {providerLabel(result.provider_run.configured_provider)} /{" "}
          {result.provider_run.configured_model} · Selected{" "}
          {providerLabel(result.provider_run.selected_provider)} /{" "}
          {result.provider_run.selected_model} · Actual {result.provider_run.actual_model}
        </p>
      </details>
    </article>
  );
}

function buildConversationContext(
  messages: ConversationMessage[],
): CoachConversationContextTurn[] {
  return messages
    .map((message): CoachConversationContextTurn =>
      message.role === "user"
        ? { role: "user", content: message.content }
        : { role: "assistant", content: message.result.answer },
    )
    .slice(-MAX_CONTEXT_TURNS);
}

function providerLabel(provider: CoachProvider) {
  return provider === "local" ? "Local" : "OpenAI";
}

function humanize(value: string) {
  return value.replaceAll("_", " ");
}

function progressionDecisionLabel(decision: CoachSuggestedAction["decision"]) {
  return {
    hold: "Hold the current target",
    increase_load: "Increase the load",
    decrease_load: "Decrease the load",
    build_baseline: "Build a baseline",
  }[decision];
}

function messageId(role: "user" | "assistant") {
  return `${role}:${Date.now()}:${Math.random().toString(36).slice(2)}`;
}

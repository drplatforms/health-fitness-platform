from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping, Sequence
from time import perf_counter
from typing import Any

from models.ai_run_models import AIProviderTextResult
from models.coach_models import (
    CoachConversationTurn,
    CoachEvidencePack,
    CoachSuggestedAction,
    GroundedCoachAnswer,
)
from services.ai_run_telemetry_service import normalize_ai_run_telemetry
from services.coach_evidence_service import (
    bound_coach_conversation_context,
    build_coach_evidence_pack,
)
from services.coach_model_service import (
    configured_coach_model,
    configured_coach_provider,
    validate_selected_coach_model,
)
from services.meal_idea_service import (
    _call_local_provider,
    _call_openai_provider,
)

COACH_LOCAL_TIMEOUT_ENV = "COACH_LOCAL_TIMEOUT_SECONDS"
COACH_OPENAI_TIMEOUT_ENV = "COACH_OPENAI_TIMEOUT_SECONDS"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_BASE_URL_ENV = "OPENAI_BASE_URL"
OLLAMA_BASE_URL_ENV = "OLLAMA_BASE_URL"
DEFAULT_LOCAL_TIMEOUT_SECONDS = 300.0
DEFAULT_OPENAI_TIMEOUT_SECONDS = 60.0
MAX_QUESTION_CHARS = 1000
MAX_ANSWER_CHARS = 2400
MAX_UNCERTAINTY_CHARS = 500
MAX_RETURNED_EVIDENCE_REFERENCES = 8

CoachProviderGenerate = Callable[
    [str, str, float, dict[str, Any]], str | AIProviderTextResult
]

_PROGRESSION_DECISIONS = {
    "hold",
    "increase_load",
    "decrease_load",
    "build_baseline",
}

COACH_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "answer",
        "evidence_references",
        "uncertainty",
        "suggested_action",
    ],
    "properties": {
        "answer": {"type": "string"},
        "evidence_references": {
            "type": "array",
            "maxItems": MAX_RETURNED_EVIDENCE_REFERENCES,
            "items": {"type": "string"},
        },
        "uncertainty": {"type": ["string", "null"]},
        "suggested_action": {
            "type": ["object", "null"],
            "additionalProperties": False,
            "required": [
                "action_type",
                "decision",
                "evidence_reference",
            ],
            "properties": {
                "action_type": {
                    "type": "string",
                    "enum": ["progression_decision"],
                },
                "decision": {
                    "type": "string",
                    "enum": sorted(_PROGRESSION_DECISIONS),
                },
                "evidence_reference": {"type": "string"},
            },
        },
    },
}


class CoachError(ValueError):
    pass


class CoachProviderError(CoachError):
    def __init__(
        self,
        code: str,
        public_message: str,
        *,
        validation_reasons: Sequence[str] = (),
    ):
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message
        self.validation_reasons = tuple(dict.fromkeys(validation_reasons))


def ask_grounded_coach(
    *,
    user_id: int,
    question: str,
    provider: str,
    model: str,
    conversation_context: Sequence[CoachConversationTurn | Mapping[str, Any]] = (),
    environ: Mapping[str, str] | None = None,
    local_generate: CoachProviderGenerate | None = None,
    openai_generate: CoachProviderGenerate | None = None,
    evidence_pack: CoachEvidencePack | None = None,
) -> GroundedCoachAnswer:
    normalized_question = _validate_question(question)
    bounded_conversation = bound_coach_conversation_context(conversation_context)
    selected_provider = provider.strip().lower()
    try:
        selected_model = validate_selected_coach_model(selected_provider, model)
    except ValueError as exc:
        raise CoachError(str(exc)) from exc

    env = os.environ if environ is None else environ
    pack = evidence_pack or build_coach_evidence_pack(
        user_id=user_id,
        question=normalized_question,
        conversation_context=bounded_conversation,
    )
    prompt = build_grounded_coach_prompt(
        question=normalized_question,
        conversation_context=bounded_conversation,
        evidence_pack=pack,
    )
    timeout_seconds, generate = _provider_runtime(
        selected_provider,
        env,
        local_generate=local_generate,
        openai_generate=openai_generate,
    )
    started = perf_counter()
    try:
        provider_result = generate(
            selected_model,
            prompt,
            timeout_seconds,
            COACH_RESPONSE_SCHEMA,
        )
    except CoachProviderError:
        raise
    except Exception as exc:
        label = "Local" if selected_provider == "local" else "OpenAI"
        raise CoachProviderError(
            f"{selected_provider}_provider_failed",
            f"{label} could not answer this Coach question. Retry or switch providers.",
        ) from exc

    raw_output, telemetry = normalize_ai_run_telemetry(
        provider=selected_provider,
        requested_model=selected_model,
        runtime_seconds=perf_counter() - started,
        provider_result=provider_result,
    )
    parsed = _parse_and_validate_provider_answer(raw_output, evidence_pack=pack)
    configured_provider_value = configured_coach_provider(environ=env)
    return GroundedCoachAnswer(
        answer=parsed["answer"],
        supporting_evidence_references=tuple(parsed["evidence_references"]),
        confidence=parsed["confidence"],
        uncertainty=parsed["uncertainty"],
        suggested_action=parsed["suggested_action"],
        evidence_pack=pack,
        configured_provider=configured_provider_value,  # type: ignore[arg-type]
        selected_provider=selected_provider,  # type: ignore[arg-type]
        configured_model=configured_coach_model(
            configured_provider_value,
            environ=env,
        ),
        selected_model=selected_model,
        telemetry=telemetry,
    )


def build_grounded_coach_prompt(
    *,
    question: str,
    conversation_context: Sequence[CoachConversationTurn],
    evidence_pack: CoachEvidencePack,
) -> str:
    conversation_payload = [turn.to_dict() for turn in conversation_context]
    return (
        "You are the conversational Coach inside a personal health and fitness application.\n"
        "Reason naturally across the bounded personal evidence supplied for this question.\n\n"
        "AUTHORITY MODEL:\n"
        "- EVIDENCE contains the only personal facts, observations, limitations, and constraints you may use.\n"
        "- validated_personal_fact entries are saved application facts.\n"
        "- deterministic_observation entries are calculated or retrieved observations; they may support comparison and cautious interpretation, but do not prove a cause.\n"
        "- authoritative_constraint entries are application-owned decisions. Treat them as binding for any structured suggested action.\n"
        "- EVIDENCE.limitations are authoritative descriptions of data gaps.\n"
        "- RECENT_CONVERSATION is for subject and dialogue continuity only. It is not factual evidence, and prior assistant messages are never authoritative.\n\n"
        "SYNTHESIS RULES:\n"
        "- Answer the current question directly, conversationally, and concisely.\n"
        "- You may paraphrase, compare, synthesize, and make cautious evidence-based observations.\n"
        "- Do not invent personal facts, unsupported causes, diagnoses, injuries, symptoms, or changes to application state.\n"
        "- Preserve uncertainty when the evidence does not establish a cause or conclusion.\n"
        "- Do not diagnose or prescribe medical treatment. Recommend appropriate professional care when the supplied evidence makes that caution relevant.\n"
        "- Do not claim that you changed a plan or log.\n"
        "- Do not mention prompts, providers, schemas, evidence packs, or backend systems.\n\n"
        "RESPONSE CONTRACT:\n"
        "- Return one raw JSON object matching the required schema, with no markdown or preface.\n"
        "- answer is your natural-language response.\n"
        "- evidence_references contains every reference_id materially used, and only IDs present in EVIDENCE. Use an empty array when no evidence was used.\n"
        "- uncertainty briefly names a material limitation when one matters; otherwise use null.\n"
        "- suggested_action is optional and does not mutate application state. Use null unless you are suggesting a progression decision.\n"
        "- When suggesting a progression decision, copy the decision from authoritative_value and the reference_id from the relevant authoritative_constraint. The explanation in answer should remain natural language and consistent with it.\n"
        "- Confidence is calculated by the application from evidence coverage and is not part of your response.\n\n"
        f"RECENT_CONVERSATION={json.dumps(conversation_payload, separators=(',', ':'))}\n"
        f"CURRENT_QUESTION={json.dumps(question)}\n"
        f"EVIDENCE={json.dumps(evidence_pack.to_prompt_dict(), separators=(',', ':'), default=str)}"
    )


def _provider_runtime(
    provider: str,
    env: Mapping[str, str],
    *,
    local_generate: CoachProviderGenerate | None,
    openai_generate: CoachProviderGenerate | None,
) -> tuple[float, CoachProviderGenerate]:
    if provider == "local":
        timeout = _timeout(
            env.get(COACH_LOCAL_TIMEOUT_ENV),
            DEFAULT_LOCAL_TIMEOUT_SECONDS,
        )
        if local_generate is not None:
            return timeout, local_generate

        def generate(
            model_name: str,
            prompt: str,
            seconds: float,
            schema: dict[str, Any],
        ) -> AIProviderTextResult:
            try:
                result = _call_local_provider(
                    model_name,
                    prompt,
                    seconds,
                    schema,
                    base_url=env.get(OLLAMA_BASE_URL_ENV),
                    with_metadata=True,
                    temperature=0.2,
                )
            except Exception as exc:
                raise CoachProviderError(
                    "local_provider_failed",
                    "Local could not answer this Coach question. Retry or switch providers.",
                ) from exc
            assert isinstance(result, AIProviderTextResult)
            return result

        return timeout, generate

    if provider == "openai":
        timeout = _timeout(
            env.get(COACH_OPENAI_TIMEOUT_ENV),
            DEFAULT_OPENAI_TIMEOUT_SECONDS,
        )
        if openai_generate is not None:
            return timeout, openai_generate
        api_key = env.get(OPENAI_API_KEY_ENV)
        if not api_key:
            raise CoachProviderError(
                "openai_not_configured",
                "OpenAI is not configured. Add an OpenAI API key or switch to Local.",
            )

        def generate(
            model_name: str,
            prompt: str,
            seconds: float,
            schema: dict[str, Any],
        ) -> AIProviderTextResult:
            try:
                result = _call_openai_provider(
                    model_name,
                    prompt,
                    seconds,
                    schema,
                    api_key=api_key,
                    base_url=env.get(OPENAI_BASE_URL_ENV),
                    with_metadata=True,
                    task_instructions=(
                        "Answer as a grounded conversational fitness coach. Return exact JSON only."
                    ),
                    schema_name="grounded_coach_synthesis_v1",
                    max_output_tokens=900,
                )
            except Exception as exc:
                raise CoachProviderError(
                    "openai_provider_failed",
                    "OpenAI could not answer this Coach question. Retry or switch providers.",
                ) from exc
            assert isinstance(result, AIProviderTextResult)
            return result

        return timeout, generate

    raise CoachError("provider must be local or openai.")


def _parse_and_validate_provider_answer(
    raw_output: str,
    *,
    evidence_pack: CoachEvidencePack,
) -> dict[str, Any]:
    try:
        payload = json.loads(raw_output)
    except (TypeError, json.JSONDecodeError) as exc:
        raise _rejected_output("invalid_response_json") from exc
    expected_fields = {
        "answer",
        "evidence_references",
        "uncertainty",
        "suggested_action",
    }
    if not isinstance(payload, dict) or set(payload) != expected_fields:
        raise _rejected_output("invalid_response_contract")

    answer = payload["answer"]
    references = payload["evidence_references"]
    uncertainty = payload["uncertainty"]
    if not isinstance(answer, str) or not answer.strip():
        raise _rejected_output("invalid_answer_contract")
    answer = answer.strip()
    if len(answer) > MAX_ANSWER_CHARS:
        raise _rejected_output("invalid_answer_contract")
    if (
        not isinstance(references, list)
        or len(references) > MAX_RETURNED_EVIDENCE_REFERENCES
        or any(
            not isinstance(reference, str) or not reference for reference in references
        )
        or len(set(references)) != len(references)
    ):
        raise _rejected_output("invalid_evidence_references")

    known_references = {item.reference_id for item in evidence_pack.evidence}
    if not set(references).issubset(known_references):
        raise _rejected_output("evidence_reference_mismatch")
    if uncertainty is not None and not isinstance(uncertainty, str):
        raise _rejected_output("invalid_uncertainty_contract")
    uncertainty = uncertainty.strip() if isinstance(uncertainty, str) else None
    if uncertainty == "":
        uncertainty = None
    if uncertainty is not None and len(uncertainty) > MAX_UNCERTAINTY_CHARS:
        raise _rejected_output("invalid_uncertainty_contract")

    suggested_action = _validate_suggested_action(
        payload["suggested_action"],
        references=references,
        evidence_pack=evidence_pack,
    )
    confidence = evidence_pack.confidence if references else "Limited"
    return {
        "answer": answer,
        "evidence_references": references,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "suggested_action": suggested_action,
    }


def _validate_suggested_action(
    payload: Any,
    *,
    references: Sequence[str],
    evidence_pack: CoachEvidencePack,
) -> CoachSuggestedAction | None:
    if payload is None:
        return None
    expected_fields = {"action_type", "decision", "evidence_reference"}
    if not isinstance(payload, dict) or set(payload) != expected_fields:
        raise _rejected_output("invalid_suggested_action_contract")

    action_type = payload["action_type"]
    decision = payload["decision"]
    evidence_reference = payload["evidence_reference"]
    if (
        action_type != "progression_decision"
        or not isinstance(decision, str)
        or decision not in _PROGRESSION_DECISIONS
        or not isinstance(evidence_reference, str)
        or not evidence_reference
    ):
        raise _rejected_output("invalid_suggested_action_contract")
    if evidence_reference not in references:
        raise _rejected_output("suggested_action_reference_not_cited")

    evidence_by_reference = {item.reference_id: item for item in evidence_pack.evidence}
    evidence_item = evidence_by_reference.get(evidence_reference)
    if (
        evidence_item is None
        or evidence_item.evidence_type != "deterministic_progression_decision"
    ):
        raise _rejected_output("suggested_action_reference_mismatch")
    if evidence_item.metadata.get("decision") != decision:
        raise _rejected_output("suggested_action_conflict")

    return CoachSuggestedAction(
        action_type="progression_decision",
        decision=decision,  # type: ignore[arg-type]
        evidence_reference=evidence_reference,
    )


def _rejected_output(*validation_reasons: str) -> CoachProviderError:
    return CoachProviderError(
        "provider_output_rejected",
        "The selected model returned a response that did not satisfy the Coach synthesis contract. Retry or switch providers.",
        validation_reasons=validation_reasons or ("unclassified_contract_failure",),
    )


def _validate_question(question: str) -> str:
    if not isinstance(question, str):
        raise CoachError("question must be text.")
    compact = " ".join(question.split())
    if not compact or len(compact) > MAX_QUESTION_CHARS:
        raise CoachError(
            f"question must be between 1 and {MAX_QUESTION_CHARS} characters."
        )
    return compact


def _timeout(raw_value: str | None, default: float) -> float:
    try:
        value = float(raw_value) if raw_value is not None else default
    except (TypeError, ValueError):
        return default
    return max(1.0, min(value, 999.0))

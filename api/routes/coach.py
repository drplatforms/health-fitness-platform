from __future__ import annotations

import logging
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from models.coach_models import CoachConversationTurn
from services.coach_model_service import (
    build_coach_model_options,
    configured_coach_model,
    configured_coach_provider,
)
from services.grounded_coach_service import (
    MAX_ANSWER_CHARS,
    CoachError,
    CoachProviderError,
    ask_grounded_coach,
)

router = APIRouter(prefix="/coach", tags=["coach"])
logger = logging.getLogger(__name__)


class CoachConversationTurnRequest(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_ANSWER_CHARS)


class CoachAskRequest(BaseModel):
    user_id: int = Field(gt=0)
    question: str = Field(min_length=1, max_length=1000)
    provider: Literal["local", "openai"] | None = None
    model: str | None = Field(default=None, min_length=1, max_length=200)
    conversation_context: list[CoachConversationTurnRequest] = Field(
        default_factory=list
    )


@router.get("/models")
def coach_model_options():
    return build_coach_model_options()


@router.post("/ask")
def coach_ask(request: CoachAskRequest):
    provider = request.provider or configured_coach_provider()
    model = request.model or configured_coach_model(provider)
    conversation = tuple(
        CoachConversationTurn(role=turn.role, content=turn.content)
        for turn in request.conversation_context
    )
    try:
        result = ask_grounded_coach(
            user_id=request.user_id,
            question=request.question,
            provider=provider,
            model=model,
            conversation_context=conversation,
        )
    except CoachProviderError as exc:
        return _coach_error_response(
            status_code=502,
            code=exc.code,
            message=exc.public_message,
            retryable=exc.code
            in {
                "local_provider_failed",
                "openai_provider_failed",
                "provider_output_rejected",
            },
            validation_reasons=exc.validation_reasons,
            provider_diagnostics=exc.provider_diagnostics,
        )
    except CoachError:
        return _coach_error_response(
            status_code=400,
            code="invalid_coach_request",
            message="Coach could not accept this request.",
            retryable=False,
        )
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        return _coach_error_response(
            status_code=status_code,
            code=(
                "coach_context_not_found"
                if status_code == 404
                else "invalid_coach_request"
            ),
            message=(
                "The requested Coach context was not found."
                if status_code == 404
                else "Coach could not accept this request."
            ),
            retryable=False,
        )
    except Exception as exc:
        return _coach_error_response(
            status_code=500,
            code="coach_internal_error",
            message="Coach could not complete this request safely.",
            retryable=False,
            error_type=type(exc).__name__,
        )

    return result.to_public_dict()


def _coach_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    retryable: bool,
    validation_reasons: tuple[str, ...] = (),
    provider_diagnostics: dict[str, object] | None = None,
    error_type: str | None = None,
) -> JSONResponse:
    correlation_id = uuid4().hex
    sanitized_reasons = tuple(
        reason
        for reason in validation_reasons
        if reason
        and len(reason) <= 80
        and all(character.isalnum() or character in "_-" for character in reason)
    )
    sanitized_diagnostics = _sanitized_provider_diagnostics(provider_diagnostics)
    logger.warning(
        "Coach request failed correlation_id=%s code=%s status_code=%s "
        "validation_reasons=%s provider_diagnostics=%s error_type=%s",
        correlation_id,
        code,
        status_code,
        sanitized_reasons,
        sanitized_diagnostics,
        error_type,
    )
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "correlation_id": correlation_id,
                "retryable": retryable,
            },
        },
    )


def _sanitized_provider_diagnostics(
    diagnostics: dict[str, object] | None,
) -> dict[str, object]:
    if not diagnostics:
        return {}
    sanitized: dict[str, object] = {}
    for key in ("provider_status", "incomplete_reason"):
        value = diagnostics.get(key)
        if (
            isinstance(value, str)
            and len(value) <= 64
            and all(character.isalnum() or character in "_-" for character in value)
        ):
            sanitized[key] = value
    raw_output_length = diagnostics.get("raw_output_length")
    if isinstance(raw_output_length, int) and raw_output_length >= 0:
        sanitized["raw_output_length"] = raw_output_length
    return sanitized

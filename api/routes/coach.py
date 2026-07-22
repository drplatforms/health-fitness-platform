from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
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
        detail: dict[str, object] = {
            "code": exc.code,
            "message": exc.public_message,
        }
        if exc.validation_reasons:
            detail["validation_reasons"] = list(exc.validation_reasons)
        if exc.provider_diagnostics:
            detail["provider_diagnostics"] = exc.provider_diagnostics
        raise HTTPException(
            status_code=502,
            detail=detail,
        ) from exc
    except CoachError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    return result.to_public_dict()

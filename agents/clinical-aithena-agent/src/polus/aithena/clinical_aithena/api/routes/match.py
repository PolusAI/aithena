"""GARDIAN patient-trial matching endpoint.

Accepts a patient clinical note, runs the full pipeline (keyword extraction,
retrieval, matching, ranking), publishes real-time progress to RabbitMQ, and
returns the ranked trial results.

Also exposes a WebSocket endpoint at ``/ws/status/{session_id}`` that
subscribes to RabbitMQ and relays status updates to the browser.  This
avoids requiring the browser to connect directly to RabbitMQ (which may
be on a port not reachable from the client).
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from polus.aithena.clinical_aithena.api.core.database import get_sync_session
from polus.aithena.clinical_aithena.pipeline.service import match_patient
from polus.aithena.clinical_aithena.rabbit import RabbitMQPublisher

logger = logging.getLogger(__name__)

router = APIRouter(tags=["match"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class PatientDemographics(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None


class MatchRequest(BaseModel):
    """Request body for the GARDIAN patient matching endpoint."""

    clinical_note: str = Field(..., min_length=1, description="Patient clinical note")
    demographics: Optional[PatientDemographics] = None
    top_n: int = Field(default=20, ge=1, le=100, description="Number of trials to return")
    retrieval_method: str = Field(default="hybrid", pattern="^(hybrid|bm25|vector)$")
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for real-time status updates via RabbitMQ",
    )


class TrialMatchResult(BaseModel):
    nct_id: str
    title: str
    relevance_score: float
    eligibility_score: float
    relevance_explanation: str
    eligibility_explanation: str
    rank: int


class KeywordsGenerated(BaseModel):
    summary: str
    conditions: List[str]


class MatchResponse(BaseModel):
    """Response from the GARDIAN patient matching endpoint."""

    results: List[TrialMatchResult]
    total_retrieved: int
    keywords_generated: Optional[KeywordsGenerated] = None
    execution_time_ms: float


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/match", response_model=MatchResponse)
async def match_patient_endpoint(body: MatchRequest, request: Request):
    """Run the GARDIAN pipeline to match a patient to clinical trials.

    Publishes real-time progress updates to RabbitMQ (if connected) so that
    browser clients can show a live status indicator.
    """
    start_time = time.time()

    # Build the progress callback bound to this request's session_id
    publisher: Optional[RabbitMQPublisher] = getattr(request.app.state, "rabbitmq_publisher", None)

    async def _progress(status: str, message: str) -> None:
        if publisher and body.session_id:
            await publisher.publish_status(body.session_id, status, message)

    # Build patient_data dict expected by the pipeline service
    patient_data: Dict[str, Any] = {"clinical_note": body.clinical_note}
    if body.demographics:
        patient_data["demographics"] = body.demographics.model_dump(exclude_none=True)

    # Run the pipeline with a synchronous DB session
    with get_sync_session() as session:
        output = await match_patient(
            session=session,
            patient_data=patient_data,
            top_n=body.top_n,
            retrieval_method=body.retrieval_method,
            progress_callback=_progress,
        )

    results = output["results"]
    keywords = output.get("keywords")

    elapsed_ms = (time.time() - start_time) * 1000

    keywords_generated = None
    if keywords:
        keywords_generated = KeywordsGenerated(
            summary=keywords.get("summary", ""),
            conditions=keywords.get("conditions", []),
        )

    return MatchResponse(
        results=[TrialMatchResult(**r) for r in results],
        total_retrieved=len(results),
        keywords_generated=keywords_generated,
        execution_time_ms=round(elapsed_ms, 1),
    )


# ---------------------------------------------------------------------------
# WebSocket endpoint – relays RabbitMQ status updates to the browser
# ---------------------------------------------------------------------------

@router.websocket("/ws/status/{session_id}")
async def status_websocket(websocket: WebSocket, session_id: str):
    """Stream pipeline status updates to the browser over WebSocket.

    The browser connects here instead of directly to RabbitMQ, so only
    the API port (8000) needs to be reachable.
    """
    publisher: Optional[RabbitMQPublisher] = getattr(
        websocket.app.state, "rabbitmq_publisher", None
    )

    if not publisher or not publisher.is_connected:
        logger.warning("WebSocket rejected – RabbitMQ not connected")
        await websocket.close(code=1011, reason="RabbitMQ not connected")
        return

    await websocket.accept()
    logger.info("WebSocket accepted for session %s", session_id)

    try:
        async with publisher.subscribe(session_id) as queue:
            while True:
                try:
                    # Wait up to 5 minutes for a message (pipeline timeout)
                    msg = await asyncio.wait_for(queue.get(), timeout=300)
                    await websocket.send_text(msg)
                except asyncio.TimeoutError:
                    logger.info("WebSocket timeout for session %s", session_id)
                    break
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for session %s", session_id)
    except Exception:
        logger.warning(
            "WebSocket error for session %s", session_id, exc_info=True
        )

"""
FastAPI wrapper for the memory-enabled Agent.

Exposes two endpoints:
  GET  /ping        - health check
  POST /invocation  - send a query to the agent, get a response

Session management:
  ONE Agent instance is created per run_id and reused across turns in the
  same session.  Different run_ids for the same user_id demonstrate
  multi-session tracking; different user_ids demonstrate tenant isolation.
"""

import os
import uuid
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent import Agent

load_dotenv()

app = FastAPI(
    title="Memory Agent API",
    description="Multi-tenant conversational agent with semantic memory",
    version="1.0.0",
)

# Session cache: run_id -> Agent instance
# ONE Agent per session (run_id) is maintained in memory
_session_cache: Dict[str, Agent] = {}


def _get_or_create_agent(user_id: str, run_id: str) -> Agent:
    """Return the existing Agent for this session or create a new one."""
    if run_id not in _session_cache:
        _session_cache[run_id] = Agent(user_id=user_id, run_id=run_id)
    return _session_cache[run_id]


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class InvocationRequest(BaseModel):
    user_id: str = Field(..., description="User identifier for memory isolation")
    run_id: Optional[str] = Field(
        default=None,
        description="Session ID (auto-generated UUID if not provided)",
    )
    query: str = Field(..., description="User's message")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context or tags"
    )


class InvocationResponse(BaseModel):
    user_id: str
    run_id: str
    query: str
    response: str


class PingResponse(BaseModel):
    status: str
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/ping", response_model=PingResponse)
def ping():
    """Health check endpoint."""
    return PingResponse(status="ok", message="Memory Agent API is running")


@app.post("/invocation", response_model=InvocationResponse)
def invocation(request: InvocationRequest):
    """
    Main conversation endpoint.

    - Reuses the same Agent instance within a session (same run_id).
    - Creates a new Agent instance for a new session (new run_id).
    - Memory is isolated per user_id (multi-tenant).
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")

    # Auto-generate run_id if not provided
    run_id = request.run_id or str(uuid.uuid4())[:8]

    try:
        agent = _get_or_create_agent(user_id=request.user_id, run_id=run_id)
        response_text = agent.chat(request.query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return InvocationResponse(
        user_id=request.user_id,
        run_id=run_id,
        query=request.query,
        response=response_text,
    )

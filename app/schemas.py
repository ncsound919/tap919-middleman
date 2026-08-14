from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


class ExecuteRequest(BaseModel):
    model: str
    input: str
    params: Optional[Dict[str, Any]] = None


class ExecuteResponseUsage(BaseModel):
    units: float
    unit_type: str
    cost_estimate: float


class ExecuteResponse(BaseModel):
    model: str
    output: str
    usage: ExecuteResponseUsage

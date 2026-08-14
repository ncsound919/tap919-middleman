"""Tap919 Middleman API - metered agent<->provider gateway core.

Endpoints (internal rail):
  GET  /internal/models    - model catalog with pricing meta
  GET  /internal/quote     - cost preview per model
  GET  /internal/ping      - health + model list
  POST /internal/execute   - execute, meter, emit usage event

The Cloudflare Worker front (/v1/*) proxies here. Stripe meters are fed from
usage_events. See README + 120 days plan for the monetization story.
"""
from __future__ import annotations

import os
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from app import crud, telemetry
from app.adapters.mock_provider import call_mock_provider
from app.db import init_db
from app.schemas import ExecuteRequest

load_dotenv()

init_db()
telemetry.init_tracing(app=None)

app = FastAPI(title="Tap919 Middleman API", version="0.1.0")

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # noqa: E402

FastAPIInstrumentor.instrument_app(app)

PRICING = {
    "affiliate:gpt4-mini": {
        "unit_price": 0.002,
        "unit_type": "per_1k_tokens",
        "provider": "openai",
    },
    "affiliate:replicate-gpu": {
        "unit_price": 0.01,
        "unit_type": "per_1k_tokens",
        "provider": "replicate",
    },
    "tap919:blackmind-lite": {
        "unit_price": 5.0,
        "unit_type": "per_task",
        "provider": "tap919",
    },
    # Draymond fleet providers (emitted by the budget engine meter rail).
    # meter.ts maps provider -> `draymond:<slug>`; these prices apply to
    # every fleet LLM call so the E3 engine books real cost.
    "draymond:opencode": {
        "unit_price": 0.0004,
        "unit_type": "per_1k_tokens",
        "provider": "opencode",
    },
    "draymond:opencode-free": {
        "unit_price": 0.0,
        "unit_type": "per_1k_tokens",
        "provider": "opencode",
    },
    "draymond:deepseek": {
        "unit_price": 0.0014,
        "unit_type": "per_1k_tokens",
        "provider": "deepseek",
    },
    "draymond:gemini": {
        "unit_price": 0.0025,
        "unit_type": "per_1k_tokens",
        "provider": "gemini",
    },
    "draymond:openai": {
        "unit_price": 0.003,
        "unit_type": "per_1k_tokens",
        "provider": "openai",
    },
    "draymond:anthropic": {
        "unit_price": 0.015,
        "unit_type": "per_1k_tokens",
        "provider": "anthropic",
    },
    "draymond:qwen": {
        "unit_price": 0.0008,
        "unit_type": "per_1k_tokens",
        "provider": "qwen",
    },
    "draymond:litellm": {
        "unit_price": 0.001,
        "unit_type": "per_1k_tokens",
        "provider": "litellm",
    },
}

from opentelemetry import trace  # noqa: E402

tracer = trace.get_tracer(__name__)


def _resolve_price(model: str) -> dict:
    rule = crud.get_pricing_rule(crud.SessionLocal(), model)
    if rule:
        return {"unit_price": rule.unit_price, "unit_type": rule.unit_type, "provider": rule.provider}
    return PRICING.get(model)


@app.get("/internal/models")
async def list_models():
    with tracer.start_as_current_span("list_models"):
        return [{"id": k, **v} for k, v in PRICING.items()]


@app.get("/internal/quote")
async def quote(model: str):
    with tracer.start_as_current_span("quote", attributes={"model": model}):
        rule = PRICING.get(model)
        if not rule:
            raise HTTPException(status_code=404, detail="Unknown model")
        return {"model": model, **rule, "estimated_latency_ms": 200}


@app.get("/internal/ping")
async def ping():
    with tracer.start_as_current_span("ping"):
        return {
            "status": "ok",
            "models": list(PRICING.keys()),
            "timestamp": datetime.utcnow().isoformat(),
        }


@app.post("/internal/execute")
async def execute(req: ExecuteRequest, x_tenant_id: str = Header("anon")):
    with tracer.start_as_current_span(
        "execute",
        attributes={
            "model": req.model,
            "tenant_id": x_tenant_id,
            "input_length": len(req.input),
        },
    ) as span:
        if req.model not in PRICING:
            span.set_attribute("error", True)
            raise HTTPException(status_code=400, detail="Unsupported model")

        # Metered rail: when the caller supplies exact units (e.g. the Draymond
        # budget engine's meter.ts), honor them instead of mocking from input.
        params = req.params or {}
        metered_units = params.get("metered_units")
        output, tokens = call_mock_provider(req.model, req.input)

        unit_type = PRICING[req.model]["unit_type"]
        if metered_units is not None:
            units = float(metered_units)
        elif unit_type == "per_1k_tokens":
            units = tokens / 1000.0
        else:  # per_task or per_call
            units = 1.0

        cost = crud.meter_usage(
            tenant_id=x_tenant_id,
            model=req.model,
            units=units,
        )

        crud.create_usage_event(
            tenant_id=x_tenant_id,
            model=req.model,
            units=units,
            cost_estimate=cost,
            meta={
                "provider": PRICING[req.model]["provider"],
                "tokens": tokens,
            },
        )

        span.set_attributes(
            {
                "units": units,
                "cost_estimate": cost,
                "output_length": len(output),
            }
        )

        return JSONResponse(
            {
                "model": req.model,
                "output": output,
                "usage": {
                    "units": units,
                    "unit_type": unit_type,
                    "cost_estimate": cost,
                },
            }
        )

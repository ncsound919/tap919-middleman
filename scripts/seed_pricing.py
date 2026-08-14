"""Seed pricing rules into the DB so meter_usage computes non-zero cost estimates."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app import models
from app.db import SessionLocal, init_db

load_dotenv()
init_db()

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


def main() -> None:
    session: Session = SessionLocal()
    try:
        for model, rule in PRICING.items():
            existing = (
                session.query(models.PricingRule)
                .filter(models.PricingRule.model == model)
                .first()
            )
            if existing:
                existing.unit_price = rule["unit_price"]
                existing.unit_type = rule["unit_type"]
                existing.provider = rule["provider"]
            else:
                session.add(
                    models.PricingRule(
                        model=model,
                        unit_price=rule["unit_price"],
                        unit_type=rule["unit_type"],
                        provider=rule["provider"],
                    )
                )
        session.commit()
        print("Seeded pricing rules.")
    finally:
        session.close()


if __name__ == "__main__":
    main()

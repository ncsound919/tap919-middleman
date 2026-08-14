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

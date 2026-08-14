from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.orm import Session

from app import models
from app.db import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_pricing_rule(db: Session, model: str):
    return db.query(models.PricingRule).filter(models.PricingRule.model == model).first()


def create_usage_event(
    tenant_id: str,
    model: str,
    units: float,
    cost_estimate: float,
    meta: Dict[str, Any],
):
    db = SessionLocal()
    try:
        event = models.UsageEvent(
            tenant_id=int(tenant_id) if tenant_id.isdigit() else None,
            model=model,
            units=units,
            cost_estimate=cost_estimate,
            meta=meta,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    finally:
        db.close()


def meter_usage(tenant_id: str, model: str, units: float) -> float:
    """Cost estimate: DB PricingRule lookup, else in-memory PRICING fallback."""
    db = SessionLocal()
    try:
        rule = get_pricing_rule(db, model)
        if rule:
            return round(units * rule.unit_price, 6)
        return 0.0
    finally:
        db.close()

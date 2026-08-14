# tap919-middleman

**Tap919 Middleman — Monetizable, observable API gateway between agents and providers. Edge storefront + metered billing + Stripe rail.**

The **cash register and kill-switch** for the agent fleet: meter every agent call, sell credits, and make incumbents nervous about their pricing power.

## Status

FastAPI metered-billing core is **built and smoke-tested** (2026-08-14):

```
GET  /internal/models    → model catalog with pricing meta
GET  /internal/quote     → cost preview per model
GET  /internal/ping      → health + model list
POST /internal/execute   → execute, meter, emit UsageEvent (x-tenant-id header)
```

Verified: token-metered call (`affiliate:gpt4-mini` → $0.0002) and task-metered call (`tap919:blackmind-lite` → $5.00) both write usage events to SQLite.

## Run

```bash
pip install -r requirements.txt
cp .env.example .env
python -m scripts.seed_pricing   # optional: seed DB pricing rules
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs (Swagger).

## Docker

```bash
docker build -t tap919-middleman:dev .
docker run --rm -p 8000:8000 --env-file .env tap919-middleman:dev
```

## Architecture

```
Agent runtimes (Draymond Router, StreetCode, BlackMind)
      │  POST /v1/execute (via Cloudflare Worker)
      ▼
┌─────────────────────────────┐
│   Middleman (this app)       │
│  - resolve PricingRule       │
│  - meter units (tokens/task) │
│  - emit UsageEvent (OTEL)    │
│  - estimate cost             │
└──────────┬──────────────────┘
           ▼
    Stripe metered billing
    (1 product per abstract model,
     1 price per metric)
```

## The play (see `120 days` plan)

- **Phase 1:** production-grade metered API core (DONE — this scaffold)
- **Phase 2:** multi-tenant plans + Stripe usage-based billing + agent-gateway pricing page
- **Phase 3:** multi-provider routing (model IDs like `tap919:fast-gpt4`), policy engine, local-first metering → **becomes an acquisition trap**
- **Phase 4:** GMV/take-rate/embeddedness numbers for the acquisition conversation

## Next steps

1. Wire Draymond's LLM Router + Budget Engine (`llm.ts`/`workflow-budget.ts`) to emit `UsageEvent`s here.
2. Cloudflare Worker front exposing `/v1/models`, `/v1/price`, `/v1/agent/ping`, `/v1/execute`.
3. Stripe metered billing: 1 product per abstract model, 1 price per metric.

## License

MIT © 2026 Overlay Eco

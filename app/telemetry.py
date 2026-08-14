import os


def init_tracing(app=None, service_name: str = "tap919-middleman"):
    """Wire OpenTelemetry when an OTLP endpoint is configured. Fail-soft otherwise."""
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otlp_endpoint:
        print("OTEL_EXPORTER_OTLP_ENDPOINT not set - tracing disabled")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            {
                "service.name": service_name,
                "deployment.environment": os.getenv("ENV", "dev"),
            }
        )
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))
        trace.set_tracer_provider(provider)

        if app is not None:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)
        print(f"OpenTelemetry initialized -> {otlp_endpoint}")
    except Exception as exc:  # noqa: BLE001
        print(f"OpenTelemetry init failed (non-fatal): {exc}")

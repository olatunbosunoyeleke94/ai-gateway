from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
trace.set_tracer_provider(provider)

otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4318/v1/traces"
)

provider.add_span_processor(
    BatchSpanProcessor(
        otlp_exporter
    )
)

tracer = trace.get_tracer(
    "llm-gateway"
)


def get_trace_id():

    span = trace.get_current_span()

    if not span:
        return None

    ctx = span.get_span_context()

    return format(
        ctx.trace_id,
        "032x"
    )

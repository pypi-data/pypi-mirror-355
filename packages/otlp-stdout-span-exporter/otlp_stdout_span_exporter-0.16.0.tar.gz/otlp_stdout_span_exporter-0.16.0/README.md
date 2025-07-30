# OTLP Stdout Span Exporter for Python

[![PyPI version](https://img.shields.io/pypi/v/otlp-stdout-span-exporter.svg)](https://pypi.org/project/otlp-stdout-span-exporter/)

A Python span exporter that writes OpenTelemetry spans to stdout, using a custom serialization format that embeds the spans serialized as OTLP protobuf in the `payload` field. The message envelope carries metadata about the spans, such as the service name, the OTLP endpoint, and the HTTP method:

```json
{
  "__otel_otlp_stdout": "0.1.0",
  "source": "my-service",
  "endpoint": "http://localhost:4318/v1/traces",
  "method": "POST",
  "content-type": "application/x-protobuf",
  "content-encoding": "gzip",
  "headers": {
    "tenant-id": "tenant-12345",
    "custom-header": "value"
  },
  "payload": "<base64-encoded-gzipped-protobuf>",
  "base64": true,
  "level": "INFO"
}
```

Outputting telemetry data in this format directly to stdout makes the library easily usable in network constrained environments, or in environments that are particularly sensitive to the overhead of HTTP connections, such as AWS Lambda.

>[!IMPORTANT]
>This package is part of the [serverless-otlp-forwarder](https://github.com/dev7a/serverless-otlp-forwarder) project and is designed for AWS Lambda environments. While it can be used in other contexts, it's primarily tested with AWS Lambda.

## Features

- Uses OTLP Protobuf serialization for efficient encoding
- Applies GZIP compression with configurable levels
- Detects service name from environment variables
- Supports custom headers via environment variables
- Supports log level for filtering in log aggregation systems
- Supports writing to stdout or named pipe
- Consistent JSON output format
- Zero external HTTP dependencies
- Lightweight and fast

## Installation

```bash
pip install otlp-stdout-span-exporter
```

## Usage

The recommended way to use this exporter is with the standard OpenTelemetry `BatchSpanProcessor`, which provides better performance by buffering and exporting spans in batches, or, in conjunction with the [lambda-otel-lite](https://pypi.org/project/lambda-otel-lite/) package, with the `LambdaSpanProcessor`, which is particularly optimized for AWS Lambda.

You can create a simple tracer provider with the BatchSpanProcessor and the OTLPStdoutSpanExporter:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from otlp_stdout_span_exporter import OTLPStdoutSpanExporter
from otlp_stdout_span_exporter.constants import LogLevel, OutputType

# Create and set the tracer provider
provider = TracerProvider()
trace.set_tracer_provider(provider)

# Create and register the exporter with default options (stdout output)
exporter = OTLPStdoutSpanExporter(gzip_level=6)

# Or with log level for filtering
debug_exporter = OTLPStdoutSpanExporter(
    gzip_level=6,
    log_level=LogLevel.DEBUG
)

# Or with named pipe output
pipe_exporter = OTLPStdoutSpanExporter(
    output_type=OutputType.PIPE  # Will write to /tmp/otlp-stdout-span-exporter.pipe
)

provider.add_span_processor(BatchSpanProcessor(exporter))

# Your instrumentation code here
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("my-operation") as span:
    span.set_attribute("my.attribute", "value")
```


## Configuration

### Constructor Options

```python
OTLPStdoutSpanExporter(
    # GZIP compression level (0-9, where 0 is no compression and 9 is maximum compression)
    # Will be overridden by environment variable if set
    gzip_level=6,
    
    # Log level for filtering in log aggregation systems
    # If not specified, no level field will be included in the output
    log_level=LogLevel.INFO,
    
    # Output type (stdout or pipe)
    # Defaults to OutputType.STDOUT if not specified
    output_type=OutputType.STDOUT
)
```

### Environment Variables

The exporter respects the following environment variables:

- `OTEL_SERVICE_NAME`: Service name to use in output
- `AWS_LAMBDA_FUNCTION_NAME`: Fallback service name (if `OTEL_SERVICE_NAME` not set)
- `OTEL_EXPORTER_OTLP_HEADERS`: Headers for OTLP export, used in the `headers` field
- `OTEL_EXPORTER_OTLP_TRACES_HEADERS`: Trace-specific headers (which take precedence if conflicting with `OTEL_EXPORTER_OTLP_HEADERS`)
- `OTLP_STDOUT_SPAN_EXPORTER_COMPRESSION_LEVEL`: GZIP compression level (0-9). Defaults to 6.
- `OTLP_STDOUT_SPAN_EXPORTER_LOG_LEVEL`: Log level for filtering (debug, info, warn, error). If set, adds a `level` field to the output.
- `OTLP_STDOUT_SPAN_EXPORTER_OUTPUT_TYPE`: Output type ("pipe" or "stdout"). Defaults to "stdout". If set to "pipe", writes to `/tmp/otlp-stdout-span-exporter.pipe`.

>[!IMPORTANT]
>Environment variables always take precedence over constructor parameters. If both are specified, the environment variable value will be used.

>[!NOTE]
>For security best practices, avoid including authentication credentials or sensitive information in headers. The serverless-otlp-forwarder infrastructure is designed to handle authentication at the destination, rather than embedding credentials in your telemetry data.


## Output Format

The exporter writes JSON objects to stdout with the following structure:

```json
{
  "__otel_otlp_stdout": "0.1.0",
  "source": "my-service",
  "endpoint": "http://localhost:4318/v1/traces",
  "method": "POST",
  "content-type": "application/x-protobuf",
  "content-encoding": "gzip",
  "headers": {
    "tenant-id": "tenant-12345",
    "custom-header": "value"
  },
  "base64": true,
  "payload": "<base64-encoded-gzipped-protobuf>",
  "level": "INFO"
}
```

- `__otel_otlp_stdout` is a marker to identify the output of this exporter.
- `source` is the emitting service name.
- `endpoint` is the OTLP endpoint (defaults to `http://localhost:4318/v1/traces` and just indicates the signal type. The actual endpoint is determined by the process that forwards the data).
- `method` is the HTTP method (always `POST`).
- `content-type` is the content type (always `application/x-protobuf`).
- `content-encoding` is the content encoding (always `gzip`).
- `headers` is the headers defined in the `OTEL_EXPORTER_OTLP_HEADERS` and `OTEL_EXPORTER_OTLP_TRACES_HEADERS` environment variables.
- `payload` is the base64-encoded, gzipped, Protobuf-serialized span data in OTLP format.
- `base64` is a boolean flag to indicate if the payload is base64-encoded (always `true`).
- `level` is the log level (only present if configured via constructor or environment variable).

## Named Pipe Output

When configured to use named pipe output (either via constructor or environment variable), the exporter will write to `/tmp/otlp-stdout-span-exporter.pipe` instead of stdout. This can be useful in environments where you want to process the telemetry data with a separate process.

If the pipe doesn't exist or can't be written to, the exporter will automatically fall back to stdout with a warning.

## License

MIT

## See Also

- [GitHub](https://github.com/dev7a/serverless-otlp-forwarder) - The main project repository for the Serverless OTLP Forwarder project
- [GitHub](https://github.com/dev7a/serverless-otlp-forwarder/tree/main/packages/node/otlp-stdout-span-exporter) | [npm](https://www.npmjs.com/package/@dev7a/otlp-stdout-span-exporter) - The Node.js version of this exporter
- [GitHub](https://github.com/dev7a/serverless-otlp-forwarder/tree/main/packages/rust/otlp-stdout-span-exporter) | [crates.io](https://crates.io/crates/otlp-stdout-span-exporter) - The Rust version of this exporter

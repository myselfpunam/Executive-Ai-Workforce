#!/bin/sh
# Starts the local OTel Collector in the foreground (Ctrl+C to stop).
# The binary itself is gitignored (~120MB) — re-run this after cloning:
#   fetch the darwin_arm64 core "otelcol" build matching your OS/arch from
#   https://github.com/open-telemetry/opentelemetry-collector-releases/releases
#   and extract the "otelcol" binary into observation/collector/bin/
cd "$(dirname "$0")"
exec ./bin/otelcol --config=otel-collector-config.yaml

import { AIRunTelemetry } from "@/types/aiRunTelemetry";

export function AIRunTelemetrySummary({
  telemetry,
  className = "",
}: {
  telemetry: AIRunTelemetry;
  className?: string;
}) {
  return (
    <div className={`text-xs text-text-muted ${className}`.trim()}>
      <p className="font-medium">
        {providerLabel(telemetry.provider)} · {telemetry.model} ·{" "}
        {telemetry.runtime_seconds.toFixed(1)}s · {costLabel(telemetry)}
      </p>
      <details className="mt-1">
        <summary className="w-fit cursor-pointer select-none">Token details</summary>
        <p className="mt-1">
          Input {tokenLabel(telemetry.input_tokens)} · Cached{" "}
          {tokenLabel(telemetry.cached_input_tokens)} · Output{" "}
          {tokenLabel(telemetry.output_tokens)}
        </p>
      </details>
    </div>
  );
}

function providerLabel(provider: string) {
  return provider === "local" ? "Local" : provider === "openai" ? "OpenAI" : provider;
}

function costLabel(telemetry: AIRunTelemetry) {
  if (telemetry.estimated_api_cost_usd === null) {
    return "cost unavailable";
  }
  if (telemetry.provider === "local") {
    return "$0.00 API";
  }
  const digits = telemetry.estimated_api_cost_usd < 0.01 ? 4 : 2;
  return `~$${telemetry.estimated_api_cost_usd.toFixed(digits)}`;
}

function tokenLabel(value: number | null) {
  return value === null ? "unavailable" : value.toLocaleString();
}

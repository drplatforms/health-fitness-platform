export interface AIRunTelemetry {
  provider: "local" | "openai" | string;
  model: string;
  runtime_seconds: number;
  input_tokens: number | null;
  cached_input_tokens: number | null;
  output_tokens: number | null;
  estimated_api_cost_usd: number | null;
  pricing_version: string | null;
}

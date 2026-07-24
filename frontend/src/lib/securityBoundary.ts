import { createHash, timingSafeEqual } from "node:crypto";

export const MAX_PROXY_ID = 2_147_483_647;

const REMOTE_ACCESS_ENABLED_ENV = "FITNESS_REMOTE_ACCESS_ENABLED";
const BASIC_AUTH_USER_ENV = "FITNESS_BASIC_AUTH_USER";
const BASIC_AUTH_PASSWORD_ENV = "FITNESS_BASIC_AUTH_PASSWORD";
const PUBLIC_ORIGIN_ENV = "FITNESS_PUBLIC_ORIGIN";

const MUTATION_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);
const QUERY_ID_FIELDS = new Set([
  "actual_set_id",
  "canonical_food_id",
  "catalog_exercise_id",
  "entry_id",
  "food_id",
  "meal_id",
  "memory_id",
  "personal_food_id",
  "plan_instance_id",
  "planned_exercise_id",
  "raw_food_source_record_id",
  "replacement_catalog_exercise_id",
  "serving_unit_id",
  "user_id",
  "weekly_plan_id",
]);
const BODY_ID_FIELDS = QUERY_ID_FIELDS;

export type BackendRouteFamily =
  | "coach"
  | "daily-driver"
  | "exercise-catalog"
  | "foods"
  | "nutrition"
  | "recovery"
  | "users"
  | "weekly-training-plans"
  | "workout-plans";

const BACKEND_ROUTE_PREFIXES: Readonly<
  Record<BackendRouteFamily, readonly string[]>
> = {
  coach: ["coach"],
  "daily-driver": ["api"],
  "exercise-catalog": ["exercise-catalog"],
  foods: ["foods"],
  nutrition: ["nutrition"],
  recovery: ["recovery"],
  users: ["users"],
  "weekly-training-plans": ["weekly-training-plans"],
  "workout-plans": ["workout-plans"],
};

const STATIC_API_PROXY_ROUTE_FAMILIES: Readonly<
  Record<string, BackendRouteFamily>
> = {
  "/api/canonical-food-display-name": "nutrition",
  "/api/coach-ask": "coach",
  "/api/coach-models": "coach",
  "/api/daily-driver-today": "daily-driver",
  "/api/exercise-catalog": "exercise-catalog",
  "/api/foods-barcode-materialize": "foods",
  "/api/foods-barcode-resolve": "foods",
  "/api/foods-canonical-available-ingredient-starters": "foods",
  "/api/foods-canonical-browse": "foods",
  "/api/foods-canonical-search": "foods",
  "/api/nutrition-available-ingredients": "nutrition",
  "/api/nutrition-canonical-logs": "nutrition",
  "/api/nutrition-food-preferences": "nutrition",
  "/api/nutrition-food-suggestions": "nutrition",
  "/api/nutrition-log-canonical": "nutrition",
  "/api/nutrition-log-personal": "nutrition",
  "/api/nutrition-meal-idea-models": "nutrition",
  "/api/nutrition-meal-ideas": "nutrition",
  "/api/nutrition-meal-ideas/history": "nutrition",
  "/api/nutrition-meal-instructions": "nutrition",
  "/api/nutrition-personal-logs": "nutrition",
  "/api/nutrition-pinned-foods": "nutrition",
  "/api/nutrition-recent-canonical-foods": "nutrition",
  "/api/nutrition-saved-meals": "nutrition",
  "/api/personal-foods": "nutrition",
  "/api/recovery-checkin": "recovery",
  "/api/temporary-workout-limitation": "users",
  "/api/weekly-training-plans": "weekly-training-plans",
  "/api/workout-actual-sets": "workout-plans",
  "/api/workout-complete": "workout-plans",
  "/api/workout-current": "workout-plans",
  "/api/workout-exercise-history-analytics": "workout-plans",
  "/api/workout-exercise-memories": "workout-plans",
  "/api/workout-exercise-profiles": "workout-plans",
  "/api/workout-planned-vs-actual": "workout-plans",
  "/api/workout-preview": "workout-plans",
  "/api/workout-progression-decisions": "workout-plans",
  "/api/workout-progression-history": "workout-plans",
  "/api/workout-select": "workout-plans",
  "/api/workout-start": "workout-plans",
  "/api/workout-substitute": "workout-plans",
  "/api/workout-substitution-candidates": "workout-plans",
};

interface DynamicApiProxyRoute {
  readonly pattern: RegExp;
  readonly family: BackendRouteFamily;
}

const DYNAMIC_API_PROXY_ROUTES: readonly DynamicApiProxyRoute[] = [
  {
    pattern: /^\/api\/exercise-instruction\/([^/]+)$/,
    family: "exercise-catalog",
  },
  {
    pattern: /^\/api\/foods-canonical-serving-units\/([^/]+)$/,
    family: "foods",
  },
  {
    pattern: /^\/api\/nutrition-canonical-logs\/([^/]+)$/,
    family: "nutrition",
  },
  {
    pattern: /^\/api\/nutrition-personal-logs\/([^/]+)$/,
    family: "nutrition",
  },
  {
    pattern: /^\/api\/nutrition-saved-meals\/([^/]+)$/,
    family: "nutrition",
  },
  {
    pattern:
      /^\/api\/nutrition-saved-meals\/([^/]+)\/(archive|instructions|log|restore|scaled)$/,
    family: "nutrition",
  },
  {
    pattern: /^\/api\/personal-foods\/([^/]+)$/,
    family: "nutrition",
  },
  {
    pattern: /^\/api\/personal-foods\/([^/]+)\/restore$/,
    family: "nutrition",
  },
];

export class RemoteAccessConfigurationError extends Error {
  constructor() {
    super(
      "Remote access configuration is incomplete or invalid. Check the required FITNESS_* settings.",
    );
    this.name = "RemoteAccessConfigurationError";
  }
}

export type RemoteAccessConfiguration =
  | { readonly enabled: false }
  | {
      readonly enabled: true;
      readonly username: string;
      readonly password: string;
      readonly publicOrigin: string;
    };

export interface RemoteRequestDecision {
  readonly ok: boolean;
  readonly status?: 401 | 403;
  readonly code?: "authentication_required" | "origin_rejected";
}

export interface ApiProxyValidation {
  readonly ok: boolean;
  readonly status?: 400;
  readonly message?: string;
  readonly family?: BackendRouteFamily;
}

export interface SafeCoachFailure {
  readonly success: false;
  readonly error: {
    readonly code: string;
    readonly message: string;
    readonly correlation_id: string;
    readonly retryable: boolean;
  };
}

type Environment = Readonly<Record<string, string | undefined>>;

export function readRemoteAccessConfiguration(
  environment: Environment = process.env,
): RemoteAccessConfiguration {
  const enabledValue = environment[REMOTE_ACCESS_ENABLED_ENV]?.trim().toLowerCase();
  if (!enabledValue || enabledValue === "false") {
    return { enabled: false };
  }
  if (enabledValue !== "true") {
    throw new RemoteAccessConfigurationError();
  }

  const username = environment[BASIC_AUTH_USER_ENV] ?? "";
  const password = environment[BASIC_AUTH_PASSWORD_ENV] ?? "";
  const publicOriginValue = environment[PUBLIC_ORIGIN_ENV]?.trim() ?? "";

  if (
    !username ||
    username !== username.trim() ||
    username.includes(":") ||
    !password ||
    !publicOriginValue
  ) {
    throw new RemoteAccessConfigurationError();
  }

  let parsedOrigin: URL;
  try {
    parsedOrigin = new URL(publicOriginValue);
  } catch {
    throw new RemoteAccessConfigurationError();
  }

  if (
    parsedOrigin.protocol !== "https:" ||
    parsedOrigin.username ||
    parsedOrigin.password ||
    (parsedOrigin.pathname !== "/" && parsedOrigin.pathname !== "") ||
    parsedOrigin.search ||
    parsedOrigin.hash
  ) {
    throw new RemoteAccessConfigurationError();
  }

  return {
    enabled: true,
    username,
    password,
    publicOrigin: parsedOrigin.origin,
  };
}

export function authorizeRemoteRequest(
  request: Pick<Request, "headers" | "method">,
  configuration: RemoteAccessConfiguration,
): RemoteRequestDecision {
  if (!configuration.enabled) {
    return { ok: true };
  }

  if (
    !isValidBasicAuthorization(
      request.headers.get("authorization"),
      configuration.username,
      configuration.password,
    )
  ) {
    return {
      ok: false,
      status: 401,
      code: "authentication_required",
    };
  }

  if (
    MUTATION_METHODS.has(request.method.toUpperCase()) &&
    !isExpectedOrigin(
      request.headers.get("origin"),
      configuration.publicOrigin,
    )
  ) {
    return {
      ok: false,
      status: 403,
      code: "origin_rejected",
    };
  }

  return { ok: true };
}

export function parseBoundedInteger(
  value: unknown,
  minimum: number,
  maximum: number,
): number | null {
  if (
    !Number.isSafeInteger(minimum) ||
    !Number.isSafeInteger(maximum) ||
    minimum > maximum
  ) {
    throw new RangeError("Invalid integer bounds.");
  }

  if (typeof value === "number") {
    return Number.isSafeInteger(value) && value >= minimum && value <= maximum
      ? value
      : null;
  }
  if (
    typeof value !== "string" ||
    !/^(?:0|[1-9]\d*)$/.test(value) ||
    value.length > 10
  ) {
    return null;
  }

  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed >= minimum && parsed <= maximum
    ? parsed
    : null;
}

export function parsePositiveIntegerId(value: unknown): number | null {
  return parseBoundedInteger(value, 1, MAX_PROXY_ID);
}

export function encodeSafePathSegment(value: string | number): string {
  const text = String(value);
  if (
    !text ||
    text !== text.trim() ||
    text.length > 128 ||
    /[/\\?#%\u0000-\u001f\u007f]/.test(text) ||
    text === "." ||
    text === ".."
  ) {
    throw new TypeError("Unsafe backend path segment.");
  }
  return encodeURIComponent(text);
}

export function buildBackendUrl(
  baseUrl: string,
  family: BackendRouteFamily,
  pathSegments: readonly (string | number)[] = [],
  query?: URLSearchParams,
): string {
  const url = new URL(baseUrl);
  const encodedSegments = [
    ...BACKEND_ROUTE_PREFIXES[family],
    ...pathSegments,
  ].map(encodeSafePathSegment);

  url.pathname = `/${encodedSegments.join("/")}`;
  url.search = query?.toString() ?? "";
  url.hash = "";
  return url.toString();
}

export function sanitizeCoachFailure(payload: unknown): SafeCoachFailure | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const candidate = payload as Partial<SafeCoachFailure>;
  const error = candidate.error;
  if (
    candidate.success !== false ||
    !error ||
    typeof error !== "object" ||
    typeof error.code !== "string" ||
    !/^[a-z][a-z0-9_]{0,63}$/.test(error.code) ||
    typeof error.message !== "string" ||
    !error.message.trim() ||
    error.message.length > 300 ||
    typeof error.correlation_id !== "string" ||
    !/^[A-Za-z0-9-]{16,64}$/.test(error.correlation_id) ||
    typeof error.retryable !== "boolean"
  ) {
    return null;
  }

  return {
    success: false,
    error: {
      code: error.code,
      message: error.message,
      correlation_id: error.correlation_id,
      retryable: error.retryable,
    },
  };
}

export function resolveApiProxyRouteFamily(
  pathname: string,
): BackendRouteFamily | null {
  const staticFamily = STATIC_API_PROXY_ROUTE_FAMILIES[pathname];
  if (staticFamily) {
    return staticFamily;
  }

  for (const route of DYNAMIC_API_PROXY_ROUTES) {
    const match = route.pattern.exec(pathname);
    if (!match) {
      continue;
    }
    if (parsePositiveIntegerId(match[1]) === null) {
      return null;
    }
    return route.family;
  }
  return null;
}

export async function validateApiProxyRequest(
  request: Request,
): Promise<ApiProxyValidation> {
  const url = new URL(request.url);
  const family = resolveApiProxyRouteFamily(url.pathname);
  if (!family) {
    return {
      ok: false,
      status: 400,
      message: "Invalid API proxy route.",
    };
  }

  for (const [name, value] of url.searchParams.entries()) {
    if (QUERY_ID_FIELDS.has(name) && parsePositiveIntegerId(value) === null) {
      return {
        ok: false,
        status: 400,
        message: `${name} must be a positive integer.`,
      };
    }
  }

  const sessionKey = url.searchParams.get("session_key");
  if (
    sessionKey !== null &&
    (url.pathname !== "/api/workout-exercise-history-analytics" ||
      !/^[a-f0-9]{20}$/.test(sessionKey))
  ) {
    return {
      ok: false,
      status: 400,
      message: "session_key is invalid.",
    };
  }

  const foodType = url.searchParams.get("food_type");
  if (
    foodType !== null &&
    (url.pathname !== "/api/nutrition-pinned-foods" ||
      !["canonical", "personal"].includes(foodType))
  ) {
    return {
      ok: false,
      status: 400,
      message: "food_type is invalid.",
    };
  }

  if (MUTATION_METHODS.has(request.method.toUpperCase())) {
    const payload = (await request
      .clone()
      .json()
      .catch(() => null)) as Record<string, unknown> | null;
    if (payload && !Array.isArray(payload)) {
      for (const [name, value] of Object.entries(payload)) {
        if (
          BODY_ID_FIELDS.has(name) &&
          value !== undefined &&
          value !== null &&
          parsePositiveIntegerId(value) === null
        ) {
          return {
            ok: false,
            status: 400,
            message: `${name} must be a positive integer.`,
          };
        }
      }
    }
  }

  return { ok: true, family };
}

function isValidBasicAuthorization(
  authorization: string | null,
  expectedUsername: string,
  expectedPassword: string,
): boolean {
  const match = /^Basic ([A-Za-z0-9+/]+={0,2})$/i.exec(authorization ?? "");
  if (!match) {
    return false;
  }

  let decoded: string;
  try {
    decoded = Buffer.from(match[1], "base64").toString("utf8");
  } catch {
    return false;
  }

  const separator = decoded.indexOf(":");
  if (separator < 0) {
    return false;
  }
  const providedUsername = decoded.slice(0, separator);
  const providedPassword = decoded.slice(separator + 1);
  const usernameMatches = constantTimeTextEqual(
    providedUsername,
    expectedUsername,
  );
  const passwordMatches = constantTimeTextEqual(
    providedPassword,
    expectedPassword,
  );
  return usernameMatches && passwordMatches;
}

function constantTimeTextEqual(left: string, right: string): boolean {
  const leftDigest = createHash("sha256").update(left, "utf8").digest();
  const rightDigest = createHash("sha256").update(right, "utf8").digest();
  return timingSafeEqual(leftDigest, rightDigest);
}

function isExpectedOrigin(origin: string | null, expectedOrigin: string): boolean {
  if (!origin) {
    return false;
  }
  try {
    const parsed = new URL(origin);
    return origin === parsed.origin && parsed.origin === expectedOrigin;
  } catch {
    return false;
  }
}

import assert from "node:assert/strict";
import { readdir } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { unstable_doesMiddlewareMatch } from "next/dist/experimental/testing/server/middleware-testing-utils.js";

import {
  MAX_PROXY_ID,
  RemoteAccessConfigurationError,
  authorizeRemoteRequest,
  buildBackendUrl,
  encodeSafePathSegment,
  parseBoundedInteger,
  parsePositiveIntegerId,
  readRemoteAccessConfiguration,
  resolveApiProxyRouteFamily,
  sanitizeCoachFailure,
  validateApiProxyRequest,
} from "./securityBoundary.ts";

const VALID_REMOTE_ENVIRONMENT = {
  FITNESS_REMOTE_ACCESS_ENABLED: "true",
  FITNESS_BASIC_AUTH_USER: "private-user",
  FITNESS_BASIC_AUTH_PASSWORD: "private-password",
  FITNESS_PUBLIC_ORIGIN: "https://fitness.example.internal",
};

const frontendSourceRoot = fileURLToPath(new URL("../", import.meta.url));
const { registerHooks } = createRequire(import.meta.url)("node:module") as {
  registerHooks: (hooks: {
    resolve: (
      specifier: string,
      context: unknown,
      nextResolve: (specifier: string, context: unknown) => unknown,
    ) => unknown;
  }) => { deregister: () => void };
};
const moduleHooks = registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === "next/server") {
      return nextResolve("next/server.js", context);
    }
    if (specifier.startsWith("@/")) {
      const target = pathToFileURL(
        path.join(frontendSourceRoot, `${specifier.slice(2)}.ts`),
      ).href;
      return nextResolve(target, context);
    }
    return nextResolve(specifier, context);
  },
});
const { config: proxyConfig, proxy } = await import("../proxy.ts");
const { NextRequest } = await import("next/server.js");
moduleHooks.deregister();

test("localhost mode remains usable without authentication", () => {
  const configuration = readRemoteAccessConfiguration({
    FITNESS_REMOTE_ACCESS_ENABLED: "false",
  });
  const decision = authorizeRemoteRequest(
    new Request("http://127.0.0.1:3100/"),
    configuration,
  );

  assert.deepEqual(configuration, { enabled: false });
  assert.deepEqual(decision, { ok: true });
});

test("remote mode fails closed without every access-control value", () => {
  for (const missingName of [
    "FITNESS_BASIC_AUTH_USER",
    "FITNESS_BASIC_AUTH_PASSWORD",
    "FITNESS_PUBLIC_ORIGIN",
  ]) {
    const environment = { ...VALID_REMOTE_ENVIRONMENT };
    delete environment[missingName as keyof typeof environment];
    assert.throws(
      () => readRemoteAccessConfiguration(environment),
      RemoteAccessConfigurationError,
    );
  }

  assert.throws(
    () =>
      readRemoteAccessConfiguration({
        ...VALID_REMOTE_ENVIRONMENT,
        FITNESS_REMOTE_ACCESS_ENABLED: "yes",
      }),
    RemoteAccessConfigurationError,
  );
  assert.throws(
    () =>
      readRemoteAccessConfiguration({
        ...VALID_REMOTE_ENVIRONMENT,
        FITNESS_PUBLIC_ORIGIN: "http://fitness.example.internal",
      }),
    RemoteAccessConfigurationError,
  );
});

test("configuration failures never include credential values", () => {
  const privateSentinel = "PRIVATE_PASSWORD_SENTINEL";
  assert.throws(
    () =>
      readRemoteAccessConfiguration({
        ...VALID_REMOTE_ENVIRONMENT,
        FITNESS_BASIC_AUTH_PASSWORD: privateSentinel,
        FITNESS_PUBLIC_ORIGIN: "not an origin",
      }),
    (error: unknown) => {
      assert.ok(error instanceof Error);
      assert.doesNotMatch(error.message, new RegExp(privateSentinel));
      return true;
    },
  );
});

test("remote mode requires valid Basic credentials", () => {
  const configuration = readRemoteAccessConfiguration(VALID_REMOTE_ENVIRONMENT);
  const validAuthorization = `Basic ${Buffer.from(
    "private-user:private-password",
  ).toString("base64")}`;
  const wrongAuthorization = `Basic ${Buffer.from(
    "private-user:wrong-password",
  ).toString("base64")}`;

  assert.deepEqual(
    authorizeRemoteRequest(
      new Request("https://fitness.example.internal/", {
        headers: { Authorization: validAuthorization },
      }),
      configuration,
    ),
    { ok: true },
  );
  assert.deepEqual(
    authorizeRemoteRequest(
      new Request("https://fitness.example.internal/"),
      configuration,
    ),
    {
      ok: false,
      status: 401,
      code: "authentication_required",
    },
  );
  assert.deepEqual(
    authorizeRemoteRequest(
      new Request("https://fitness.example.internal/", {
        headers: { Authorization: wrongAuthorization },
      }),
      configuration,
    ),
    {
      ok: false,
      status: 401,
      code: "authentication_required",
    },
  );
});

test("remote mutations require the exact configured origin", () => {
  const configuration = readRemoteAccessConfiguration(VALID_REMOTE_ENVIRONMENT);
  const authorization = `Basic ${Buffer.from(
    "private-user:private-password",
  ).toString("base64")}`;

  for (const origin of [null, "https://evil.example", "null"]) {
    const headers = new Headers({ Authorization: authorization });
    if (origin !== null) {
      headers.set("Origin", origin);
    }
    assert.deepEqual(
      authorizeRemoteRequest(
        new Request("https://fitness.example.internal/api/coach-ask", {
          method: "POST",
          headers,
        }),
        configuration,
      ),
      { ok: false, status: 403, code: "origin_rejected" },
    );
  }

  assert.deepEqual(
    authorizeRemoteRequest(
      new Request("https://fitness.example.internal/api/coach-ask", {
        method: "POST",
        headers: {
          Authorization: authorization,
          Origin: "https://fitness.example.internal",
        },
      }),
      configuration,
    ),
    { ok: true },
  );
});

test("positive integer parsing rejects traversal and ambiguous values", () => {
  const invalidValues: unknown[] = [
    "1/../../health-state/1?ignored=",
    "1%2F..%2Fhealth-state",
    "1%5C..%5Chealth-state",
    "..",
    ".",
    "1?ignored=true",
    "1#fragment",
    " 1",
    "1 ",
    "true",
    "false",
    "1.0",
    "-1",
    "0",
    String(MAX_PROXY_ID + 1),
    true,
    false,
    1.5,
    -1,
    0,
  ];
  for (const value of invalidValues) {
    assert.equal(parsePositiveIntegerId(value), null, String(value));
  }

  assert.equal(parsePositiveIntegerId("1"), 1);
  assert.equal(parsePositiveIntegerId(MAX_PROXY_ID), MAX_PROXY_ID);
  assert.equal(parseBoundedInteger("0", 0, 10), 0);
  assert.equal(parseBoundedInteger("10", 0, 10), 10);
  assert.equal(parseBoundedInteger("11", 0, 10), null);
});

test("fixed backend construction cannot escape its allowlisted family", () => {
  const query = new URLSearchParams({ date: "2026-07-24" });
  const endpoint = new URL(
    buildBackendUrl(
      "http://127.0.0.1:8000",
      "nutrition",
      [101, "canonical-logs"],
      query,
    ),
  );

  assert.equal(endpoint.origin, "http://127.0.0.1:8000");
  assert.equal(endpoint.pathname, "/nutrition/101/canonical-logs");
  assert.equal(endpoint.searchParams.get("date"), "2026-07-24");
  assert.throws(() => encodeSafePathSegment("1/../../coach"));
  assert.throws(() => encodeSafePathSegment(".."));
  assert.throws(() =>
    buildBackendUrl("http://127.0.0.1:8000", "nutrition", [
      "1%2F..%2Fcoach",
    ]),
  );
});

test("representative GET traversal is rejected before backend dispatch", async () => {
  let backendFetchCalls = 0;
  const dispatch = async (request: Request) => {
    const validation = await validateApiProxyRequest(request);
    if (!validation.ok) {
      return validation;
    }
    backendFetchCalls += 1;
    return validation;
  };

  const traversal = await dispatch(
    new Request(
      "http://127.0.0.1:3100/api/nutrition-canonical-logs?user_id=1%2F..%2F..%2Fhealth-state%2F1%3Fignored%3D&date=2026-07-24",
    ),
  );
  assert.equal(traversal.ok, false);
  assert.equal(traversal.status, 400);
  assert.equal(backendFetchCalls, 0);

  const valid = await dispatch(
    new Request(
      "http://127.0.0.1:3100/api/nutrition-canonical-logs?user_id=101&date=2026-07-24",
    ),
  );
  assert.equal(valid.ok, true);
  assert.equal(valid.family, "nutrition");
  assert.equal(backendFetchCalls, 1);
});

test("representative POST traversal is rejected before backend dispatch", async () => {
  let backendFetchCalls = 0;
  const dispatch = async (request: Request) => {
    const validation = await validateApiProxyRequest(request);
    if (!validation.ok) {
      return validation;
    }
    backendFetchCalls += 1;
    return validation;
  };

  const invalid = await dispatch(
    new Request("http://127.0.0.1:3100/api/nutrition-log-canonical", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: "1/../../coach/models",
        canonical_food_id: 7,
        grams: 100,
      }),
    }),
  );
  assert.equal(invalid.ok, false);
  assert.equal(invalid.status, 400);
  assert.equal(backendFetchCalls, 0);

  const valid = await dispatch(
    new Request("http://127.0.0.1:3100/api/nutrition-log-canonical", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: 101,
        canonical_food_id: 7,
        grams: 100,
      }),
    }),
  );
  assert.equal(valid.ok, true);
  assert.equal(valid.family, "nutrition");
  assert.equal(backendFetchCalls, 1);
});

test("dynamic proxy IDs and opaque session keys are strict", async () => {
  assert.equal(
    resolveApiProxyRouteFamily("/api/nutrition-saved-meals/7"),
    "nutrition",
  );
  assert.equal(
    resolveApiProxyRouteFamily(
      "/api/nutrition-saved-meals/1%2F..%2Fcoach/restore",
    ),
    null,
  );
  assert.equal(
    (
      await validateApiProxyRequest(
        new Request(
          "http://127.0.0.1:3100/api/workout-exercise-history-analytics?user_id=101&session_key=abc/../../coach",
        ),
      )
    ).ok,
    false,
  );
  assert.equal(
    (
      await validateApiProxyRequest(
        new Request(
          "http://127.0.0.1:3100/api/workout-exercise-history-analytics?user_id=101&session_key=0123456789abcdefabcd",
        ),
      )
    ).ok,
    true,
  );
});

test("Coach proxy errors preserve only the safe public contract", () => {
  const privateSentinel = "PRIVATE_PROVIDER_OUTPUT_SENTINEL";
  const sanitized = sanitizeCoachFailure({
    success: false,
    error: {
      code: "provider_output_rejected",
      message: "Coach could not complete this request safely.",
      correlation_id: "0123456789abcdef0123456789abcdef",
      retryable: false,
      provider_diagnostics: { raw_output_preview: privateSentinel },
    },
    prompt: privateSentinel,
    evidence_pack: privateSentinel,
  });

  assert.deepEqual(sanitized, {
    success: false,
    error: {
      code: "provider_output_rejected",
      message: "Coach could not complete this request safely.",
      correlation_id: "0123456789abcdef0123456789abcdef",
      retryable: false,
    },
  });
  assert.doesNotMatch(JSON.stringify(sanitized), new RegExp(privateSentinel));
  assert.equal(
    sanitizeCoachFailure({
      success: false,
      error: {
        code: "provider_output_rejected",
        message: privateSentinel.repeat(40),
        correlation_id: "0123456789abcdef0123456789abcdef",
        retryable: false,
      },
    }),
    null,
  );
});

test("every Next API route is covered by the explicit family allowlist", async () => {
  const apiRoot = fileURLToPath(new URL("../app/api", import.meta.url));
  const routeFiles = await findRouteFiles(apiRoot);

  for (const routeFile of routeFiles) {
    const relativeDirectory = path.relative(apiRoot, path.dirname(routeFile));
    const requestPath = `/api/${relativeDirectory
      .split(path.sep)
      .map((segment) => (/^\[[^\]]+\]$/.test(segment) ? "1" : segment))
      .join("/")}`;
    assert.notEqual(
      resolveApiProxyRouteFamily(requestPath),
      null,
      `Missing proxy family policy for ${requestPath}`,
    );
  }
});

test("the actual Next matcher protects API and dynamic application routes", () => {
  for (const pathname of [
    "/api/personal-foods/7.js",
    "/api/nutrition-saved-meals/7.png",
    "/personal-foods/7.js",
    "/personal-foods/profile.svg",
    "/coach",
  ]) {
    assert.equal(doesProxyMatch(pathname), true, pathname);
  }

  for (const pathname of [
    "/_next/static/chunks/app.js",
    "/_next/image",
    "/exercise-media/free-exercise-db/push-up/start.jpg",
    "/favicon.ico",
    "/file.svg",
    "/globe.svg",
    "/next.svg",
    "/vercel.svg",
    "/window.svg",
  ]) {
    assert.equal(doesProxyMatch(pathname), false, pathname);
  }

  assert.equal(doesProxyMatch("/private/file.svg"), true);
  assert.equal(doesProxyMatch("/file.svg/details"), true);
  assert.equal(doesProxyMatch("/api/file.svg"), true);
});

test("the Proxy challenges remote requests and rejects mutations before dispatch", async () => {
  const environmentNames = Object.keys(VALID_REMOTE_ENVIRONMENT);
  const previousEnvironment = Object.fromEntries(
    environmentNames.map((name) => [name, process.env[name]]),
  );
  Object.assign(process.env, VALID_REMOTE_ENVIRONMENT);

  const validAuthorization = `Basic ${Buffer.from(
    "private-user:private-password",
  ).toString("base64")}`;
  const wrongAuthorization = `Basic ${Buffer.from(
    "private-user:wrong-password",
  ).toString("base64")}`;
  let backendDispatches = 0;
  const dispatch = async (request: InstanceType<typeof NextRequest>) => {
    const response = await proxy(request);
    if (response.headers.get("x-middleware-next") === "1") {
      backendDispatches += 1;
    }
    return response;
  };

  try {
    const missingCredentials = await dispatch(
      new NextRequest(
        "https://fitness.example.internal/api/personal-foods/7.js?user_id=101",
      ),
    );
    assert.equal(missingCredentials.status, 401);
    assert.equal(
      missingCredentials.headers.get("WWW-Authenticate"),
      'Basic realm="Fitness", charset="UTF-8"',
    );

    const invalidCredentials = await dispatch(
      new NextRequest(
        "https://fitness.example.internal/api/personal-foods/7?user_id=101",
        { headers: { Authorization: wrongAuthorization } },
      ),
    );
    assert.equal(invalidCredentials.status, 401);

    const missingOrigin = await dispatch(
      new NextRequest(
        "https://fitness.example.internal/api/personal-foods/7",
        {
          method: "PATCH",
          headers: {
            Authorization: validAuthorization,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ user_id: 101 }),
        },
      ),
    );
    assert.equal(missingOrigin.status, 403);
    assert.equal(backendDispatches, 0);

    const validRequest = await dispatch(
      new NextRequest(
        "https://fitness.example.internal/api/personal-foods/7",
        {
          method: "PATCH",
          headers: {
            Authorization: validAuthorization,
            "Content-Type": "application/json",
            Origin: "https://fitness.example.internal",
          },
          body: JSON.stringify({ user_id: 101 }),
        },
      ),
    );
    assert.equal(validRequest.status, 200);
    assert.equal(validRequest.headers.get("x-middleware-next"), "1");
    assert.equal(backendDispatches, 1);
  } finally {
    for (const name of environmentNames) {
      const previousValue = previousEnvironment[name];
      if (previousValue === undefined) {
        delete process.env[name];
      } else {
        process.env[name] = previousValue;
      }
    }
  }
});

function doesProxyMatch(pathname: string): boolean {
  return unstable_doesMiddlewareMatch({
    config: proxyConfig,
    url: `https://fitness.example.internal${pathname}`,
  });
}

async function findRouteFiles(directory: string): Promise<string[]> {
  const entries = await readdir(directory, { withFileTypes: true });
  const files: string[] = [];
  for (const entry of entries) {
    const candidate = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await findRouteFiles(candidate)));
    } else if (entry.name === "route.ts") {
      files.push(candidate);
    }
  }
  return files;
}

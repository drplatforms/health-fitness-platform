import assert from "node:assert/strict";
import { createRequire } from "node:module";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const frontendSourceRoot = fileURLToPath(new URL("../", import.meta.url));
const dailyDriverApiTestModule = `data:text/javascript,${encodeURIComponent(
  "export function getApiBaseUrl() { return 'http://127.0.0.1:8000'; }",
)}`;
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
    if (specifier === "@/lib/dailyDriverApi") {
      return { url: dailyDriverApiTestModule, shortCircuit: true };
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

const { NextRequest } = await import("next/server.js");
const canonicalLogRoute = await import(
  "../app/api/nutrition-canonical-logs/[entryId]/route.ts"
);
const personalLogRoute = await import(
  "../app/api/nutrition-personal-logs/[entryId]/route.ts"
);
const personalFoodRoute = await import(
  "../app/api/personal-foods/[personalFoodId]/route.ts"
);
const personalFoodRestoreRoute = await import(
  "../app/api/personal-foods/[personalFoodId]/restore/route.ts"
);
const savedMealRoute = await import(
  "../app/api/nutrition-saved-meals/[mealId]/route.ts"
);
const savedMealArchiveRoute = await import(
  "../app/api/nutrition-saved-meals/[mealId]/archive/route.ts"
);
const savedMealInstructionsRoute = await import(
  "../app/api/nutrition-saved-meals/[mealId]/instructions/route.ts"
);
const savedMealLogRoute = await import(
  "../app/api/nutrition-saved-meals/[mealId]/log/route.ts"
);
const savedMealRestoreRoute = await import(
  "../app/api/nutrition-saved-meals/[mealId]/restore/route.ts"
);
moduleHooks.deregister();

const FRONTEND_ORIGIN = "http://127.0.0.1:3100";
const INVALID_ID = "7.js";

test("every corrected dynamic handler rejects invalid route IDs before fetch", async () => {
  const cases = [
    {
      name: "personal food GET",
      invoke: () =>
        personalFoodRoute.GET(
          new NextRequest(
            `${FRONTEND_ORIGIN}/api/personal-foods/${INVALID_ID}?user_id=101`,
          ),
          personalFoodContext(INVALID_ID),
        ),
    },
    {
      name: "personal food PATCH",
      invoke: () =>
        personalFoodRoute.PATCH(
          jsonRequest(
            `${FRONTEND_ORIGIN}/api/personal-foods/${INVALID_ID}`,
            "PATCH",
            { user_id: 101, name: "Private food" },
          ),
          personalFoodContext(INVALID_ID),
        ),
    },
    {
      name: "personal food DELETE",
      invoke: () =>
        personalFoodRoute.DELETE(
          new NextRequest(
            `${FRONTEND_ORIGIN}/api/personal-foods/${INVALID_ID}?user_id=101`,
            { method: "DELETE" },
          ),
          personalFoodContext(INVALID_ID),
        ),
    },
    {
      name: "personal food restore POST",
      invoke: () =>
        personalFoodRestoreRoute.POST(
          jsonRequest(
            `${FRONTEND_ORIGIN}/api/personal-foods/${INVALID_ID}/restore`,
            "POST",
            { user_id: 101 },
          ),
          personalFoodContext(INVALID_ID),
        ),
    },
    {
      name: "canonical log PATCH",
      invoke: () =>
        canonicalLogRoute.PATCH(
          jsonRequest(
            `${FRONTEND_ORIGIN}/api/nutrition-canonical-logs/${INVALID_ID}`,
            "PATCH",
            { user_id: 101, grams: 120 },
          ),
          entryContext(INVALID_ID),
        ),
    },
    {
      name: "canonical log DELETE",
      invoke: () =>
        canonicalLogRoute.DELETE(
          new NextRequest(
            `${FRONTEND_ORIGIN}/api/nutrition-canonical-logs/${INVALID_ID}?user_id=101&date=2026-07-24`,
            { method: "DELETE" },
          ),
          entryContext(INVALID_ID),
        ),
    },
    {
      name: "personal log PATCH",
      invoke: () =>
        personalLogRoute.PATCH(
          jsonRequest(
            `${FRONTEND_ORIGIN}/api/nutrition-personal-logs/${INVALID_ID}`,
            "PATCH",
            { user_id: 101, grams: 120 },
          ),
          entryContext(INVALID_ID),
        ),
    },
    {
      name: "personal log DELETE",
      invoke: () =>
        personalLogRoute.DELETE(
          new NextRequest(
            `${FRONTEND_ORIGIN}/api/nutrition-personal-logs/${INVALID_ID}?user_id=101&date=2026-07-24`,
            { method: "DELETE" },
          ),
          entryContext(INVALID_ID),
        ),
    },
    {
      name: "saved meal GET",
      invoke: () =>
        savedMealRoute.GET(
          new NextRequest(
            `${FRONTEND_ORIGIN}/api/nutrition-saved-meals/${INVALID_ID}?user_id=101`,
          ),
          mealContext(INVALID_ID),
        ),
    },
    {
      name: "saved meal PATCH",
      invoke: () =>
        savedMealRoute.PATCH(
          jsonRequest(
            `${FRONTEND_ORIGIN}/api/nutrition-saved-meals/${INVALID_ID}`,
            "PATCH",
            { user_id: 101, name: "Dinner" },
          ),
          mealContext(INVALID_ID),
        ),
    },
    {
      name: "saved meal DELETE",
      invoke: () =>
        savedMealRoute.DELETE(
          jsonRequest(
            `${FRONTEND_ORIGIN}/api/nutrition-saved-meals/${INVALID_ID}`,
            "DELETE",
            { user_id: 101 },
          ),
          mealContext(INVALID_ID),
        ),
    },
    {
      name: "saved meal archive POST",
      invoke: () =>
        savedMealArchiveRoute.POST(
          jsonRequest(
            `${FRONTEND_ORIGIN}/api/nutrition-saved-meals/${INVALID_ID}/archive`,
            "POST",
            { user_id: 101 },
          ),
          mealContext(INVALID_ID),
        ),
    },
    {
      name: "saved meal instructions POST",
      invoke: () =>
        savedMealInstructionsRoute.POST(
          jsonRequest(
            `${FRONTEND_ORIGIN}/api/nutrition-saved-meals/${INVALID_ID}/instructions`,
            "POST",
            { user_id: 101, provider: "configured-provider" },
          ),
          mealContext(INVALID_ID),
        ),
    },
    {
      name: "saved meal log POST",
      invoke: () =>
        savedMealLogRoute.POST(
          jsonRequest(
            `${FRONTEND_ORIGIN}/api/nutrition-saved-meals/${INVALID_ID}/log`,
            "POST",
            { user_id: 101, entry_date: "2026-07-24" },
          ),
          mealContext(INVALID_ID),
        ),
    },
    {
      name: "saved meal restore POST",
      invoke: () =>
        savedMealRestoreRoute.POST(
          jsonRequest(
            `${FRONTEND_ORIGIN}/api/nutrition-saved-meals/${INVALID_ID}/restore`,
            "POST",
            { user_id: 101 },
          ),
          mealContext(INVALID_ID),
        ),
    },
  ] satisfies readonly { name: string; invoke: () => Promise<Response> }[];

  const originalFetch = globalThis.fetch;
  let backendFetches = 0;
  globalThis.fetch = (async () => {
    backendFetches += 1;
    throw new Error("Invalid route parameters must not reach fetch.");
  }) as typeof fetch;

  try {
    for (const handlerCase of cases) {
      const fetchesBefore = backendFetches;
      const response = await handlerCase.invoke();
      assert.equal(response.status, 400, handlerCase.name);
      assert.equal(backendFetches, fetchesBefore, handlerCase.name);
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("a valid personal-food ID dispatches once to the fixed nutrition route", async () => {
  const originalFetch = globalThis.fetch;
  const dispatchedUrls: string[] = [];
  globalThis.fetch = (async (input: string | URL | Request) => {
    dispatchedUrls.push(String(input));
    return Response.json({ id: 7 });
  }) as typeof fetch;

  try {
    const response = await personalFoodRoute.GET(
      new NextRequest(
        `${FRONTEND_ORIGIN}/api/personal-foods/7?user_id=101`,
      ),
      personalFoodContext("7"),
    );

    assert.equal(response.status, 200);
    assert.equal(dispatchedUrls.length, 1);
    const backendUrl = new URL(dispatchedUrls[0]);
    assert.equal(backendUrl.origin, "http://127.0.0.1:8000");
    assert.equal(backendUrl.pathname, "/nutrition/101/personal-foods/7");
    assert.equal(backendUrl.search, "");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

function jsonRequest(
  url: string,
  method: "POST" | "PATCH" | "DELETE",
  body: Record<string, unknown>,
) {
  return new NextRequest(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function personalFoodContext(personalFoodId: string) {
  return { params: Promise.resolve({ personalFoodId }) };
}

function entryContext(entryId: string) {
  return { params: Promise.resolve({ entryId }) };
}

function mealContext(mealId: string) {
  return { params: Promise.resolve({ mealId }) };
}

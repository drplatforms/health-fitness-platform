import nextEnv from "@next/env";

const { loadEnvConfig } = nextEnv;
loadEnvConfig(process.cwd());

const requireRemote = process.argv.includes("--require-remote");

try {
  const configuration = validateRemoteAccessEnvironment(
    process.env,
    requireRemote,
  );
  if (configuration.enabled) {
    console.warn(
      `WARNING: private single-user remote access is enabled for ${configuration.publicOrigin}.`,
    );
  }
} catch {
  console.error(
    "Remote access configuration is incomplete or invalid. Check the required FITNESS_* settings.",
  );
  process.exitCode = 1;
}

export function validateRemoteAccessEnvironment(environment, remoteRequired = false) {
  const enabledValue = environment.FITNESS_REMOTE_ACCESS_ENABLED
    ?.trim()
    .toLowerCase();
  if (!enabledValue || enabledValue === "false") {
    if (remoteRequired) {
      throw new Error("Remote access must be enabled for shared mode.");
    }
    return { enabled: false };
  }
  if (enabledValue !== "true") {
    throw new Error("Remote access enablement must be true or false.");
  }

  const username = environment.FITNESS_BASIC_AUTH_USER ?? "";
  const password = environment.FITNESS_BASIC_AUTH_PASSWORD ?? "";
  const originValue = environment.FITNESS_PUBLIC_ORIGIN?.trim() ?? "";
  if (
    !username ||
    username !== username.trim() ||
    username.includes(":") ||
    !password ||
    !originValue
  ) {
    throw new Error("Required remote access settings are missing.");
  }

  const origin = new URL(originValue);
  if (
    origin.protocol !== "https:" ||
    origin.username ||
    origin.password ||
    (origin.pathname !== "/" && origin.pathname !== "") ||
    origin.search ||
    origin.hash
  ) {
    throw new Error("The public origin must be an HTTPS origin.");
  }

  return { enabled: true, publicOrigin: origin.origin };
}

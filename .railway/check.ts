/**
 * Offline smoke test for railway.ts.
 *
 * Evaluates the program the way the Railway CLI does (Node with type stripping)
 * and asserts the invariants a `railway config plan` cannot check for us:
 * unique resources, every runnable service has a start command, GitHub sources
 * pin the production branch, function bodies round-trip to ./functions, no
 * secret-looking variable is committed as a literal value, a variable named like
 * a shared variable is a `${{shared.NAME}}` reference to it, every variable a
 * service declares is mentioned somewhere in the code that service runs, and every
 * service loads its enumerated secrets from Doppler at boot.
 *
 * Run from this directory: npm run check
 */
import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readdirSync, readFileSync, realpathSync, rmSync, statSync, writeFileSync } from "node:fs";
import { stripTypeScriptTypes } from "node:module";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createRailwayContext, project, type ResourceNode } from "railway/iac";
import program, { buildFunctionSource, SHARED_VARIABLES } from "./railway.ts";

const EXPECTED_BRANCH = "develop";
const SECRET_NAME = /KEY|SECRET|PASSWORD|TOKEN/;
const REPO_ROOT = join(import.meta.dirname, "..");

/** Read by a runtime rather than by our code, so no source file names them. */
const RUNTIME_VARIABLES: ReadonlySet<string> = new Set(["PYTHONUNBUFFERED"]);

const SKIPPED_DIRS: ReadonlySet<string> = new Set(["node_modules", "__pycache__", ".next", "dist", "tests"]);
const isSkippedFile = (name: string): boolean =>
  name.endsWith(".md") || name.startsWith(".env") || name.endsWith(".test.ts") || name.startsWith("test_");

/**
 * Concatenated source of every file under `root`, following symlinks (the Python
 * services reach shared code through them). Returns the file count too, so an
 * empty scan fails instead of passing.
 */
const readSourceTree = (root: string): { text: string; files: number } => {
  const visited = new Set<string>();
  const chunks: string[] = [];
  const walk = (path: string): void => {
    const real = realpathSync(path);
    if (visited.has(real)) {
      return;
    }
    visited.add(real);
    if (statSync(real).isDirectory()) {
      for (const entry of readdirSync(real)) {
        if (!SKIPPED_DIRS.has(entry)) {
          walk(join(path, entry));
        }
      }
    } else if (!isSkippedFile(path.split("/").pop() ?? "")) {
      chunks.push(readFileSync(real, "utf8"));
    }
  };
  walk(root);
  return { text: chunks.join("\n"), files: chunks.length };
};

/**
 * Source of a Python service: the files its `api.py` entry point imports,
 * transitively (python-import-closure.py). Scanning the whole directory instead
 * would count a symlinked shared file the service never imports.
 */
const readPythonClosure = (entry: string): { text: string; files: number } => {
  const files = execFileSync("python3", [join(import.meta.dirname, "python-import-closure.py"), entry], {
    encoding: "utf8",
  })
    .split("\n")
    .filter((line) => line.length > 0);
  return { text: files.map((file) => readFileSync(file, "utf8")).join("\n"), files: files.length };
};

/** A function's own source file, named after the service. */
const functionFileOf = (resource: ResourceNode & { type: "service" }): string => `${resource.name.toLowerCase()}.ts`;

/** The absolute path of a function's own source file. */
const functionPathOf = (resource: ResourceNode & { type: "service" }): string =>
  join(import.meta.dirname, "functions", functionFileOf(resource));

/** The code a service runs: its function file, or the directory its deploys watch. */
const codeRootOf = (resource: ResourceNode & { type: "service" }): string | undefined => {
  if (resource.kind === "function") {
    return functionPathOf(resource);
  }
  const pattern = resource.build?.watchPatterns?.[0];
  return pattern ? join(REPO_ROOT, pattern.replace(/^\//, "").replace(/\/\*\*$/, "")) : undefined;
};

/**
 * Best effort: drop comments so a commented-out call never counts. Python loses its
 * `#` lines (docstrings stay); TS loses block and line comments, keeping a `//` after
 * `:` (a URL in a string).
 */
const stripComments = (text: string, isPython: boolean): string =>
  isPython
    ? text.replace(/^\s*#.*$/gm, "")
    : text.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

/**
 * How each language's entry point must call its Doppler loader. TS awaits it (or the
 * server and secret reads race it); a cron awaits it inside `main`, so the TS rule
 * cannot require top level. Python calls it at module level, not inside a function
 * that may never run.
 */
/** A Python service's fail-closed INTERNAL_API_KEY verifier, built at module level. */
const INTERNAL_API_KEY_VERIFIER =
  /^verify_internal_api_key = make_internal_api_key_verifier\(require_internal_api_key\(\)\)$/m;

const LOADER_CALL_RULES = {
  python: { pattern: /^load_doppler_secrets\(DOPPLER_SECRETS\)/m, rule: "call load_doppler_secrets(DOPPLER_SECRETS) at module level" },
  typescript: { pattern: /\bawait\s+loadDopplerSecrets\(DOPPLER_SECRETS\)/, rule: "await loadDopplerSecrets(DOPPLER_SECRETS)" },
} as const;

/** The file whose top-level code starts the service: a function's own file, else index.ts or api.py. */
const entryPointOf = (resource: ResourceNode & { type: "service" }, codeRoot: string): string => {
  if (resource.kind === "function") {
    return functionPathOf(resource);
  }
  const pythonEntry = join(codeRoot, "api.py");
  return existsSync(pythonEntry) ? pythonEntry : join(codeRoot, "src", "index.ts");
};

/**
 * The sorted names in an entry point's DOPPLER_SECRETS list or tuple, or null when
 * there is none. Stopping at the first `)` or `]` is safe: a secret name holds neither.
 */
const parseDopplerSecrets = (text: string): string[] | null => {
  const match = /\bDOPPLER_SECRETS\s*=\s*[[(]([^\])]*)[\])]/.exec(text);
  return match ? [...match[1].matchAll(/["']([^"']+)["']/g)].map((m) => m[1]).sort() : null;
};

/**
 * Parse each function as it ships (loader + file), so a syntax error or a clashing
 * top-level name (an early SyntaxError) fails here instead of on Railway. Types are
 * stripped first because `node --check` parses JavaScript only.
 */
const checkFunctionParses = (file: string): string | null => {
  const dir = mkdtempSync(join(tmpdir(), "railway-fn-"));
  try {
    const path = join(dir, "function.mjs");
    writeFileSync(path, stripTypeScriptTypes(buildFunctionSource(file).toString("utf8")));
    execFileSync(process.execPath, ["--check", path], { stdio: "pipe" });
    return null;
  } catch (error) {
    const stderr = (error as { stderr?: Buffer }).stderr?.toString() ?? "";
    return stderr.split("\n").find((line) => line.includes("Error")) ?? String(error);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
};

const definition = await program(
  createRailwayContext({ command: "check", environment: "production", projectName: "WhichGLP" }),
  project,
);
const resources = (definition.resources ?? []) as ResourceNode[];

const failures: string[] = [];
const fail = (message: string): void => {
  failures.push(message);
};

const seen = new Set<string>();
for (const resource of resources) {
  if (seen.has(resource.address)) {
    fail(`duplicate resource ${resource.address}`);
  }
  seen.add(resource.address);
}

for (const resource of resources) {
  if (resource.type !== "service") {
    continue;
  }
  const start = resource.deploy?.startCommand;
  if (!start) {
    fail(`${resource.address} has no start command`);
  }
  if (resource.source?.type === "github" && resource.source.branch !== EXPECTED_BRANCH) {
    fail(`${resource.address} deploys branch ${resource.source.branch ?? "(unset)"}, expected ${EXPECTED_BRANCH}`);
  }
  if (resource.kind === "function") {
    const encoded = start?.startsWith("./run.sh ") ? start.slice("./run.sh ".length) : "";
    const file = functionFileOf(resource);
    const expected = buildFunctionSource(file);
    if (!encoded || Buffer.from(encoded, "base64").compare(expected) !== 0) {
      fail(`${resource.address} start command does not encode functions/_doppler-secrets.ts + functions/${file}`);
    }
    if (!resource.deploy?.cronSchedule) {
      fail(`${resource.address} has no cron schedule`);
    }
    const parseError = checkFunctionParses(file);
    if (parseError) {
      fail(`${resource.address} does not parse as shipped (loader + functions/${file}): ${parseError}`);
    }
  }
  for (const [name, value] of Object.entries(resource.variables ?? {})) {
    if (value.type === "literal" && SECRET_NAME.test(name)) {
      fail(`${resource.address} commits ${name} as a literal; use preserve()`);
    }
    if (value.type === "sharedReference") {
      if (value.name !== name) {
        fail(
          `${resource.address} sets ${name} from shared.${value.name}; a shared reference must keep the variable's own name`,
        );
      } else if (!SHARED_VARIABLES.has(name)) {
        fail(`${resource.address} references shared.${name}, which is not in SHARED_VARIABLES`);
      }
    } else if (SHARED_VARIABLES.has(name)) {
      fail(
        `${resource.address} declares ${name} as ${value.type}; it is a shared variable, so reference it as \${{shared.${name}}}`,
      );
    }
  }

  const codeRoot = codeRootOf(resource);
  if (!codeRoot) {
    fail(`${resource.address} has no code location (watch pattern or function file) to check its variables against`);
    continue;
  }
  const pythonEntry = join(codeRoot, "api.py");
  const source =
    resource.kind === "function"
      ? { text: buildFunctionSource(functionFileOf(resource)).toString("utf8"), files: 2 }
      : existsSync(pythonEntry)
        ? readPythonClosure(pythonEntry)
        : readSourceTree(codeRoot);
  if (source.files === 0) {
    fail(`${resource.address} code location ${codeRoot} holds no files`);
    continue;
  }
  for (const name of Object.keys(resource.variables ?? {})) {
    if (!RUNTIME_VARIABLES.has(name) && !new RegExp(`\\b${name}\\b`).test(source.text)) {
      fail(`${resource.address} declares ${name}, which its code (${codeRoot}) never reads; remove it`);
    }
  }
  // Every backend service loads its own enumerated secrets from Doppler at boot, in
  // its entry point (comments stripped), with a non-empty DOPPLER_SECRETS list that
  // equals its shared references, secret or not (minus the Doppler access variables).
  const entry = entryPointOf(resource, codeRoot);
  const isPython = entry.endsWith(".py");
  const entryText = stripComments(readFileSync(entry, "utf8"), isPython);
  const { pattern, rule } = LOADER_CALL_RULES[isPython ? "python" : "typescript"];
  const call = pattern.exec(entryText);
  if (!call) {
    fail(`${resource.address} must ${rule} (${entry})`);
  } else if (resource.kind !== "function" && entry.endsWith("index.ts")) {
    const serverImport = entryText.indexOf("import('./server");
    if (serverImport === -1 || serverImport < call.index) {
      fail(`${resource.address} must load its Doppler secrets before importing ./server (${entry})`);
    }
  }
  // Every Python service guards its internal endpoints with INTERNAL_API_KEY and fails
  // closed: it builds the shared verifier at module level, after the Doppler load, so a
  // missing key stops the boot instead of leaving the endpoints open.
  if (isPython && call) {
    const verifier = INTERNAL_API_KEY_VERIFIER.exec(entryText);
    if (!verifier || verifier.index < call.index) {
      fail(`${resource.address} must build verify_internal_api_key with make_internal_api_key_verifier(require_internal_api_key()) at module level, after its Doppler load (${entry})`);
    }
  }
  const listed = parseDopplerSecrets(entryText);
  const expected = Object.entries(resource.variables ?? {})
    .filter(([name, value]) => value.type === "sharedReference" && !name.startsWith("DOPPLER_"))
    .map(([name]) => name)
    .sort();
  if (listed === null || listed.length === 0) {
    fail(`${resource.address} has no non-empty DOPPLER_SECRETS list (${entry})`);
  } else if (listed.join(",") !== expected.join(",")) {
    fail(`${resource.address} DOPPLER_SECRETS is [${listed.join(", ")}], expected [${expected.join(", ")}] (its shared references)`);
  }
}

for (const resource of resources) {
  const summary =
    resource.type === "service"
      ? `${resource.kind.padEnd(12)} ${(resource.deploy?.cronSchedule ?? "").padEnd(12)} ${(resource.deploy?.startCommand ?? "").slice(0, 60)}`
      : resource.type === "database"
        ? `${resource.kind.padEnd(12)} ${resource.engine.padEnd(12)} ${(resource.deploy?.startCommand ?? "").slice(0, 60)}`
        : resource.type === "volume"
          ? `${resource.config?.sizeMB ?? "?"} MB in ${resource.config?.region ?? "?"}`
          : "";
  console.log(`${resource.address.padEnd(32)} ${summary}`);
}

if (failures.length > 0) {
  console.error(`\n${failures.length} check(s) failed:`);
  for (const failure of failures) {
    console.error(`  - ${failure}`);
  }
  process.exit(1);
}
console.log(`\nOK: ${resources.length} resources in project ${definition.name}`);

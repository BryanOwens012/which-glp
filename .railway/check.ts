/**
 * Offline smoke test for railway.ts.
 *
 * Evaluates the program the way the Railway CLI does (Node with type stripping)
 * and asserts the invariants a `railway config plan` cannot check for us:
 * unique resources, every runnable service has a start command, GitHub sources
 * pin the production branch, function bodies round-trip to ./functions, no
 * secret-looking variable is committed as a literal value, a variable named like
 * a shared variable is a `${{shared.NAME}}` reference to it, and every variable a
 * service declares is mentioned somewhere in the code that service runs.
 *
 * Run from this directory: npm run check
 */
import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, realpathSync, statSync } from "node:fs";
import { join } from "node:path";
import { createRailwayContext, project, type ResourceNode } from "railway/iac";
import program, { SHARED_VARIABLES } from "./railway.ts";

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

/** The code a service runs: its function file, or the directory its deploys watch. */
const codeRootOf = (resource: ResourceNode & { type: "service" }): string | undefined => {
  if (resource.kind === "function") {
    return join(import.meta.dirname, "functions", `${resource.name.toLowerCase()}.ts`);
  }
  const pattern = resource.build?.watchPatterns?.[0];
  return pattern ? join(REPO_ROOT, pattern.replace(/^\//, "").replace(/\/\*\*$/, "")) : undefined;
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
    const file = `${resource.name.toLowerCase()}.ts`;
    const expected = readFileSync(join(import.meta.dirname, "functions", file));
    if (!encoded || Buffer.from(encoded, "base64").compare(expected) !== 0) {
      fail(`${resource.address} start command does not encode functions/${file}`);
    }
    if (!resource.deploy?.cronSchedule) {
      fail(`${resource.address} has no cron schedule`);
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
        `${resource.address} declares ${name} as a ${value.type} value; it is a shared variable, so reference it as \${{shared.${name}}}`,
      );
    }
  }

  const codeRoot = codeRootOf(resource);
  if (!codeRoot) {
    fail(`${resource.address} has no code location (watch pattern or function file) to check its variables against`);
    continue;
  }
  const pythonEntry = join(codeRoot, "api.py");
  const source = existsSync(pythonEntry) ? readPythonClosure(pythonEntry) : readSourceTree(codeRoot);
  if (source.files === 0) {
    fail(`${resource.address} code location ${codeRoot} holds no files`);
    continue;
  }
  for (const name of Object.keys(resource.variables ?? {})) {
    if (!RUNTIME_VARIABLES.has(name) && !new RegExp(`\\b${name}\\b`).test(source.text)) {
      fail(`${resource.address} declares ${name}, which its code (${codeRoot}) never reads; remove it`);
    }
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

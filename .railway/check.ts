/**
 * Offline smoke test for railway.ts.
 *
 * Evaluates the program the way the Railway CLI does (Node with type stripping)
 * and asserts the invariants a `railway config plan` cannot check for us:
 * unique resources, every runnable service has a start command, GitHub sources
 * pin the production branch, function bodies round-trip to ./functions, and no
 * secret-looking variable is committed as a literal value.
 *
 * Run from this directory: npm run check
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { createRailwayContext, project, type ResourceNode } from "railway/iac";
import program from "./railway.ts";

const EXPECTED_BRANCH = "develop";
const SECRET_NAME = /KEY|SECRET|PASSWORD|TOKEN/;

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
  }
}

for (const resource of resources) {
  const summary =
    resource.type === "service"
      ? `${resource.kind.padEnd(12)} ${(resource.deploy?.cronSchedule ?? "").padEnd(12)} ${(resource.deploy?.startCommand ?? "").slice(0, 60)}`
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

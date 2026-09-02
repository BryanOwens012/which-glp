# Railway Infrastructure as Code

`railway.ts` declares the whole WhichGLP `production` environment on Railway: the API, the four Python services, Redis and its volume, and the four cron functions whose source lives in `functions/`. It replaces the per-service `railway.json` files (Railway's deprecated Config as Code, unread after 2026-12-01).

## Editing

1. Change `railway.ts` (or a file in `functions/`).
2. `npm ci && npm run typecheck && npm run check` from this directory. `check` evaluates the file the way the CLI does and asserts branch pinning, function round-trips, and that no secret is committed as a literal.
3. `railway config plan` from a directory linked to the WhichGLP project. Read every line: the plan must list only the change you made, never an unexpected delete of a service, variable, domain, proxy, or volume.
4. `railway config apply` (Bryan only; agents are held read-only on Railway).

## Rules

- **Omit means delete.** Every resource and every variable name must be listed. Values stay on Railway via `preserve()`; never paste a value into this file.
- **Branch is explicit.** Production tracks `develop`; the SDK's `github()` helper defaults to `main`.
- **Dashboard edits drift.** After changing anything in the Railway UI, run `railway config pull` on a scratch branch (it overwrites `railway.ts`), read the diff, fold the change back into the real file by hand, and discard the pull.
- **One file per project.** Do not add a `partial` export or a second language file.
- **Networking is live state.** Each service's private-network hostname (`privateNetworkEndpoint`) and Railway-generated domain are part of the graph the plan diffs; the first plan reported a networking update on every service until both were declared. Declare them through `buildNetworking`.
- **Redis is a `database` node, not a `service`.** Railway addresses it as `database.Redis`; declaring it with `service()` plans a delete-and-recreate. Its variables, TCP proxy, and mount are owned by the database product and stay out of the file.

## Linking a clone

Link state is per machine, not per repo:

```bash
railway link -p df649372-5b20-4e68-8ccd-31935edceade -e production
```

Docs: <https://docs.railway.com/infrastructure-as-code> and the reference at `/infrastructure-as-code/reference`.

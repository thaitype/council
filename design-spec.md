# Council — Design Spec

Status: Layer 1–3 locked. Layer 4 in progress (Blocks 1, 2, 3, 4 locked; Block 5 = Deployment & Config pending).

---

## Layer 1: Vision

- **What** — Council is an agent control plane that puts a hard human-approval gate between AI coding agents and the real world. Agents run on the developer's local machine in their normal setup, and propose **Artifacts** through Council's MCP endpoint. A human approves; Council executes against protected targets.
- **Why** — Devs already love their agent CLIs; the missing piece is a hard human-in-the-loop on real-world side effects, with central audit and team approval, without forcing devs into a new chat product.
- **Who it's for** — Developers and teams running AI coding agent CLIs (Claude Code, Codex, Cursor CLI, etc.) who want a security-first approval gate, locally or shared across a team.
- **One service** — **Council** is a single Go binary that exposes:
  - **REST API** — for the web UI and ops.
  - **MCP server (Streamable HTTP)** — for agent CLIs to call `create_artifact` and friends directly.
  - **Web UI** — the approval inbox.
  - **Executor pool** — picks up approved artifacts and runs them.
  Runs locally or on a shared host; same binary, same config.
- **Core primitive — Artifact** — Unit of approval. Coarse enough to avoid approval fatigue, fine enough to keep blast radius clear. Wraps any executable action (bash, kubectl, az/gcloud/aws, curl, scripts). Lifecycle: proposed → approved/rejected → running → done/failed.
- **v1 policy** — Every Artifact requires human approval. No auto-run, no allowlist. Security-first; UX refinements (tiers, allowlists) deferred to v2+.
- **Async flow** — Agent proposes; doesn't block on approval. Artifacts pile into Council's review queue. Human approves on their own time, in any order. Executor runs async; results land in artifact history.
- **Phase-1 web UI** — approval inbox + artifact detail + run history. **No chat UI.**
- **Done looks like** — Dev points Claude Code's MCP config at `https://council.example.com/mcp` with a token → agent calls `create_artifact` for any real-world action → Artifact lands in Council's queue → reviewer approves in web UI → Council's executor runs it against the target → output saved to artifact history. Same binary works on a laptop or a shared server.

---

## Layer 2: Scope

### In scope (v1)

- **Council** (Go): REST API, MCP server (Streamable HTTP), artifact state machine, persistent store (SQLite v1), executor pool.
- **Web UI** (React, embedded in Council binary): approval inbox, artifact detail view, run history, project switcher. No chat.
- **Projects** as grouping unit for artifacts, executors, credentials.
- **One executor**: `local-shell` (runs on Council host). `kube-job` deferred to v2.
- **Auth**: bearer token for MCP/REST clients; shared-password session for web UI.
- **Audit log**: every artifact + approval + execution recorded, replayable.
- **Deployment**: single Go binary, runs locally or on a server. Helm/manifests for Kube optional but documented.
- **Agent integration**: documented MCP setup for Claude Code as the reference; should work for any agent CLI supporting MCP over Streamable HTTP.

### Out of scope (v1)

- Chat UI of any kind.
- Auto-run / allowlists / tiered approval.
- Multi-tenant org features, SSO, full RBAC (only operator/approver/viewer at most).
- Slack, email, mobile, or any non-web channel.
- Plugin marketplace / third-party executors.
- Rollback automation; cost/quotas; secret management beyond what executors need to function.
- Streaming output from running executors to web UI in realtime (poll or refresh in v1).
- Local-side companion process (was "Herald") — agents talk MCP-over-HTTP directly to Council.

### Constraints

- Backend: Go.
- Frontend: React (embedded as `embed.FS`).
- Same binary runs local + server; config is the only difference.
- Council never tries to control the agent's process; only the artifact boundary.
- MCP over Streamable HTTP is the agent-facing protocol; REST is the UI/ops protocol.

### Users / Actors

- **Operator** — installs/runs Council, configures projects, executors, credentials.
- **Developer** — runs agent CLI locally with Council's MCP endpoint configured.
- **Approver** — reviews and approves Artifacts in the web UI. v1: same person as developer or operator (no separation enforced).
- **Agent** — AI coding CLI; calls Council's MCP endpoint over HTTP.

---

## Layer 3: Building Blocks

```
            ┌──────────────────────┐
            │   1. Artifact Core   │   ← foundation
            └──────────┬───────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              │
  ┌──────────────┐  ┌──────────────┐  │
  │ 2. Council   │  │ 3. Executor  │  │
  │    Server    │  │   Framework  │  │
  └────┬─────────┘  └──────┬───────┘  │
       │                   │          │
       ▼                   │          ▼
  ┌─────────────┐          │   ┌──────────────────┐
  │ 4. Web UI   │          └──►│ 5. Deployment &  │
  └─────────────┘              │    Config        │
                               └──────────────────┘
```

1. **Artifact Core** — domain model + state machine + persistence. Foundation. Depends on: nothing.
2. **Council Server** — Go binary serving REST + MCP (Streamable HTTP). Project model, artifact CRUD, approval, auth/tokens. Depends on: Artifact Core.
3. **Executor Framework** — pluggable runner interface; v1 ships `local-shell` only. Depends on: Artifact Core.
4. **Web UI** — React app embedded in Council. Approval inbox, artifact detail, run history. No chat. Depends on: Council Server.
5. **Deployment & Config** — single binary; local mode and server mode; Helm/manifests for Kube; shared config model; install docs. Depends on: Council Server, Executor Framework.

---

## Layer 4: Block Specs

### Block 1 — Artifact Core (locked)

**What it does**

Defines the Artifact domain — its shape, lifecycle, and storage. Every other block reads/writes through this. No HTTP, no UI; just types, state transitions, and a persistence layer.

**Artifact shape (v1)**

| Field | Type | v1? | Notes |
|---|---|---|---|
| `id` | uuid | ✓ | server-assigned |
| `project_id` | uuid | ✓ | required |
| `title` | string | ✓ | short, human-readable |
| `rationale` | string (markdown) | ✓ | shown in approval UI |
| `payload` | jsonb (tagged by `kind`) | ✓ | see variants below |
| `runtime` | enum | ✓ | `local-shell` (v1) |
| `runtime_config` | jsonb | ✓ | runtime-specific |
| `created_by` | string | ✓ | principal resolved from MCP token |
| `session_id` | uuid | ✓ | MCP session id (per-agent-process) |
| `created_at` | timestamp | ✓ | |
| `state` | enum | ✓ | proposed/approved/rejected/running/done/failed |
| `approved_by` | string? | ✓ | |
| `approved_at` | timestamp? | ✓ | |
| `rejection_reason` | string? | ✓ | |
| `execution` | nullable struct | ✓ | started_at, finished_at, exit_code, stdout, stderr, executor_id |

**Identity model**

- `created_by` = stable principal (e.g. `claude-code@thada-mbp`), resolved server-side from the token presented on the MCP connection. Agent does **not** self-declare this.
- `session_id` = the MCP session id (`Mcp-Session-Id` header in Streamable HTTP). Fresh per agent process; lets the inbox group "all artifacts from one agent run."

**Payload variants (tagged union)**

```jsonc
// v1
{ "kind": "command", "command": "kubectl apply -f m.yaml", "cwd": "...", "env": {...} }

// v2
{ "kind": "bundle",  "command": "./deploy.sh", "bundle_ref": "blob://...", "cwd": "...", "env": {...} }

// v3 (illustrative, not committed)
{ "kind": "git_ref", "command": "make deploy", "repo": "...", "ref": "abc123" }
```

Go shape: `Payload` interface with variants (`CommandPayload`, etc.); custom `UnmarshalJSON` switches on `kind`. Executor framework dispatches on the same.

**State machine**

```
proposed ──approve──► approved ──claim──► running ──┬─► done
   │                                                └─► failed
   └──reject──► rejected
```

Terminal: `rejected`, `done`, `failed`. **No re-runs in v1** — re-running means proposing a new Artifact.

**Persistence**

- SQLite (single file) for v1. Schema migrations via `golang-migrate`.
- Postgres-compatible SQL kept in mind, but no driver abstraction yet.
- Append-only audit table: every state transition logged with actor + timestamp + before/after state. Powers replayable history.

**Key decisions / trade-offs**

- **Payload as JSON-tagged union, not flat columns.** Storage in SQL is fine since payload is never filtered/indexed. Win is Go ergonomics + extensibility.
- **Closed `runtime` enum.** Forces executor parity; new runtimes mean a new enum value + executor impl.
- **No re-run.** Keeps state machine small.
- **SQLite first.** Fits "local or shared server" without ops burden.
- **Audit is a sibling table, not event-sourced.** Sufficient for replay.
- **Server-issued identity (`created_by`, `session_id`).** Agents can't lie about who they are.

**Open questions / [TBD]**

- `runtime_config` validation: in this block, or push to executor? Leaning push to executor.
- Optional `expected_effect` field. `[TBD]`
- Soft-delete vs hard-delete. `[TBD]` — likely soft-delete.

---

### Block 2 — Council Server (locked)

**What it does**

Single Go HTTP server. Three faces on one binary:

- **REST API** — `/api/...` for the web UI and ops.
- **MCP server** — `/mcp` Streamable HTTP endpoint for agent CLIs.
- **Static web UI** — `/` serves the embedded React app.

Owns project model and auth. Wraps Artifact Core for persistence. Drives the executor dispatch loop.

**REST endpoints (v1)**

```
# Projects
GET    /api/projects
POST   /api/projects                  body: { name, description }
GET    /api/projects/:id

# Artifacts
GET    /api/projects/:id/artifacts    ?state=proposed&limit=50&cursor=...
GET    /api/artifacts/:id
POST   /api/artifacts/:id/approve     body: { note? }
POST   /api/artifacts/:id/reject      body: { reason }
GET    /api/artifacts/:id/execution   poll for run output

# Auth
POST   /api/tokens                    operator-only; mints agent tokens
GET    /api/me                        identity check

# Health
GET    /healthz
GET    /readyz
```

**MCP tools (over Streamable HTTP at `/mcp`)**

| Tool | Inputs | Returns |
|---|---|---|
| `create_artifact` | `project?`, `title`, `rationale`, `command`, `cwd?`, `env?`, `runtime?`, `runtime_config?` | `{ artifact_id, state, url }` |
| `get_artifact` | `artifact_id` | full artifact JSON |
| `list_my_artifacts` | `project?`, `state?`, `limit?` | recent artifacts created by this principal/session |
| `wait_for_artifact` | `artifact_id`, `timeout_seconds?` (max 300) | blocks until terminal state or timeout |

`create_artifact` does **not** accept `created_by` or `session_id` from the agent. Council derives them from the MCP token (principal) and `Mcp-Session-Id` header.

**Auth model (v1)**

- **Agent → Council MCP**: bearer token in `Authorization` header. Token scopes to one or more projects and resolves to a principal (`created_by`). Operator mints via `/api/tokens`. No expiry in v1 (revoke by deletion).
- **Web UI**: shared password session for v1. No SSO.
- **Roles**: operator (everything), approver (approve/reject/view), viewer (view only). Project-scoped. No full RBAC.

**Project model**

- Project = name + description + executor binding + runtime defaults (e.g. cwd, env templates).
- Project owns its credentials; passed to executor at run time, never returned in API responses.
- Soft-delete; artifacts retained for audit.

**Tech choices**

- Router: stdlib `net/http` (Go 1.22+ ServeMux) or `chi`. Lean stdlib.
- DB: SQLite via `modernc.org/sqlite`.
- Migrations: `golang-migrate`.
- MCP: official Go MCP SDK or hand-rolled Streamable HTTP handler against the spec.
- Config: env vars + `~/.council/config.json`. Same shape local vs server.

**Key decisions / trade-offs**

- **One binary, three faces.** REST, MCP, and UI in one process. Simpler ops; tradeoff is monolithic deploy.
- **MCP handlers reuse the same domain calls as REST.** No translation layer; both call into Artifact Core.
- **Polling for execution output (v1).** No WebSocket/SSE in v1. Defer streaming to v2.
- **Tokens, not OIDC.** Operator-issued bearer tokens. Devs paste into agent's MCP config (with env-var substitution where supported).
- **Project = executor binding.** A project can't fan out to multiple executors in v1.

**Open questions / [TBD]**

- Pagination style: cursor or offset? Lean cursor.
- Webhook/notification on new artifact for remote approvers? `[TBD v2]`
- Execution log size limits — truncate + link to file? `[TBD]`

---

### Block 3 — Executor Framework (locked)

**What it does**

Picks up approved Artifacts, runs them, captures output, writes the final result back to Artifact Core. Pluggable interface; **v1 ships `local-shell` only**. `kube-job` deferred to v2.

**Where it runs**

In-process with Council as a goroutine pool. Single Go binary. Future executors run their *logic* inside Council and call out to target systems; only the *workload* runs remotely.

**Runner interface**

```go
type Executor interface {
    Name() string                         // "local-shell"
    Validate(a Artifact) error            // pre-flight: payload kind, runtime_config shape
    Run(ctx context.Context, a Artifact, sink ResultSink) error
}

type ResultSink interface {
    AppendStdout(b []byte) error
    AppendStderr(b []byte) error
    Finish(exitCode int, err error) error
}
```

**Dispatch loop**

- Single dispatcher goroutine. Polls for `state = approved` artifacts (1s; bumped by in-process notify on approve).
- Claims via transactional state transition `approved → running` with `executor_id` set.
- Hands off to the matching executor's `Run`.
- On return: transitions `running → done | failed`, persists exit code + captured output.
- Concurrency cap: configurable (default 4).

**Local-shell executor (v1)**

- `payload.kind == "command"` only.
- `exec.CommandContext("bash", "-lc", payload.command)` with `cwd`, `env` from payload merged with project defaults.
- Stdout/stderr piped to `ResultSink`.

**Kube-job executor (v2 — sketch only)**

- Materializes artifact as `batchv1.Job` in the project's namespace.
- Image, command, env from payload + project defaults; secrets via `Secret` refs.
- Watches Job to completion; tails pod logs into `ResultSink`.

**Credentials**

- Council holds a per-project credential bundle (env vars, file paths). Encrypted-at-rest with a master key from env.
- Executors read at run time via project-scoped accessor.
- Secret values never returned in API responses or written to artifact rows.

**Failure handling**

- Non-zero exit → `failed`, no retry. Re-running = new Artifact.
- Executor crash/panic → recovered; transitions to `failed` with `err = "executor crashed"`.
- Council restart while artifact `running` → on boot, sweep stale `running` rows and mark `failed`.
- Per-executor default timeout (e.g. 30 min for local-shell), configurable.

**Key decisions / trade-offs**

- In-process executors; simpler binary. Trade: noisy executor can affect HTTP latency.
- Poll + notify, no message queue.
- No retries.
- v1 = local-shell only; kube-job validates the abstraction in v2.
- Buffered output to DB, capped (default 1 MB stdout/stderr).

**Open questions / [TBD]**

- Per-project executor allowlist or implicit from binding? `[TBD]`
- Master-key source: `age`, libsodium, or stdlib AES-GCM. `[TBD]`

---

### Block 4 — Web UI (locked)

**What it does**

The reviewer's surface. Approval inbox + artifact detail + run history. **No chat.**

**Pages**

1. **Login** — shared password.
2. **Inbox** (default) — `state = proposed` across visible projects. Newest first. Filter by project.
3. **Artifact detail** — header (title, project, state, created_by, session_id, timestamps); rationale (markdown); command preview; runtime + runtime_config; action bar (Approve / Reject); execution panel (poll 2s while running).
4. **History** — non-`proposed` artifacts; filter by project + state. Optional grouping by `session_id`.
5. **Projects** — list/create. Operator-only edit.
6. **Tokens** — operator-only. Mint agent tokens (per project scope), copy once on creation, list + revoke.

**Tech choices**

- React + Vite, TypeScript.
- Bundled and served by Council as static assets (`embed.FS`).
- State: TanStack Query.
- Styling: Tailwind.
- Markdown: `react-markdown` with safe defaults.
- Routing: `react-router` flat routes.

**Polling**

- Inbox: 5s.
- Artifact detail (running): 2s.
- Other: refetch on focus + 30s stale time.

**Key decisions / trade-offs**

- No chat — conversation lives with the agent on the dev's machine.
- Polling, not WebSocket/SSE.
- Bundled into Council binary.
- Tailwind + minimal component lib.
- Markdown rationale.

**Open questions / [TBD]**

- Diff view for file-changing commands. Out of scope v1.
- Keyboard shortcuts. Tentatively in.
- Mobile layout. `[TBD]`

---

### Block 5 — Deployment & Config (locked)

**What it does**

Defines how Council is built, distributed, configured, and operated. Covers single-binary packaging, the config model, first-run bootstrap, and the two deployment modes (local laptop, shared server).

**Distribution (v1)**

- **Single static Go binary**, `council`. Build from source: `go install` or `go build ./cmd/council`.
- **Container image**: `ghcr.io/<org>/council:<version>` — distroless base, binary at `/council`, default `EXPOSE 8080`.
- **No prebuilt release binaries in v1.** Cross-compiled artifacts (linux/darwin amd64/arm64), Homebrew tap, etc. deferred until the project is ready for broader distribution.
- **Web UI assets** built into the binary via `embed.FS`. No separate static-files step.

**CLI surface**

```
council serve [--config PATH]      # main entrypoint
council init                       # interactive: creates config, sets admin password
council token mint --project P --principal NAME [--scope ...]
council token list
council token revoke <id>
council project create --name N
council db migrate                 # explicit; serve auto-runs by default
council version
council doctor                     # config + DB + executor sanity checks
```

**Config file — `~/.council/config.json`**

```json
{
  "listen": "127.0.0.1:8080",
  "external_url": "https://council.example.com",
  "database": {
    "path": "~/.council/council.db"
  },
  "auth": {
    "ui_password_hash": "argon2id$...",
    "master_key_env": "COUNCIL_MASTER_KEY"
  },
  "executors": {
    "local_shell": {
      "enabled": true,
      "default_timeout_seconds": 1800,
      "max_concurrent": 4,
      "stdout_cap_bytes": 1048576,
      "stderr_cap_bytes": 1048576
    }
  },
  "logging": {
    "level": "info",
    "format": "json"
  }
}
```

- **Path resolution**: `--config` flag > `$COUNCIL_CONFIG` env > `~/.council/config.json` > `/etc/council/config.json`.
- **Env overrides**: any leaf can be set via `COUNCIL_<UPPER_SNAKE_PATH>` (e.g. `COUNCIL_LISTEN=0.0.0.0:8080`). Useful for container deploys.
- **Same shape, two deployments** — laptop and server use the same JSON; only `listen`, `external_url`, `database.path`, and TLS termination differ. Server mode typically sits behind a reverse proxy; Council does not terminate TLS itself in v1.

**Secrets & master key**

- Master key (32 bytes, base64) read from env (`COUNCIL_MASTER_KEY` by default). Used to encrypt per-project credential bundles at rest.
- `council init` generates one and prints it once with instructions to persist via secret manager / systemd `EnvironmentFile` / Kube `Secret`.
- Council refuses to start if encrypted credential rows exist but no master key is provided.

**First-run bootstrap (`council init`)**

1. Creates `~/.council/` if missing.
2. Generates `master_key`; prints once.
3. Prompts for admin (operator) password → `argon2id` hash into `auth.ui_password_hash`.
4. Writes default `config.json`.
5. Runs DB migrations.
6. Prints next steps: start `council serve`, log in, mint first token.

**Kubernetes deployment**

- **Reference manifests** in `deploy/kubernetes/` (plain YAML in v1; Helm chart later).
- **Workload**: `Deployment`, replicas: 1 in v1 (SQLite is single-writer; HA needs Postgres in v2).
- **Storage**: `PersistentVolumeClaim` mounted at `/var/lib/council` for the SQLite file.
- **Config**: `ConfigMap` for non-secret config; `Secret` for `COUNCIL_MASTER_KEY` and `auth.ui_password_hash`.
- **Service + Ingress** for HTTP. TLS at the ingress.
- **Liveness/readiness** probes: `/healthz` and `/readyz`.

**Logging, metrics, tracing (v1 minimum)**

- Structured JSON logs to stdout (level + format from config).
- Per-request log line for REST/MCP: method, path, status, principal, project, artifact id (if any), duration.
- Audit log writes go to DB **and** stdout (so external log shippers capture them too).
- `/metrics` Prometheus endpoint with basics: HTTP latency, executor pool depth, artifacts by state. Optional in v1; flag-gated.
- No tracing in v1.

**Backup & recovery**

- v1 backup story: stop service, copy `council.db`. Restore = drop file back, start.
- Document this. No hot-backup in v1.

**Upgrade path**

- Build/pull new binary/image; restart. Migrations auto-run on `serve` start (controlled by `--auto-migrate=false` for ops who want explicit control).
- Forward-only migrations in v1.

**Key decisions / trade-offs**

- **Build from source / container image only.** No prebuilt binaries in v1; reduces release-engineering burden. Trade: friction for non-Go users; revisit when broader audience.
- **Single binary, one config file.** Lowest operational floor.
- **No TLS in Council itself.** Reverse proxy in prod; localhost in dev.
- **SQLite single-replica.** Hard scale limit. Postgres + multi-replica is v2.
- **Master key in env, not file.** Forces operators to think about secret management.
- **Forward-only migrations.** Bad migration = restore from backup.

**Open questions / [TBD]**

- Helm chart: v1 or v2? Lean v2.
- Audit log retention/rotation. `[TBD]`
- Self-update / built-in updater? No.

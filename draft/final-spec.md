# Council — Design Specification

> **Multi-agent orchestration platform with artifact governance**  
> Part of the chief-tribe ecosystem

---

## 1. Vision

Council is a platform where AI agents propose actions, humans review them, and approved actions get executed — all with clear separation between throwaway work and managed code.

The current AI agent landscape forces a binary choice: either give agents autonomy and accept risk, or gate every action and lose productivity. Council resolves this by treating agent output as artifacts that flow through environments — proven safe in sandbox, reviewed by humans, executed in production by separate executors.

Council is **agent-agnostic** (works with Claude Code, OpenCode, Pi, or any CLI agent), **vertical-agnostic** (DevOps, coding, data ops, security all fit), and **deployment-flexible** (laptop, jumphost, in-cluster).

---

## 2. Position in chief-tribe

```
chief-tribe/
├── sage           ← behavior principles (any agent)
├── chief          ← workflow framework (single-task)
├── chieftain      ← runtime + distribution (developer-focused)
└── council        ← multi-agent platform (team + governance)
```

| | Single-agent focus | Multi-agent focus |
|---|---|---|
| **No runtime** | sage, chief | — |
| **With runtime** | chieftain | **council** |

Council is the team-and-governance layer. Where chieftain optimizes for one developer working with one agent, council orchestrates many agents working on many tasks for many people.

---

## 3. Core concepts

### 3.1 Agent

An **agent** is an autonomous worker that:
- Runs in an isolated workspace (filesystem + git branch)
- Uses an underlying CLI runtime (Claude Code, OpenCode, Pi)
- Receives tasks via triggers
- Produces artifacts as output

Agents in council are **session-scoped** by default — spun up for a task, terminated after. Long-running agents (watchers, monitors) are explicit configurations.

### 3.2 Artifact

An **artifact** is the output of an agent's work. Council distinguishes two kinds:

**Temporary artifact**
- One-time output: incident remediation, investigation result, ad-hoc fix
- Lifecycle: produced → reviewed → executed → archived
- Storage: database (with markdown rendering for human review)
- Approval: through council UI
- TTL: configurable, default 7 days

**Permanent artifact**
- Reusable code: kubernetes manifest, terraform module, runbook script
- Lifecycle: produced → PR → reviewed → merged → versioned
- Storage: git repository
- Approval: through standard PR review
- No TTL: lives in source control

The split exists because mixing them creates noise. A `kubectl patch` to fix today's incident shouldn't pollute the same review queue as a permanent CI/CD pipeline change.

### 3.3 Trigger

A **trigger** initiates an agent session. Council supports four types:

- **Prompt** — user types a request through UI/API
- **Cron** — scheduled execution at fixed times
- **Webhook** — external event (PagerDuty, GitHub, monitoring alert)
- **Manual** — operator-initiated from dashboard

All triggers produce a uniform `Task` object that the orchestrator dispatches to an agent.

### 3.4 Environment

An **environment** is where agent work happens or where artifacts execute:

- **Sandbox** — isolated, ephemeral, where agents have full autonomy
- **Production** — real, where reviewed artifacts run via separate executor

Council enforces that agents never directly touch production. Production access requires reviewed artifact + executor service with production credentials.

### 3.5 Workspace

A **workspace** is an agent's private working directory:
- Isolated filesystem (`agents/{agent-id}/workspace/`)
- Dedicated git branch (`agent/{agent-id}/{task-slug}`)
- Scoped credentials (sandbox-only)
- Cleaned up after session

Multiple agents can run concurrently without interference because workspaces never share state.

### 3.6 Approval

An **approval** is a human decision on an artifact. Council supports:

- **Approve** — execute as-is
- **Approve with edits** — modify then execute
- **Reject** — discard with feedback
- **Request changes** — send back to agent for revision

Approval policies are configurable per artifact type, risk level, and approver role.

### 3.7 Promotion

**Promotion** is the path from temporary to permanent. When a temporary artifact has been used multiple times or is explicitly tagged for permanence, council can:

- Open a PR converting the artifact into managed code
- Suggest where in the codebase it belongs (scripts/, runbooks/, terraform/)
- Link the new code back to the artifact history

Promotion bridges ad-hoc fixes and managed infrastructure.

---

## 4. Architecture

### 4.1 Component overview

```
┌──────────────────────────────────────────────────────────────┐
│  CLIENTS                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  Web UI      │  │  CLI         │  │  Webhook source  │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘    │
└─────────┼─────────────────┼─────────────────┼────────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │ HTTPS / JSON-RPC
┌───────────────────────────▼──────────────────────────────────┐
│  COUNCIL SERVER                                              │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  API Gateway                                           │  │
│  │  - Authentication, rate limit, request routing         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  Trigger     │  │  Agent       │  │  Artifact        │    │
│  │  Manager     │  │  Orchestrator│  │  Service         │    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  Approval    │  │  Promotion   │  │  Audit           │    │
│  │  Engine      │  │  Service     │  │  Logger          │    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
│                                                              │
└────────┬─────────────────┬─────────────────┬─────────────────┘
         │                 │                 │
         ▼                 ▼                 ▼
┌──────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Storage    │  │   Agent         │  │   Executor      │
│              │  │   Runtime       │  │   Service       │
│  Postgres +  │  │   (subprocess)  │  │   (separate     │
│  Object Store│  │                 │  │   process/pod)  │
│  + Git       │  │  Claude Code /  │  │                 │
│              │  │  OpenCode / Pi  │  │  Production     │
└──────────────┘  └─────────────────┘  │  credentials    │
                                       └─────────────────┘
                                                │
                                                ▼
                                       ┌─────────────────┐
                                       │   Production    │
                                       │   Environment   │
                                       └─────────────────┘
```

### 4.2 Component responsibilities

**API Gateway**
- HTTPS termination, authentication (OIDC/token), authorization (RBAC)
- Rate limiting per user and per project
- Request routing to internal services
- Request/response logging for audit

**Trigger Manager**
- Receives triggers from all sources (prompt, cron, webhook, manual)
- Normalizes them into uniform `Task` objects
- Persists task records before dispatch
- Manages cron schedules

**Agent Orchestrator**
- Spawns agent runtime in isolated workspace
- Provisions sandbox environment if required
- Tracks agent session lifecycle
- Captures stdout/stderr, events, tool calls
- Enforces resource quotas (max concurrent agents, timeout, memory)
- Cleanup on completion

**Artifact Service**
- Validates artifact schema on submission
- Stores temporary artifacts in database
- Indexes artifacts for query/search
- Manages artifact state transitions
- Generates rendered views (markdown, HTML)

**Approval Engine**
- Routes artifacts to approvers based on policy
- Tracks approval state and decision history
- Notifies approvers (email, Slack, in-app)
- Enforces multi-approver policies for high-risk artifacts
- Records approval audit trail

**Promotion Service**
- Identifies promotion candidates (usage frequency, explicit tags)
- Generates PR content from artifact
- Opens PR in target repository via Git provider API
- Tracks promotion history

**Audit Logger**
- Records every state change with actor, timestamp, action
- Append-only log
- Exportable for compliance review

**Storage**
- Postgres: artifacts, sessions, approvals, audit log, user data
- Object store: large artifact content, agent traces, sandbox logs
- Git: permanent artifacts via PRs to user repos

**Agent Runtime**
- External CLI process (Claude Code, OpenCode, Pi)
- Council shells out and communicates via stdin/stdout/files
- Receives task, reads convention from `.council/`, writes artifacts
- Stateless from council's perspective

**Executor Service**
- Separate from agents
- Runs approved artifacts with production credentials
- Reports execution result back to council
- Can be: in-process executor, GitHub Actions runner, ArgoCD application, custom

### 4.3 Data flow: end-to-end task

```
1. Trigger arrives (e.g., user prompt via UI)
   │
   ▼
2. Trigger Manager normalizes → Task(id, type, payload, project)
   │
   ▼
3. Agent Orchestrator:
   - Allocates workspace dir
   - Creates branch in scratch repo
   - Provisions sandbox env (if configured)
   - Generates scoped credentials
   - Spawns agent runtime as subprocess
   │
   ▼
4. Agent runtime:
   - Reads .council/council.md (convention)
   - Reads .council/skills/ (task-specific guidance)
   - Performs work in workspace + sandbox
   - Writes artifact to .council/artifacts/pending/
   │
   ▼
5. Agent emits "artifact ready" signal
   │
   ▼
6. Artifact Service:
   - Validates schema
   - Persists to DB
   - Triggers approval workflow
   │
   ▼
7. Approval Engine:
   - Determines approvers from policy
   - Sends notifications
   - Awaits decision
   │
   ▼
8. Human reviews via UI:
   - Sees artifact + agent trace + sandbox results
   - Approves / rejects / edits
   │
   ▼
9. On approval:
   - Artifact moves to "approved" state
   - Executor Service is invoked
   │
   ▼
10. Executor:
    - Runs artifact with production credentials
    - Reports result back
    │
    ▼
11. Council records execution:
    - Updates artifact state to "executed"
    - Logs result
    - Cleans up workspace and sandbox
```

---

## 5. Data model

### 5.1 Core entities

**Project**
- Top-level container for everything
- Has its own `.council/` configuration
- Has its own approver pool, agent templates, schedules

**Agent Template**
- Reusable definition: which runtime, which skills, which credentials
- Example: `incident-investigator`, `cost-analyzer`, `security-scanner`

**Agent Session**
- Concrete instance of an agent template running a task
- Has workspace, branch, credentials, lifecycle state

**Task**
- A unit of work originated from a trigger
- May spawn multiple agent sessions (e.g., investigator → fixer)

**Trigger**
- Definition of when/how tasks are created
- Subtypes: `PromptTrigger`, `CronTrigger`, `WebhookTrigger`, `ManualTrigger`

**Artifact**
- Output produced by an agent
- Has type, content, metadata, state
- Either `Temporary` or `Permanent` discriminator

**Approval**
- Decision record on an artifact
- Has approver, decision, timestamp, optional edits, comments

**Execution**
- Record of running an approved artifact
- Has executor identity, start/end time, exit code, output

**Audit Event**
- Append-only record of any state change
- Has actor, action, target, timestamp, payload

### 5.2 State machines

**Task lifecycle**
```
created → queued → running → completed
                          ↘ failed
                          ↘ cancelled
```

**Artifact lifecycle (temporary)**
```
draft → pending_review → approved → executing → executed
              ↓                         ↓
          rejected                  failed
              ↓
           archived
```

**Agent session lifecycle**
```
provisioning → running → finalizing → terminated
                  ↓
               errored
```

### 5.3 Relationships

```
Project ─┬─ has many Agent Templates
         ├─ has many Triggers
         ├─ has many Tasks
         ├─ has many Artifacts
         └─ has many Approvers (Users)

Trigger ─── creates Tasks

Task ────── has many Agent Sessions
            has many Artifacts

Agent Session ── produces Artifacts
                 has Workspace
                 has Sandbox

Artifact ── has Approvals
            has Executions
            references Task
            (if promoted) → Permanent Artifact (PR)

User ─── creates Triggers
         performs Approvals
         owns Audit Events
```

---

## 6. Conventions (the markdown layer)

Council's contract with agents lives in a `.council/` directory in each project. This is what agent runtimes read.

### 6.1 Directory structure

```
project/
├── .council/
│   ├── council.md              # main config
│   ├── skills/                 # agent-readable task guidance
│   │   ├── investigate-pod/
│   │   ├── analyze-cost/
│   │   └── refactor-component/
│   ├── artifacts/              # working area for artifacts
│   │   ├── schemas/            # artifact type schemas
│   │   └── pending/            # agent writes here
│   ├── triggers/
│   │   ├── crons.yaml
│   │   └── webhooks.yaml
│   ├── policies/
│   │   ├── approval.yaml
│   │   ├── forbidden-commands.yaml
│   │   └── promotion.yaml
│   └── agents/                 # runtime workspace (gitignored)
│       └── {session-id}/
│
├── runbooks/                   # promoted permanent artifacts
├── scripts/                    # promoted permanent artifacts
└── (regular project)
```

### 6.2 council.md

The single source of truth that agents read first:

- Project identity and scope
- Available artifact types
- Approval policy summary
- Forbidden patterns
- References to skills and templates

### 6.3 Artifact schemas

Each artifact type has a schema (YAML or JSON Schema):

- Required fields (summary, rationale, content, rollback)
- Optional fields (risk level, affected resources, cost estimate)
- Validation rules (no forbidden commands, must reference rollback)

Council validates submissions against these schemas before accepting.

### 6.4 Skills

Skills follow the same pattern as Claude Code skills:

- Markdown file with frontmatter (description, allowed-tools, when-to-use)
- Body explaining how to perform the task
- References to artifact templates

Skills are how council teaches agents domain-specific behavior without baking it into runtime.

---

## 7. API contracts (overview)

Council exposes a REST + WebSocket API. The API surface includes:

### 7.1 Resource endpoints

- **Projects** — CRUD, settings, member management
- **Agent Templates** — define, list, version
- **Triggers** — create (prompt/cron/webhook), list, enable/disable
- **Tasks** — create, list, get status, cancel
- **Agent Sessions** — list, get state, get trace, terminate
- **Artifacts** — list, filter, get content, get trace
- **Approvals** — submit decision, list pending, history
- **Executions** — list, get result, retry
- **Audit Events** — query, export

### 7.2 Streaming endpoints

- **Agent session events** — WebSocket stream of agent activity
- **Artifact updates** — server-sent events when state changes
- **Approval notifications** — push to subscribed clients

### 7.3 Webhook ingestion

- **Generic webhook** — `POST /webhooks/{trigger-id}` with signed payload
- **GitHub** — PR comments, issue mentions
- **PagerDuty** — incident events
- **Custom** — user-defined trigger handlers

### 7.4 Agent runtime contract

Council communicates with agent runtimes through:

- **Filesystem** — agent reads `.council/`, writes to `pending/`
- **MCP server** — council exposes MCP tools agent can call (submit_artifact, request_approval, check_status)
- **Subprocess stdio** — for streaming events from agent to council

The MCP server is how council offers structured submission instead of relying on filename conventions alone.

---

## 8. Security model

### 8.1 Identity

- **Users** authenticate via OIDC (Google, GitHub, Azure AD)
- **Agents** receive scoped service credentials per session
- **Executors** have their own credentials separate from agents
- All identities have audit trails

### 8.2 Credential separation

Three credential pools, never mixed:

- **Agent credentials** — sandbox-only, time-limited, read-only to production
- **Executor credentials** — production write, used only after approval
- **Council credentials** — internal services, never exposed to agents

### 8.3 Authorization

RBAC with these roles:

- **Viewer** — read-only access
- **Triggerer** — can create tasks
- **Approver** — can approve artifacts
- **Admin** — manages templates, policies, members
- **Owner** — full project control

Permissions are project-scoped. Cross-project access requires explicit grant.

### 8.4 Sandbox isolation

Every agent runs in a sandbox that:

- Has filesystem isolation (container or chroot)
- Has network isolation (egress allowlist)
- Has compute limits (CPU, memory, timeout)
- Cannot access other agents' workspaces
- Cannot access production credentials
- Has its own ephemeral cloud resources (RG, namespace, project)

### 8.5 Audit and compliance

- Every state change is logged with actor + timestamp
- Logs are append-only and tamper-evident
- Exportable for SOC2 / ISO27001 review
- Configurable retention period
- PII redaction in logs

### 8.6 Secrets management

- Secrets never embedded in artifacts
- Council references secrets by ID
- Executor resolves secret IDs at runtime
- Secret rotation handled by integrations (Vault, Azure Key Vault, AWS Secrets Manager)

---

## 9. Deployment topologies

### 9.1 Single-node (developer/small team)

```
[laptop or single VM]
├── Council server (single binary)
├── Postgres (local)
├── Object store (local filesystem)
├── Web UI (embedded in binary)
└── Agent runtime (subprocess)
```

Suitable for: solo developers, small teams, evaluation, dev environments.

### 9.2 Jumphost (medium team)

```
[Jumphost VM]
├── Council server
├── Web UI
├── Agent runtime pool
├── Sandbox provisioner (Docker / kind)
└── Executor service

[External]
├── Postgres (managed)
├── Object store (S3-compatible)
└── Production environments (k8s, cloud)
```

Suitable for: ops teams, security-conscious orgs, mixed workloads.

### 9.3 Kubernetes (large team / production)

```
[Council namespace]
├── council-api (deployment)
├── council-orchestrator (deployment)
├── council-executor (deployment)
├── council-ui (deployment)
└── postgres (statefulset or external)

[Sandbox namespaces]
└── per-session ephemeral namespaces

[Production namespaces]
└── (untouched by agents, only by executors)
```

Suitable for: enterprise, multi-team platforms, regulated environments.

### 9.4 Hybrid (control plane + edge)

Council control plane in one location (cloud), agents and executors closer to target environments (on-prem, edge).

Suitable for: organizations with multiple data centers or air-gapped environments.

---

## 10. Extension points

Council is designed for extension along several axes.

### 10.1 Agent runtime adapters

Each runtime (Claude Code, OpenCode, Pi, future) has an adapter that:

- Knows how to spawn the runtime
- Knows how to inject council MCP tools
- Knows how to capture session events
- Knows how to terminate cleanly

Adding a new runtime = writing a new adapter.

### 10.2 Trigger sources

Beyond the four built-in trigger types, custom triggers can be added:

- New webhook formats
- New event sources (Kafka, RabbitMQ, cloud events)
- New scheduling backends

### 10.3 Artifact types

Projects define their own artifact types via schemas in `.council/artifacts/schemas/`. Council validates against any schema you define.

### 10.4 Executors

Executor service is pluggable:

- Built-in: subprocess executor, container executor
- Pluggable: GitHub Actions, GitLab CI, ArgoCD, custom HTTP webhook
- Each executor implements: `Run(artifact) → Result`

### 10.5 Storage backends

- Default: Postgres + filesystem object store
- Pluggable: SQLite (single-node), S3, MinIO, Azure Blob

### 10.6 Notification channels

- Built-in: email, in-app
- Pluggable: Slack, Teams, Discord, PagerDuty, custom webhooks

### 10.7 Promotion targets

- Default: GitHub PR, GitLab MR
- Pluggable: any Git provider, any code review system

---

## 11. Non-goals (explicitly out of scope)

To preserve scope, council deliberately does not:

- **Build its own agent reasoning** — uses existing CLI runtimes
- **Replace CI/CD** — produces artifacts that CI/CD runs
- **Manage source code** — code lives in user's git, council just opens PRs
- **Provide LLM hosting** — agents call their own LLM providers
- **Implement deep observability** — exports to existing tools (Prometheus, Datadog, OpenTelemetry)
- **Replace incident management** — integrates with PagerDuty, doesn't replace it
- **Enforce coding standards** — that's chief's job
- **Optimize prompts** — that's user/agent's responsibility

Council is the orchestration + governance layer between humans, agents, and infrastructure. Everything else, it delegates.

---

## 12. Comparisons

| | Council | Chieftain | Cowork (Anthropic) | Copilot Coding Agent | Pulumi Neo |
|---|---|---|---|---|---|
| **Scope** | Multi-agent platform | Single-dev runtime | Multi-agent (productized) | Coding-focused | IaC-focused |
| **Trigger types** | All four | Prompt + manual | Prompt | GitHub events | Prompt |
| **Temp/Permanent split** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Agent-agnostic** | ✅ | Partial | ❌ (Claude only) | ❌ | ❌ |
| **Vertical-agnostic** | ✅ | ✅ | ✅ | Coding | IaC |
| **Open source** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Deployment** | Laptop → cluster | Laptop | SaaS | SaaS | SaaS |
| **Approval UI** | ✅ | ❌ | ✅ | (GitHub) | ✅ |
| **Promotion path** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Sandbox-first** | ✅ | Partial | ✅ | ✅ (Codespace) | ✅ (preview) |

Council's differentiation: **temp/permanent artifact split + multi-agent + open + agent-agnostic**. No other product covers all four.

---

## 13. Phase plan

### Phase 1: Markdown convention (proof of concept)

Markdown-only specification. No binary, no UI, no database. Users adopt by copying conventions into their project and using existing agent CLIs. This validates that the core idea (temporary artifact governance + promotion path) works in practice before any code is written.

Deliverables: convention specs, reference examples for 1-2 verticals, documentation.

### Phase 2: Light tooling

CLI utilities that help manage the `.council/` directory: artifact validators, simple cron runner, schema linters. Still no UI, still file-system based. Single-user, single-machine.

Deliverables: `council` CLI binary, basic cron support.

### Phase 3: Server runtime

Go-based server with HTTP API, database persistence, Web UI for artifact gallery and approval. Multi-user, multi-project. Single-node deployment first.

Deliverables: council server binary, Postgres schema, Web UI, basic RBAC.

### Phase 4: Production-grade platform

Kubernetes deployment, full RBAC, audit compliance features, executor pluggability, multi-runtime adapter completeness, observability.

Deliverables: Helm chart, multi-tenancy, SSO, audit export, full integrations.

### Phase 5: Ecosystem maturity

MCP server library reuse with chieftain, contributed runtime adapters, trigger source library, executor library. Plugin marketplace.

---

## 14. Success criteria

Council succeeds if it achieves these outcomes:

1. **Agent autonomy without production risk** — agents work freely in sandbox, production stays protected
2. **Reduced approval fatigue** — humans review meaningful artifacts (batched), not individual commands
3. **Knowledge graduation** — ad-hoc fixes flow naturally into managed code
4. **Multi-runtime portability** — same project works with Claude Code, OpenCode, or Pi without rewriting
5. **Audit compliance** — full traceability satisfies SOC2/ISO27001 reviewers
6. **Scale-friendly economics** — running 100 agent sessions/day costs reasonable money
7. **Zero-to-value path** — markdown-only Phase 1 useful even without runtime

The platform is meant to make AI agents trustworthy enough to deploy at team scale — not by limiting what they can do, but by structuring how their work flows through environments and reviewers.

---

## 15. Open questions

Items that remain to be decided:

- **Workflow definition language** — bespoke YAML or adopt existing (Argo Workflows, Temporal)?
- **Multi-tenancy granularity** — project-level isolation enough, or need org-level?
- **Realtime collaboration** — should multiple approvers see live cursor on artifact?
- **Cost attribution** — how to track LLM cost per agent session, expose to users?
- **Time-travel debugging** — should council retain enough state to replay agent decisions?
- **Federated council** — should multiple council instances coordinate (cross-team)?

These are deferred to later phases but kept in view to avoid architectural decisions that close them off.

---

*"Where agents propose, humans decide, and infrastructure executes."*
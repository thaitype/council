# Council Phase 1 — Design Specification

> **Markdown-only convention for multi-agent artifact governance**  
> Proof-of-concept layer of the chief-tribe ecosystem

---

## 1. Purpose of Phase 1

Phase 1 is a **markdown specification**, not a runtime. It exists to validate council's core ideas before committing to a Go implementation:

- Does temporary/permanent artifact split work in practice?
- Can agents produce structured artifacts without bespoke runtime?
- Does the approval-via-filesystem workflow feel natural?
- Is the convention portable across Claude Code, OpenCode, and Pi?

If users find Phase 1 useful on its own — even without UI, database, or server — that confirms the foundation is sound. Phase 2+ then adds tooling without changing the conventions Phase 1 establishes.

---

## 2. Scope

### 2.1 In scope

- Convention specification for the `.council/` directory
- Markdown templates that agents read and write
- Reference examples showing end-to-end workflows
- Documentation explaining how to adopt council in an existing project
- Compatibility guidance for Claude Code, OpenCode, and Pi

### 2.2 Out of scope

- Any Go binary or compiled artifact
- Web UI
- Database storage
- HTTP API
- Authentication or RBAC enforcement
- Cron scheduling (use system cron in Phase 1)
- Webhook receivers
- Approval automation
- Notification systems
- Sandbox provisioning automation
- MCP server implementation
- Multi-user coordination

Everything in this list is deferred to Phase 2+.

---

## 3. Deliverables

Phase 1 ships as a single Git repository containing:

1. **Specification documents** — the conventions agents must follow
2. **Templates** — copy-paste-ready markdown files
3. **Reference examples** — complete walkthroughs of real scenarios
4. **Adoption guide** — how to add council to an existing project
5. **Compatibility matrix** — what works with which agent runtime

No binary, no installer, no service. The repository itself is the deliverable.

---

## 4. Repository structure

```
council/
├── README.md
├── PHILOSOPHY.md
├── ROADMAP.md
├── LICENSE
│
├── spec/
│   ├── 00-overview.md
│   ├── 01-directory-structure.md
│   ├── 02-council-md.md
│   ├── 03-artifact-format.md
│   ├── 04-artifact-types.md
│   ├── 05-trigger-conventions.md
│   ├── 06-approval-workflow.md
│   ├── 07-promotion-path.md
│   ├── 08-skills.md
│   ├── 09-agent-isolation.md
│   └── 10-policies.md
│
├── templates/
│   ├── council.md
│   ├── artifacts/
│   │   ├── remediation-script.md
│   │   ├── code-change.md
│   │   ├── investigation-report.md
│   │   ├── data-migration.md
│   │   └── infrastructure-change.md
│   ├── policies/
│   │   ├── approval.yaml
│   │   ├── forbidden-commands.yaml
│   │   └── promotion.yaml
│   ├── skills/
│   │   └── (skill template structure)
│   └── triggers/
│       └── crons.yaml
│
├── examples/
│   ├── README.md
│   ├── devops-pod-investigation/
│   ├── coding-tech-debt-scan/
│   └── data-migration-proposal/
│
├── docs/
│   ├── getting-started.md
│   ├── adoption-guide.md
│   ├── runtime-compatibility.md
│   ├── faq.md
│   └── comparison.md
│
└── .council/
    └── (council uses its own conventions for its own development)
```

---

## 5. Specification scope

### 5.1 Directory structure specification

Defines the canonical layout of `.council/` inside any project:

- Required directories
- Optional directories
- Naming conventions for files within
- What is gitignored vs tracked
- How multiple agents share the directory without conflict

### 5.2 council.md specification

Defines the contract file at `.council/council.md`:

- Required sections
- Project metadata
- Available artifact types declaration
- Approval policy summary
- References to skills and policies
- How agents are expected to read it (similar to AGENTS.md)

### 5.3 Artifact format specification

Defines the universal structure of an artifact file:

- Frontmatter fields (required and optional)
- Body sections (required and optional)
- File naming convention
- Lifecycle states represented in filesystem
- How agents claim, write, and finalize artifacts

### 5.4 Artifact types specification

Defines the catalog of built-in artifact types:

- Remediation script
- Code change
- Investigation report
- Data migration
- Infrastructure change

For each type: schema, when to use, expected sections, validation rules. Users can define custom types in their own `.council/`, but Phase 1 ships these five as references.

### 5.5 Trigger conventions specification

Defines how triggers are represented in markdown/yaml:

- Prompt trigger (logged in markdown)
- Cron trigger (yaml schedule definition)
- Webhook trigger (yaml endpoint definition, simulated in Phase 1)
- Manual trigger (CLI invocation pattern)

Phase 1 does not implement triggers — it specifies how they should be expressed so Phase 2+ tooling can read them.

### 5.6 Approval workflow specification

Defines the filesystem-based approval workflow:

- Pending → approved → executed states represented as directories
- How humans move artifacts between states
- How agents check for approval status
- Approval metadata (who, when, comments) in markdown
- Multi-approver coordination through file convention

### 5.7 Promotion path specification

Defines how temporary artifacts become permanent:

- When promotion is suggested
- What promotion produces (a PR-ready file structure)
- Naming and location conventions for promoted artifacts
- How promotion history is recorded back in the temporary artifact

### 5.8 Skills specification

Defines the skill format council expects:

- Frontmatter (description, allowed-tools, when-to-use)
- Body structure
- Compatibility with Claude Code skills
- Compatibility with OpenCode skills
- Compatibility with Pi skills
- Where skills live in `.council/`

Council's skill format is a strict superset of existing conventions, so the same skill file works across runtimes.

### 5.9 Agent isolation specification

Defines how multiple agents work in the same project without interference:

- Workspace directory per agent session
- Branch naming convention
- Artifact namespacing (which agent produced which artifact)
- Cleanup expectations after session ends
- Conflict handling when two agents touch the same area

### 5.10 Policies specification

Defines the policy files in `.council/policies/`:

- Approval policy (who approves what, based on risk/type)
- Forbidden commands (patterns that artifacts must not contain)
- Promotion policy (when to suggest promotion)

Phase 1 specifies the format. Enforcement is manual (humans read policies and apply them) until Phase 2 adds validators.

---

## 6. Templates

Phase 1 provides ready-to-use templates that users copy into their projects.

### 6.1 council.md template

A skeleton council.md with placeholders for project-specific content. Users fill in:

- Project name and description
- Which artifact types they accept
- Their approval policy
- Their forbidden commands
- Their promotion rules

### 6.2 Artifact templates

One markdown template per artifact type, showing:

- Required frontmatter
- Required body sections
- Example content
- Hints for agents on what to write

### 6.3 Policy templates

YAML templates for the three policy files:

- `approval.yaml` — risk levels and approver requirements
- `forbidden-commands.yaml` — patterns to disallow
- `promotion.yaml` — promotion criteria

### 6.4 Skill template

A skeleton skill directory showing the expected structure. Empty body for users to fill with their own task guidance.

### 6.5 Trigger templates

Configuration files demonstrating how to declare:

- A cron schedule
- A webhook endpoint definition
- A manual trigger entry point

These are documentation in Phase 1; they become functional in Phase 2.

---

## 7. Reference examples

Three complete end-to-end scenarios that demonstrate council in action.

### 7.1 Example 1: DevOps pod investigation

**Scenario:** A Kubernetes pod is crashing. An agent investigates, proposes a fix, human reviews, fix is executed.

**Demonstrates:**
- Prompt-triggered task
- Investigation skill
- Remediation-script artifact type
- Manual approval workflow
- Single-execution artifact (no promotion)

**Includes:**
- Initial prompt
- Sample agent workspace
- Generated artifact in `pending/`
- Reviewer's approval action
- Execution result
- Final state of `.council/`

### 7.2 Example 2: Coding tech debt scan

**Scenario:** A scheduled scan looks for code quality issues. Agent identifies problems, proposes fixes as artifacts, some get promoted to permanent code.

**Demonstrates:**
- Cron-triggered task (specified in `crons.yaml`)
- Multiple artifacts from one task
- Code-change artifact type
- Promotion path from temporary to permanent (PR opened)

**Includes:**
- Cron configuration
- Multiple generated artifacts
- Promotion trigger when an artifact is reused
- Resulting PR content

### 7.3 Example 3: Data migration proposal

**Scenario:** An agent inspects database schema differences and proposes migration steps. Human reviews carefully because of high risk.

**Demonstrates:**
- High-risk artifact requiring multiple approvers
- Data-migration artifact type
- Rollback plan as required field
- Multi-approver coordination

**Includes:**
- Migration script artifact
- Multi-approver sign-off
- Rollback verification
- Audit trail in markdown

Each example is a complete project that users can clone, read through, and adapt.

---

## 8. Documentation

### 8.1 Getting started

A short walkthrough that takes someone from zero to a working council project in 15 minutes:

- Clone the repository
- Copy templates into a sample project
- Configure council.md
- Trigger an agent manually
- Review and approve the artifact
- See the workflow complete

### 8.2 Adoption guide

A longer document for teams adding council to an existing project:

- How to introduce `.council/` without disrupting current workflow
- How to configure for your tech stack
- How to migrate existing runbooks into council artifact types
- How to coordinate multiple team members as approvers
- Common pitfalls and how to avoid them

### 8.3 Runtime compatibility guide

Detailed instructions for each supported agent runtime:

- **Claude Code** — how to point Claude Code at `.council/`, recommended permission settings, hook configuration
- **OpenCode** — equivalent setup for OpenCode
- **Pi** — adaptation for Pi (no MCP, so different integration)
- **Other CLIs** — general principles for any agent that reads markdown

Includes a compatibility matrix showing which features work in which runtime.

### 8.4 FAQ

Answers to anticipated questions:

- "Why markdown instead of a real runtime?"
- "How does this differ from chief?"
- "Can I use this in production?"
- "What happens when Phase 2 ships?"
- "How do I migrate from chief to council?"
- "Can I use both council and chieftain?"
- "What if I don't have multiple agents?"

### 8.5 Comparison document

How council relates to:

- chief, chieftain, sage (siblings in chief-tribe)
- Cowork, Copilot Coding Agent (commercial alternatives)
- Pulumi Neo, Kiro (vertical-specific tools)
- LangGraph, Mastra (frameworks below council)

Honest about what council does and does not do.

---

## 9. Compatibility matrix

Phase 1 explicitly supports three agent runtimes. The matrix documents what works:

| Feature | Claude Code | OpenCode | Pi |
|---|---|---|---|
| Read council.md | ✅ | ✅ | ✅ |
| Read skills from .council/skills/ | ✅ | ✅ | ✅ |
| Write artifacts to .council/artifacts/pending/ | ✅ | ✅ | ✅ |
| Read approval status from filesystem | ✅ | ✅ | ✅ |
| Subagents | ✅ | ✅ | Partial |
| Permission scoping | ✅ | ✅ | Partial |
| Hooks for validation | ✅ | Partial | ❌ |

This sets expectations honestly. Phase 1 may have rough edges with Pi, full smoothness with Claude Code and OpenCode.

---

## 10. Validation strategy

Phase 1 succeeds if:

- A user can adopt council in their project in under an hour using only the documentation
- The three reference examples can be replayed end-to-end without modification
- At least two of the three runtimes (Claude Code, OpenCode, Pi) work for the full workflow
- A user can extend council with a custom artifact type without rewriting anything
- Feedback from early users surfaces gaps in the conventions, not in tooling

Phase 1 explicitly does not need to be ergonomic. Filesystem-based approval is clunky compared to a UI. That's expected. The point is to test whether the conventions are coherent, not whether the experience is polished.

---

## 11. Success metrics for Phase 1

- **Convention completeness** — every concept in the full design spec has a markdown representation
- **Reference example coverage** — at least 3 distinct verticals shown working
- **Runtime parity** — at least 2 runtimes support the full workflow
- **Adoption clarity** — getting-started guide tested with someone unfamiliar with chief-tribe
- **Extension proof** — at least one custom artifact type contributed by an early user

If Phase 1 hits these, Phase 2 can be designed with confidence.

---

## 12. Migration path to Phase 2

Phase 1 conventions become the **input format** for Phase 2 tooling.

When the Go CLI ships in Phase 2:

- It reads the same `.council/` directory
- It validates the same artifact format
- It honors the same policy files
- It supports the same skill format

Users who adopt Phase 1 do not have to migrate when Phase 2 arrives — they upgrade by installing the CLI and pointing it at their existing `.council/`.

This guarantee shapes Phase 1 design: every convention must be machine-parseable, even though Phase 1 itself does not parse them.

---

## 13. Phase 1 timeline shape

Phase 1 is a writing project, not a coding project. Its work breakdown:

1. **Spec drafting** — write the ten specification documents
2. **Template authoring** — produce all template files with realistic content
3. **Example construction** — build out three full scenarios
4. **Documentation** — write getting-started, adoption guide, runtime compatibility
5. **Internal testing** — run the examples end-to-end with each runtime
6. **External feedback** — share with a small group, gather corrections
7. **Refinement** — incorporate feedback, finalize specs
8. **Public release** — open the repository

The work is sequential up to step 3, then can parallelize. Most of the value is in steps 1-3; steps 4-7 polish.

---

## 14. Open questions for Phase 1

Decisions that affect Phase 1 specifically:

- **Approval state encoded in directory name or frontmatter?** — moving files between `pending/` and `approved/` is intuitive; frontmatter status field is more flexible but less obvious
- **Single artifact file or directory per artifact?** — single file is simpler; directory allows attachments (logs, screenshots, traces)
- **YAML or markdown frontmatter for policies?** — YAML is conventional; markdown allows inline documentation
- **Should Phase 1 include MCP server stubs?** — would prepare for Phase 3 but pollutes the markdown-only commitment
- **English-only or bilingual (Thai/English) docs from start?** — bilingual aligns with chief-tribe but doubles documentation work

These need to be resolved before Phase 1 work begins. They are scoped to Phase 1; later phases may revisit.

---

## 15. What Phase 1 is not

To be clear about expectations:

- Phase 1 is **not a product** — it is a specification
- Phase 1 is **not opinionated about runtime** — it works with any agent that reads markdown
- Phase 1 is **not deployable** — there is nothing to deploy
- Phase 1 is **not multi-user** — coordination happens through git/filesystem like any other text artifact
- Phase 1 is **not ergonomic** — moving files manually for approval is intentionally crude
- Phase 1 is **not feature-complete** — many concepts in the full vision (cron triggers, webhook ingestion, executor service) are documented but not functional

Phase 1's value is **conceptual**: it forces every council idea to be expressible in markdown, which forces clarity. If a concept can't be specified in markdown, it probably isn't designed yet.

---

*"Conventions before code. Markdown before machinery."*
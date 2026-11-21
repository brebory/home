# Home Control Center

Welcome to the central command center for @brebory's agentic workspace. This repository acts as the master coordination hub across projects, housing shared agent skills, global steering documents, and project navigation maps.

---

## Project Ecosystem

Before executing builds, tests, or git operations, always navigate (`cd`) into the target repository:

| Project | Location | Visibility / Remote | Focus |
| :--- | :--- | :--- | :--- |
| **brendonroberto.com** | `~/Workspace/brendonroberto.com` | Public | Personal portfolio & web platform |
| **fiber** | `~/Documents/GameProjects/fiber` | Private (`snackpackgames/fiber`) | Core multiplayer 2D RPG (Godot 4, Nakama) |
| **Dreambeat-Rush** | `~/Documents/Unreal Projects/PlatformFighterStarterKit 5.3` | Private (`Dreambeat-Rush/Dreambeat-Rush`) | Somnolent platform fighter (Unreal Engine 5.3). Art source in `~/Documents/GameProjects/Dreambeat Rush` |
| **Rubbley** | `~/Documents/GameProjects/Rubbley` | Public / Private | Game project |

> **Note on Windows Paths:** `~` resolves to `C:\Users\broberto`. Check `AGENTS.local.md` for machine-specific path overrides if present.

---

## Critical Rules & Conventions

### 1. Worktree Policy: Sibling Worktrees Only
* **Sibling Worktrees (`../<project>-<suffix>`) are PERMITTED:** For parallel task execution, isolated branch work, or multi-agent swarms, creating sibling worktrees outside the repository root is encouraged (e.g. `../fiber-2`, `../fiber-feature-combat`). Use `git worktree list` inside any project to inspect active worktrees.
* **Nested Worktrees (`.worktrees/`, `.claude/worktrees/`) are STRICTLY FORBIDDEN:** Never create a worktree or clone inside a project's own directory tree. In Godot projects, the engine, linter (`gdlint`), and test runner (`GUT`) recursively scan all directories; nested worktrees trigger duplicate class definitions, script errors, and double test runs.

### 2. Asking Design Decisions & Choices
* When prompting the user for architectural, game design, or implementation choices (e.g. during `/grilling`, wayfinder sessions, or triage), use interactive choice tools (`AskUserQuestion`, `ask_question`, or a structured multiple-choice picker).
* Put the recommended choice first with `(Recommended)` appended.
* Keep factual context in the preceding message; keep the question prompt and option labels clean and concise.

### 3. AFK Implementation Pipeline
* For asynchronous / background development:
  `Loose idea` → `/wayfinder-chart` → `/wayfinder` → `/wayfinder-handoff` → `implementation`
* Consult [`docs/agents/afk-pipeline.md`](./docs/agents/afk-pipeline.md) for full destination types, gate conditions, and artifact conventions.

### 4. Issue Tracking & Labels
* Issues and backlogs are managed via GitHub CLI (`gh`).
* Canonical triage labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`.
* See [`docs/agents/triage-labels.md`](./docs/agents/triage-labels.md) and [`docs/agents/issue-tracker.md`](./docs/agents/issue-tracker.md).

---

## Shared Skills Library

All agent skills are centralized in `.agents/skills/` (and mirrored in `.claude/skills/`):

### Engineering & Workflow (`mattpocock/skills` + `unslop`)
* **Specs & Design:** `/to-spec`, `/to-prd`, `/to-issues`, `/to-tickets`, `/domain-modeling`, `/codebase-design`, `/ubiquitous-language`
* **Interviewing:** `/grill-me`, `/grilling`, `/grill-with-docs`, `/ask-matt`
* **Execution & Quality:** `/implement`, `/tdd`, `/prototype`, `/diagnosing-bugs`, `/code-review`, `/qa`, `/improve-codebase-architecture`, `/resolving-merge-conflicts`, `/unslop`
* **Agent Operations:** `/wayfinder`, `/handoff`, `/triage`, `/teach`, `/writing-great-skills`

### Creative & Game Tooling
* **`/aseprite`**: Documentation, Lua API scripting, sprite-sheet export CLI, and animation workflows.
* **`/pixel-composer`**: VFX node graphs, particle systems, procedural shaders, and export pipelines.

### Pipeline Automations
* **`/wayfinder-chart`**: Start a wayfinder effort with declared destination type.
* **`/wayfinder-handoff`**: Hand off completed maps into implementation plans and labelled issues.

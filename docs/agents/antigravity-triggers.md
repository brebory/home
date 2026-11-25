# Antigravity Triggers (Gemini API) — Shared Nightly Routine Template

This guide and the reusable template under [`templates/antigravity-triggers/`](../../templates/antigravity-triggers/) port the [AFK Implementation Pipeline](afk-pipeline.md) routines to **Gemini API Antigravity Triggers** — cloud-hosted, cron-scheduled agents that run in a persistent Google-managed Linux sandbox even while your local machine is asleep.

---

## Plan & Billing Coverage (Read First)

- **Not covered directly by consumer subscription quota:** Google AI Pro and Google AI Ultra subscriptions do **not** include direct access to the Antigravity Preview Agent API (`antigravity-preview-09-2026`). Triggers run on the **Gemini API** (pay-as-you-go per model token + tools).
- **Covered via your plan's monthly Gemini API credits:** Google AI Pro and Ultra plans include recurring monthly Google Cloud / Gemini API credits redeemable inside Google AI Studio (each monthly grant rolls over and stays valid for 12 months):
  - **Google AI Pro:** \$10/month
  - **Google AI Ultra (5x):** \$40/month
  - **Google AI Ultra (20x):** \$100/month
- **Activation & Guardrails:**
  1. Sign in to [Google AI Studio](https://aistudio.google.com) with the primary subscriber account and click **Claim your free API credits** in the left menu.
  2. Complete the one-time \$5 prepaid billing deposit (required by Gemini API billing to unlock promotional credits; your monthly plan credits are drawn down first before touching the \$5).
  3. Set a **hard monthly spend cap** on your AI Studio project so unattended runs can never exceed your included credits.
  4. Keep `max_total_tokens` set in your trigger config (default `500000` per run — best-effort ceiling) and start on `gemini-3.8-flash` before considering heavier models.

> If you prefer zero API billing setup and don't mind your desktop staying awake, use **`/automation`** in the Antigravity App instead — it runs directly against your personal subscription quota.

---

## Template Layout

```text
templates/antigravity-triggers/
├── manage_triggers.py                        # Zero-dependency Python 3 CLI for Credentials & Triggers
├── trigger.config.example.json               # Generic starter config for any repo
└── prompts/
    ├── implement-routine.template.md         # Nightly `ready-for-agent` implementation prompt
    └── wayfinding-routine.template.md        # Nightly `wayfinder:map` frontier prompt
```

### Why this design?

- **Zero secret leakage:** Your GitHub PAT is stored once via the Gemini API **Credentials** endpoint (`type: "bearer_token"`). The sandbox's egress proxy injects `Authorization: Bearer <token>` on the wire for `api.github.com` and `github.com` — the raw token never exists inside container env vars or files.
- **Persistent sandbox, clean git state:** A trigger reuses the same Linux environment across runs (preserving downloaded toolchains and build caches), while every routine prompt opens with `git fetch origin && git checkout <branch> && git reset --hard origin/<branch> && git clean -fd`.
- **Single source of truth:** Each project only commits a small JSON config (schedule, repo, test command, extra rules). Running `manage_triggers.py update-trigger <id> --config ...` keeps the live cloud trigger synced with git.

---

## Quickstart (Per Project)

### 1. Create a scoped GitHub PAT & store it as a Gemini Credential

Create a fine-grained GitHub PAT scoped **only** to the target repository with:
- **Contents:** Read & write (push branches)
- **Issues:** Read & write (claim/comment/close wayfinding research tickets)
- **Pull requests:** Read & write (open PRs)

Store it once in your Gemini API project:
```bash
export GEMINI_API_KEY="your-ai-studio-api-key"
export GITHUB_TOKEN="github_pat_..."

python3 templates/antigravity-triggers/manage_triggers.py create-credential \
  --id github-<project>-pat
```

To rotate the PAT later without touching any trigger:
```bash
export GITHUB_TOKEN="github_pat_new..."
python3 templates/antigravity-triggers/manage_triggers.py rotate-credential \
  --id github-<project>-pat
```

### 2. Copy & customize a project trigger config

Copy [`trigger.config.example.json`](../../templates/antigravity-triggers/trigger.config.example.json) into your project repo (for example, `documentation/agents/antigravity-triggers/<project>-implement.trigger.json`) and fill in:
- `display_name`, `schedule`, `time_zone`
- `model` and `max_total_tokens`
- `prompt_template` (`prompts/implement-routine.template.md` or `prompts/wayfinding-routine.template.md`)
- `prompt_vars` (`PROJECT_NAME`, `REPO`, `DEFAULT_BRANCH`, `WORKSPACE_DIR`, `CONTEXT_FILE`, `TEST_CMD`, `EXTRA_RULES`)
- `environment.repo_url` and `environment.github_credential_id`

### 3. Dry-run, create, and smoke-test

```bash
# Inspect the exact rendered JSON payload first
python3 templates/antigravity-triggers/manage_triggers.py create-trigger \
  --config /path/to/<project>-implement.trigger.json \
  --dry-run

# Register the cloud trigger (save the returned `id`)
python3 templates/antigravity-triggers/manage_triggers.py create-trigger \
  --config /path/to/<project>-implement.trigger.json

# Fire a manual test run immediately and inspect execution status
python3 templates/antigravity-triggers/manage_triggers.py run <trigger_id>
python3 templates/antigravity-triggers/manage_triggers.py executions <trigger_id>
```

### 4. Day-to-day management

```bash
# List all triggers
python3 templates/antigravity-triggers/manage_triggers.py list

# Sync prompt or schedule changes to an existing trigger
python3 templates/antigravity-triggers/manage_triggers.py update-trigger <trigger_id> \
  --config /path/to/<project>-implement.trigger.json

# Pause / resume / delete
python3 templates/antigravity-triggers/manage_triggers.py pause <trigger_id>
python3 templates/antigravity-triggers/manage_triggers.py resume <trigger_id>
python3 templates/antigravity-triggers/manage_triggers.py delete <trigger_id>
```

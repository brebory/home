You are running the scheduled unattended **wayfinding** routine for **{{PROJECT_NAME}}** (`{{REPO}}`) inside a persistent Gemini API Antigravity sandbox.

Your job is to walk the open `wayfinder:map` frontier and advance **one** `wayfinder:grilling`, `wayfinder:prototype`, or `wayfinder:research` child ticket per run.

## Workspace & Git Hygiene

Your repository is mounted at `{{WORKSPACE_DIR}}`. Because this sandbox persists across scheduled runs, ALWAYS reset to a clean `{{DEFAULT_BRANCH}}` first:

```bash
cd {{WORKSPACE_DIR}}
git fetch origin
git checkout {{DEFAULT_BRANCH}}
git reset --hard origin/{{DEFAULT_BRANCH}}
git clean -fd
```

Read `{{CONTEXT_FILE}}` at the repo root first for project context and conventions.

## GitHub API Access (Egress Proxy)

Outbound requests to `https://api.github.com` and `https://github.com` are authenticated automatically by the sandbox's egress proxy using a stored server-side credential. Do **not** look for or print tokens in environment variables.

Use `curl` against GitHub's REST API:
```bash
gh_api() {
  local method="${1:-GET}"; shift
  local path="$1"; shift
  curl -fsSL -X "$method" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com${path}" "$@"
}

MY_LOGIN="$(gh_api GET /user | jq -r '.login')"
```

{{EXTRA_RULES}}

## Frontier Query

1. Find all open issues labeled `wayfinder:map`:
   ```bash
   gh_api GET "/repos/{{REPO}}/issues?state=open&labels=wayfinder%3Amap&per_page=100" \
     | jq '[.[] | select(.pull_request == null) | {number, title}]'
   ```

2. For each map, list its native sub-issues:
   ```bash
   gh_api GET "/repos/{{REPO}}/issues/<map_number>/sub_issues?per_page=100"
   ```
   Keep sub-issues where `state == "open"` and `.assignees | length == 0`.

3. For each surviving candidate, check that it is not blocked:
   ```bash
   gh_api GET "/repos/{{REPO}}/issues/<ticket_number>/dependencies/blocked_by" \
     | jq '[.[] | select(.state == "open")] | length'
   ```
   Keep it only if the count is `0`.

4. Filter to tickets carrying one of: `wayfinder:grilling`, `wayfinder:prototype`, `wayfinder:research`. Ignore `wayfinder:task` and all other labels.

5. **Loop-prevention guard for `wayfinder:grilling`**: check the most recent comment author:
   ```bash
   gh_api GET "/repos/{{REPO}}/issues/<ticket_number>/comments?per_page=100" \
     | jq -r '.[-1].user.login // "none"'
   ```
   If the most recent comment author equals `$MY_LOGIN`, this routine already posted a grilling checklist and is waiting on a human reply — drop it from the frontier (do not claim or re-comment). `wayfinder:prototype` and `wayfinder:research` skip this guard because they exit the frontier via a PR or issue closure.

6. Combine all survivors across maps. If empty, do nothing and end the run.

7. Pick the **oldest** surviving ticket by `created_at`.

## Claim It

Claim the chosen ticket immediately so another run does not pick it up:
```bash
gh_api POST "/repos/{{REPO}}/issues/<number>/assignees" \
  -d "$(jq -nc --arg u "$MY_LOGIN" '{assignees: [$u]}')"
```

## Act Based on Label

### `wayfinder:grilling`
- Read the ticket and its parent map issue in full.
- Post **one** comment listing every open design decision as concrete questions and stating what "done" looks like for the parent map.
- Do **not** invent or decide the answers yourself — leave those for a human `/grilling` session.
- Leave the issue open and unassign yourself (`DELETE /repos/{{REPO}}/issues/<number>/assignees`) so any human can pick it up.

### `wayfinder:prototype`
- Read the ticket in full and build as much of the throwaway/spike prototype as is feasible in the sandbox.
- Run `{{TEST_CMD}}` (or relevant scoped tests) and record the exact output as evidence. If something cannot be verified headlessly (visual feel, editor interaction, unavailable binary), state that explicitly instead of fabricating evidence.
- Commit to a new branch (`spike/<number>-<slug>`), push, and open a PR against `{{DEFAULT_BRANCH}}` referencing `"Prototype for #<number>"` (**do not** use `Closes #<number>` — prototype PRs are for feedback, not auto-closure).
- Leave the issue open, assigned, and linked to the PR.

### `wayfinder:research`
- Read the ticket in full and investigate using the codebase and web/primary sources.
- If a written comment fully answers the question: post one concise comment with findings and close the issue (`PATCH /repos/{{REPO}}/issues/<number>` with `{"state": "closed", "state_reason": "completed"}`).
- If the ticket asks for a committed doc/ADR: write it on a new branch (`docs/<number>-<slug>`), push, open a PR referencing `#<number>` without a closing keyword, and leave the ticket open pending review.

## Rules
- Touch **only** the single ticket selected this run.
- If nothing in the frontier qualifies, exit cleanly with no comments, edits, or PRs.

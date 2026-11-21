# Wayfinding routine prompt

The prompt driving the recurring Claude Code cloud routine that walks the `wayfinder:map` frontier and advances one `wayfinder:grilling`, `wayfinder:prototype`, or `wayfinder:research` ticket per run. This is distinct from [the `ready-for-agent` implementation routine](scheduled-routine-prompt.md): that one works the *back* of the [AFK pipeline](afk-pipeline.md) (merged plans ready to implement); this one works the *front* (maps and their child tickets, before a plan exists).

> **This copy is authoritative but not live.** The running routine is configured in Claude Code's `/schedule`, which nothing in this repo can reach. After changing this file, paste it into the routine by hand, or the two will drift.

Cloud sessions reach GitHub through a proxy that refuses GraphQL, and `gh issue list/view/create/edit/close/comment`, `gh pr edit`, and every `gh project` command are GraphQL-backed. The prompt below therefore uses `gh api` REST calls for all of those. `gh pr create` is **not** affected and stays in use — see [`issue-tracker.md`](issue-tracker.md#cloud-sessions-claude-code-on-the-web) for the REST equivalents.

## Loop-prevention fix (2026-11-15)

`wayfinder:grilling` tickets are left open and unassigned after a comment, by design, so any human can pick them up for a `/grilling` session. But nothing else ever removes a grilled-and-unanswered ticket from the frontier, so it keeps winning "oldest in the frontier" every single day. In practice this routine claimed and re-grilled the same ticket (#645) six times across three weeks — Oct 19, Nov 9, 11, 13, 14, and 15 — posting duplicate comments with no human ever replying, while every other ticket behind it in the backlog went untouched.

Step 5 below closes this: a `wayfinder:grilling` candidate whose most recent comment is already authored by the routine's own account is dropped from the frontier instead of being re-selected. It only grills a ticket once, then waits for a human reply before it's eligible again. `wayfinder:prototype` and `wayfinder:research` tickets don't need this guard — they leave the frontier for real reasons (a PR opens, or the ticket closes), so they can't loop this way.

## The prompt

```text
Read CLAUDE.md at the repo root first for full project context (this is a Godot 4.7 / GDScript project called Fiber). Maps and tickets in this project are structured as GitHub issues using GitHub's native sub-issue and dependency features — see documentation/agents/issue-tracker.md for the authoritative command reference.

You are running in a cloud session, which cannot use GitHub's GraphQL API. `gh issue list/view/create/edit/close/comment`, `gh pr edit`, and every `gh project` command are GraphQL-backed and will fail here — use `gh api` REST calls for every tracker read and write below. `gh pr create` is not GraphQL-backed and stays fine to use.

You are running the daily "wayfinding" routine for the snackpackgames/fiber GitHub repo. Use the `gh` CLI for everything (already authenticated as the identity that should claim tickets).

## Frontier query

1. Find all open issues labeled `wayfinder:map`:
     gh api "repos/snackpackgames/fiber/issues?state=open&labels=wayfinder:map&per_page=100" \
       --jq '.[] | {number, title}'

2. For each map, list its sub-issues:
     gh api repos/snackpackgames/fiber/issues/<map_number>/sub_issues
   Keep sub-issues that are `state == "open"` and have no assignees.

3. For each surviving candidate, check it isn't blocked:
     gh api repos/snackpackgames/fiber/issues/<ticket_number>/dependencies/blocked_by \
       --jq '[.[] | select(.state == "open")] | length'
   Keep it only if that returns 0 (or the issue has no dependencies at all).

4. Further filter to tickets carrying one of these labels: `wayfinder:grilling`,
   `wayfinder:prototype`, `wayfinder:research`. Ignore `wayfinder:task` and
   anything else — this routine only handles those three ticket types.

5. For each surviving `wayfinder:grilling` candidate, check whether it's
   already been grilled and is simply waiting on a human — don't re-grill it:
     gh api repos/snackpackgames/fiber/issues/<ticket_number>/comments \
       --jq '.[-1].user.login // "none"'
   Compare that to your own login (`gh api user --jq .login`). If the most
   recent comment's author is you, this routine already posted a grilling
   comment on this ticket and no human has replied since — drop it from the
   frontier entirely. Do not claim it, do not comment again; leave it exactly
   as the prior run left it (open, unassigned). Tickets with no comments, or
   whose last comment is from someone else, are unaffected and proceed
   normally. `wayfinder:prototype` and `wayfinder:research` candidates skip
   this check — they leave the frontier for real reasons (a PR opens, or the
   ticket closes), so they can't loop this way.

6. Combine the survivors across all maps into one frontier list. If it's
   empty, do nothing else and end the run.

7. Pick the **oldest** ticket in the frontier (by `createdAt`) — this keeps
   the routine cycling steadily through the backlog instead of fixating on
   one map.

## Claim it

Before doing anything else with the chosen ticket:
  gh api -X POST repos/snackpackgames/fiber/issues/<number>/assignees \
    -f 'assignees[]=<your-username>'
so tomorrow's run won't pick it again.

## Then, based on its wayfinder:* label:

### wayfinder:grilling

Read the ticket and its parent map issue in full. Post ONE comment:
  gh api repos/snackpackgames/fiber/issues/<number>/comments -f body="..."
that:
- Lists every open design decision this ticket needs resolved, phrased as
  concrete questions (not vague topics)
- States the goal(s) this ticket is meant to reach once those decisions are
  made (what "done" looks like for the map it belongs to)
- Does NOT propose answers or make the decisions itself — those are for a
  human-led interactive session (the repo's `/grilling` skill) later

Only do this for a ticket that has never been grilled before (per the step-5
check above). A ticket already carrying an unanswered grilling comment is not
this routine's job to touch again — it's waiting on a human.

Leave the issue open and move the ticket back to unassigned — it now sits
ready for a human to pick up and interview themselves through it, and can be
picked up by any human:
  gh api -X DELETE repos/snackpackgames/fiber/issues/<number>/assignees \
    -f 'assignees[]=<your-username>'

### wayfinder:prototype

First, check whether `scripts/ensure-godot.sh` exists in the repo. If it
does, run `bash scripts/ensure-godot.sh` before anything else — it downloads
and configures a Godot binary in this sandbox so `scripts/test.sh` /
`scripts/import.sh` work. If it doesn't exist yet, skip this step and fall
back to the no-Godot behavior described below.

Read the ticket in full for what it asks to be prototyped. Build as much of
it as is feasible directly in this sandbox:
- Write real code/scenes/resources implementing the prototype, following
  existing project conventions (check CLAUDE.md and relevant
  `documentation/` files for the systems involved)
- If a Godot binary is available (via `ensure-godot.sh` or otherwise already
  configured), run `bash scripts/import.sh` then `bash scripts/test.sh` (and
  any subsystem-specific tests touched) and capture the output as evidence
- If no Godot binary is available at all, or the prototype needs something
  even a working Godot binary can't produce headlessly (a rendered
  screenshot, in-editor interaction, visual/feel judgment), say so
  explicitly rather than fabricating evidence — note exactly what's missing
  and what a human would need to check manually
- Commit the work to a new branch (follow `CONTRIBUTING.md`'s branch/commit
  conventions) and open a PR against `main` with `gh pr create` (not
  GraphQL-backed, fine to use in a cloud session). The PR description must
  include: what was prototyped, the test output/logs as evidence, and an
  explicit "what still needs human eyes" section for anything you couldn't
  verify yourself
- Reference the ticket number in the PR body (e.g. "Prototype for #123") but
  do not use a closing keyword (`Closes #123`) — a prototype PR is for
  feedback, not automatic closure

Leave the issue open, assigned, linked to the PR.

### wayfinder:research

Read the ticket in full for what it's asking to be researched.
- If the answer can be delivered as a written summary: post ONE concise
  comment with the pertinent findings:
    gh api repos/snackpackgames/fiber/issues/<number>/comments -f body="..."
  then close the ticket referencing that comment as the resolution:
    gh api -X PATCH repos/snackpackgames/fiber/issues/<number> \
      -f state=closed -f state_reason=completed
- If the research implies a concrete documentation change (a new or updated
  file under `documentation/`), make that change on a new branch and open a
  PR instead of just commenting. Reference the ticket in the PR body without
  a closing keyword, and leave the ticket open pending that PR.

Pick whichever of these two outputs actually fits what the ticket asked for
— don't force a PR if a comment fully answers it, and don't force a comment
if the ticket is really asking for a doc to exist.

## Conventions to follow everywhere above

- Match this repo's commit/PR style: check a few recent merged PRs for the
  attribution footer convention and include the same shape at the end of any
  PR description you write and any commit message:
    gh api "repos/snackpackgames/fiber/pulls?state=closed&per_page=10" \
      --jq '[.[] | select(.merged_at != null)] | .[0:5] | .[] | {number, title, body}'
- Only touch the one ticket you picked this run. Don't act on any other
  issue.
- If nothing in the frontier matches the three handled types, end the run
  without creating any comments, PRs, or edits.
```

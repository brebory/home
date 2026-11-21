# Claude Code Entrypoint

Please read and follow [@AGENTS.md](./AGENTS.md) for the project index, worktree rules, and global agent conventions.

## Claude Code Specifics
- **Skills**: Shared skills are available under `.claude/skills/` and `.agents/skills/`.
- **Worktrees**: Sibling worktrees (`../<repo>-<suffix>`) are permitted. Never use `EnterWorktree` into `.claude/worktrees/` because nested worktrees break Godot engine scanning and test suites.
- **Local Overrides**: Machine-specific configurations or tokens should be placed in `AGENTS.local.md` or `.claude/settings.local.json` (both are gitignored).

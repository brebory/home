#!/usr/bin/env python3
"""Manage Gemini API Antigravity Triggers and stored credentials.

Zero third-party dependencies (Python 3.9+ stdlib only).

Environment variables:
  GEMINI_API_KEY   Required for all non-dry-run API calls.
  GITHUB_TOKEN     Default env var read by create-credential / rotate-credential.

Examples:
  # 1. Store a write-only GitHub PAT in Gemini Credentials (egress proxy)
  python3 manage_triggers.py create-credential --id github-ansible-pat

  # 2. Preview the rendered trigger payload without calling the API
  python3 manage_triggers.py create-trigger --config path/to/config.json --dry-run

  # 3. Create the scheduled trigger
  python3 manage_triggers.py create-trigger --config path/to/config.json

  # 4. Run a trigger immediately to verify permissions & auth
  python3 manage_triggers.py run <trigger_id>
  python3 manage_triggers.py executions <trigger_id>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
SCRIPT_DIR = Path(__file__).resolve().parent
PLACEHOLDER_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"Error: environment variable {name} is not set.")
    return value


def api_request(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    api_key = require_env("GEMINI_API_KEY")
    url = f"{API_BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "x-goog-api-key": api_key,
        "Accept": "application/json",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8").strip()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        sys.exit(f"HTTP {exc.code} {method} {url}\n{body}")
    except urllib.error.URLError as exc:
        sys.exit(f"Network error calling {url}: {exc.reason}")


def resolve_template_path(template_ref: str, config_dir: Path) -> Path:
    candidate = Path(template_ref)
    if candidate.is_absolute() and candidate.is_file():
        return candidate
    for base in (config_dir, SCRIPT_DIR):
        resolved = (base / candidate).resolve()
        if resolved.is_file():
            return resolved
    sys.exit(
        f"Error: prompt_template '{template_ref}' not found relative to "
        f"{config_dir} or {SCRIPT_DIR}."
    )


def render_prompt(config: dict[str, Any], config_path: Path) -> str:
    if "prompt" in config and config["prompt"]:
        return str(config["prompt"])

    template_ref = config.get("prompt_template")
    if not template_ref:
        sys.exit("Error: config must specify either 'prompt' or 'prompt_template'.")

    template_path = resolve_template_path(str(template_ref), config_path.parent)
    template_text = template_path.read_text(encoding="utf-8")
    prompt_vars: dict[str, Any] = config.get("prompt_vars") or {}

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in prompt_vars:
            sys.exit(
                f"Error: template {template_path.name} requires prompt_vars['{key}'], "
                f"which is missing from {config_path}."
            )
        return str(prompt_vars[key])

    rendered = PLACEHOLDER_RE.sub(replace, template_text)
    leftover = PLACEHOLDER_RE.findall(rendered)
    if leftover:
        sys.exit(f"Error: unresolved placeholders after rendering: {leftover}")
    return rendered


def build_trigger_payload(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    prompt_text = render_prompt(config, config_path)
    env_cfg = config.get("environment") or {}

    repo_url = env_cfg.get("repo_url")
    target_dir = env_cfg.get("target_dir", "/workspace/repo")
    github_cred = env_cfg.get("github_credential_id")

    allowlist: list[dict[str, Any]] = []
    if github_cred:
        allowlist.append({"domain": "api.github.com", "credential": github_cred})
        allowlist.append({"domain": "github.com", "credential": github_cred})

    for domain in env_cfg.get("extra_allowed_domains") or []:
        if isinstance(domain, str):
            allowlist.append({"domain": domain})
        elif isinstance(domain, dict):
            allowlist.append(domain)

    if env_cfg.get("allow_unlisted_egress", True):
        allowlist.append({"domain": "*"})

    environment: dict[str, Any] = {"type": "remote"}
    if repo_url:
        environment["sources"] = [
            {
                "type": "repository",
                "source": repo_url,
                "target": target_dir,
            }
        ]
    if env_cfg.get("env"):
        environment["env"] = env_cfg["env"]
    if allowlist:
        environment["network"] = {"allowlist": allowlist}

    agent_config: dict[str, Any] = {"type": "antigravity"}
    if config.get("model"):
        agent_config["model"] = config["model"]
    if config.get("max_total_tokens") is not None:
        agent_config["max_total_tokens"] = str(config["max_total_tokens"])

    interaction: dict[str, Any] = {
        "agent": config.get("agent", "antigravity-preview-09-2026"),
        "agent_config": agent_config,
        "input": [{"type": "text", "text": prompt_text}],
        "environment": environment,
    }

    payload: dict[str, Any] = {
        "display_name": config["display_name"],
        "schedule": config["schedule"],
        "time_zone": config["time_zone"],
        "max_consecutive_failures": int(config.get("max_consecutive_failures", 3)),
        "execution_timeout_seconds": int(config.get("execution_timeout_seconds", 1800)),
        "interaction": interaction,
    }
    return payload


def cmd_create_credential(args: argparse.Namespace) -> None:
    token = require_env(args.token_env)
    payload = {
        "id": args.id,
        "type": "bearer_token",
        "token": token,
    }
    if args.dry_run:
        redacted = {**payload, "token": "***REDACTED***"}
        print(json.dumps(redacted, indent=2))
        return
    result = api_request("POST", "/credentials", payload)
    print(json.dumps(result, indent=2))


def cmd_rotate_credential(args: argparse.Namespace) -> None:
    token = require_env(args.token_env)
    payload = {
        "type": "bearer_token",
        "token": token,
    }
    if args.dry_run:
        redacted = {**payload, "token": "***REDACTED***"}
        print(json.dumps(redacted, indent=2))
        return
    result = api_request("PATCH", f"/credentials/{args.id}", payload)
    print(json.dumps(result, indent=2))


def cmd_list_credentials(_args: argparse.Namespace) -> None:
    result = api_request("GET", "/credentials")
    print(json.dumps(result, indent=2))


def cmd_create_trigger(args: argparse.Namespace) -> None:
    config_path = Path(args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    payload = build_trigger_payload(config, config_path)
    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return
    result = api_request("POST", "/triggers", payload)
    print(json.dumps(result, indent=2))


def cmd_update_trigger(args: argparse.Namespace) -> None:
    config_path = Path(args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    payload = build_trigger_payload(config, config_path)
    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return
    result = api_request("PATCH", f"/triggers/{args.trigger_id}", payload)
    print(json.dumps(result, indent=2))


def cmd_list_triggers(_args: argparse.Namespace) -> None:
    result = api_request("GET", "/triggers")
    print(json.dumps(result, indent=2))


def cmd_get_trigger(args: argparse.Namespace) -> None:
    result = api_request("GET", f"/triggers/{args.trigger_id}")
    print(json.dumps(result, indent=2))


def cmd_run_trigger(args: argparse.Namespace) -> None:
    result = api_request("POST", f"/triggers/{args.trigger_id}/executions", {})
    print(json.dumps(result, indent=2))


def cmd_executions(args: argparse.Namespace) -> None:
    result = api_request("GET", f"/triggers/{args.trigger_id}/executions")
    print(json.dumps(result, indent=2))


def cmd_set_status(args: argparse.Namespace, status: str) -> None:
    result = api_request("PATCH", f"/triggers/{args.trigger_id}", {"status": status})
    print(json.dumps(result, indent=2))


def cmd_delete_trigger(args: argparse.Namespace) -> None:
    result = api_request("DELETE", f"/triggers/{args.trigger_id}")
    print(json.dumps(result, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage Gemini API Antigravity Triggers and stored credentials."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create-credential", help="Store a write-only GitHub PAT credential.")
    p.add_argument("--id", required=True, help="Credential ID (e.g. github-ansible-pat).")
    p.add_argument("--token-env", default="GITHUB_TOKEN", help="Env var holding the PAT.")
    p.add_argument("--dry-run", action="store_true", help="Print redacted request payload only.")
    p.set_defaults(func=cmd_create_credential)

    p = sub.add_parser("rotate-credential", help="Rotate an existing stored credential.")
    p.add_argument("--id", required=True, help="Credential ID to rotate.")
    p.add_argument("--token-env", default="GITHUB_TOKEN", help="Env var holding the new PAT.")
    p.add_argument("--dry-run", action="store_true", help="Print redacted request payload only.")
    p.set_defaults(func=cmd_rotate_credential)

    p = sub.add_parser("list-credentials", help="List stored credentials.")
    p.set_defaults(func=cmd_list_credentials)

    p = sub.add_parser("create-trigger", help="Create a scheduled trigger from a config JSON.")
    p.add_argument("--config", required=True, help="Path to trigger config JSON.")
    p.add_argument("--dry-run", action="store_true", help="Print rendered payload and exit.")
    p.set_defaults(func=cmd_create_trigger)

    p = sub.add_parser("update-trigger", help="Update an existing trigger from a config JSON.")
    p.add_argument("trigger_id", help="Trigger ID to update.")
    p.add_argument("--config", required=True, help="Path to trigger config JSON.")
    p.add_argument("--dry-run", action="store_true", help="Print rendered payload and exit.")
    p.set_defaults(func=cmd_update_trigger)

    p = sub.add_parser("list", help="List all triggers in this Gemini API project.")
    p.set_defaults(func=cmd_list_triggers)

    p = sub.add_parser("get", help="Get details for a single trigger.")
    p.add_argument("trigger_id", help="Trigger ID.")
    p.set_defaults(func=cmd_get_trigger)

    p = sub.add_parser("run", help="Fire a trigger immediately (even if paused).")
    p.add_argument("trigger_id", help="Trigger ID.")
    p.set_defaults(func=cmd_run_trigger)

    p = sub.add_parser("executions", help="List past executions for a trigger.")
    p.add_argument("trigger_id", help="Trigger ID.")
    p.set_defaults(func=cmd_executions)

    p = sub.add_parser("pause", help="Pause scheduled runs for a trigger.")
    p.add_argument("trigger_id", help="Trigger ID.")
    p.set_defaults(func=lambda a: cmd_set_status(a, "paused"))

    p = sub.add_parser("resume", help="Resume scheduled runs for a trigger.")
    p.add_argument("trigger_id", help="Trigger ID.")
    p.set_defaults(func=lambda a: cmd_set_status(a, "active"))

    p = sub.add_parser("delete", help="Permanently delete a trigger.")
    p.add_argument("trigger_id", help="Trigger ID.")
    p.set_defaults(func=cmd_delete_trigger)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Manage authentication with the keyed package index."""

from __future__ import annotations

import difflib
import os
import re
import sys
import time
import webbrowser
from pathlib import Path
from stat import S_IMODE
from typing import Any

import requests
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm
from rich.table import Table

console = Console()

CLIENT_ID = "Iv23liYfluVCvdF3yHnd"
DEVICE_URL = "https://github.com/login/device/code"
TOKEN_URL = "https://github.com/login/oauth/access_token"
API_URL = "https://api.github.com/user"

PKG_HOST = os.getenv("KEYED_INDEX_HOST", "pkgs.keyed.dev")
NETRC = Path.home() / ("_netrc" if os.name == "nt" else ".netrc")

# Match the complete machine block from machine line to password line
HOST_BLOCK_RE = re.compile(rf"(?ms)^machine\s+{re.escape(PKG_HOST)}\b.*?^password\s+\S+")
LOGIN_RE = re.compile(r"\blogin\s+(\S+)")
PASSWORD_RE = re.compile(r"\bpassword\s+(\S+)")

ENTRY_TEMPLATE = "machine {host}\nlogin {login}\npassword {password}"

# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------


def _device_flow() -> tuple[str, str, str, int]:
    r = requests.post(
        DEVICE_URL,
        data={"client_id": CLIENT_ID, "scope": "read:user"},
        headers={"Accept": "application/json"},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    return data["device_code"], data["user_code"], data["verification_uri"], data["interval"]


def _poll_token(device_code: str, interval: int) -> str:
    max_attempts = 60  # 10 minutes (10 s * 60)
    attempts = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Waiting for GitHub authorization…", total=None)

        while attempts < max_attempts:
            attempts += 1
            time.sleep(interval)

            r = requests.post(
                TOKEN_URL,
                data={
                    "client_id": CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"Accept": "application/json"},
                timeout=10,
            )
            data = r.json()

            if "access_token" in data:
                progress.update(task, description="✅ Authorization successful!")
                return data["access_token"]

            if data.get("error") == "authorization_pending":
                continue
            if data.get("error") == "slow_down":
                interval += 5
                continue

            progress.update(task, description=f"❌ OAuth error: {data.get('error')}")
            raise RuntimeError(data.get("error_description", "OAuth error"))

        progress.update(task, description="❌ Authentication timed out")
        raise RuntimeError("Authentication timed out. Please try again.")


def _query_github_user(token: str) -> dict[str, Any]:
    r = requests.get(API_URL, headers={"Authorization": f"Bearer {token}"}, timeout=10)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# .netrc helpers
# ---------------------------------------------------------------------------


def _parse_netrc_block(block: str) -> tuple[str | None, str | None]:
    login = LOGIN_RE.search(block)
    password = PASSWORD_RE.search(block)
    return (login.group(1) if login else None, password.group(1) if password else None)


def _write_netrc(text: str) -> None:
    existed = NETRC.exists()
    bad_perms = existed and S_IMODE(NETRC.stat().st_mode) != 0o600
    if bad_perms:
        console.print(f"[yellow]{NETRC} is world-readable. pip will ignore it.[/yellow]")
        if not Confirm.ask("Fix permissions to 600?", default=True):
            console.print("[red]Aborted - insecure permissions left unchanged[/red]")
            sys.exit(1)
    NETRC.write_text(text)
    NETRC.chmod(0o600)


def _show_diff(old: str, new: str) -> bool:
    """Render unified diff and return True if user approves."""
    if old == new:
        console.print("[green]No changes necessary.[/green]")
        return False

    diff_lines = difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        fromfile=str(NETRC),
        tofile=f"{NETRC} (new)",
        lineterm="",
    )
    console.print(Panel("\n".join(diff_lines), title="Proposed .netrc changes", style="cyan"))
    return Confirm.ask("Apply these changes?", default=True)


def _save_credentials(login: str, password: str) -> None:
    entry = ENTRY_TEMPLATE.format(host=PKG_HOST, login=login, password=password)
    old_content = NETRC.read_text() if NETRC.exists() else ""
    match = HOST_BLOCK_RE.search(old_content)

    if match:
        # Split into before/match/after using positions
        before = old_content[: match.start()]
        after = old_content[match.end() :]

        # Handle spacing more carefully
        if not before and not after:
            # Only this block exists
            new_content = entry + "\n"
        elif not before:
            # Block at start of file
            new_content = entry + after
        elif not after.strip():
            # Block at end of file (after might have trailing whitespace)
            new_content = f"{before.rstrip()}\n\n{entry}\n"
        else:
            # Block in middle - preserve surrounding spacing patterns
            # Keep any leading newlines in 'after' to maintain spacing
            new_content = f"{before}{entry}{after}"
    else:
        # Adding new block
        new_content = f"{entry}\n" if not old_content else f"{old_content.rstrip()}\n\n{entry}\n"

    if _show_diff(old_content, new_content):
        _write_netrc(new_content)
        console.print(f"[green]Credentials saved to {NETRC}[/green]")
    else:
        console.print("[red]Aborted - no changes were made[/red]")
        sys.exit(1)


def _remove_credentials() -> None:
    if not NETRC.exists():
        console.print("[yellow]No credentials found.[/yellow]")
        return

    old_content = NETRC.read_text()
    match = HOST_BLOCK_RE.search(old_content)

    if not match:
        console.print("[yellow]No credentials found for this host.[/yellow]")
        return

    # Split into before/after using positions
    before = old_content[: match.start()]
    after = old_content[match.end() :]

    # Handle spacing when removing the block
    if not before.strip() and not after.strip():
        # Only this block existed
        new_content = ""
    elif not before.strip():
        # Block was at start - keep after content, remove leading whitespace
        new_content = after.lstrip()
    elif not after.strip():
        # Block was at end - keep before content, ensure single trailing newline
        new_content = before.rstrip() + "\n" if before.rstrip() else ""
    else:
        # Block was in middle - join before and after with appropriate spacing
        before_clean = before.rstrip()
        # Check if there are blank lines in 'after' to preserve spacing
        after_lines = after.lstrip("\n")
        if before_clean and after_lines:
            new_content = before_clean + "\n\n" + after_lines
        else:
            new_content = before_clean + after_lines

    if _show_diff(old_content, new_content):
        _write_netrc(new_content)
        console.print("[green]Credentials removed.[/green]")
    else:
        console.print("[red]Aborted - no changes were made[/red]")
        sys.exit(1)


def _get_saved_credentials() -> tuple[str, str] | None:
    if not NETRC.exists():
        return None
    block_match = HOST_BLOCK_RE.search(NETRC.read_text())
    if not block_match:
        return None
    return _parse_netrc_block(block_match.group(0))  # type: ignore[return-value]


def _test_package_repository_access(username: str, token: str) -> tuple[bool, str]:
    try:
        response = requests.get(f"https://{PKG_HOST}/auth/verify", auth=(username, token), timeout=10)
    except requests.ConnectionError:
        return False, f"Could not connect to {PKG_HOST}"
    except requests.Timeout:
        return False, "Request timed out"
    except requests.RequestException as e:
        return False, f"Request failed: {e}"

    if response.status_code == 200:
        return True, "Package repository access verified"
    if response.status_code == 401:
        return False, "Authentication failed - check your sponsorship status"
    return False, f"Unexpected response: {response.status_code}"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def login() -> None:
    """Authenticate and create/update the netrc entry for keyed package index."""

    console.print(Panel("Sign in with GitHub to access Keyed packages", title="🔑 Keyed Login"))
    device_code, user_code, url, interval = _device_flow()
    console.print(f"1. Open [cyan]{url}[/cyan]\n2. Enter code: [bold yellow]{user_code}[/bold yellow]")
    if Confirm.ask("Open browser now?", default=True):
        webbrowser.open(url)

    token = _poll_token(device_code, interval)
    user = _query_github_user(token)["login"]
    console.print(f"[green]Authenticated as {user}[/green]")

    _save_credentials(user, token)
    console.print(f"\nInstall with:\n  pip install --index-url https://{PKG_HOST}/simple/ keyed-extras")


def status() -> None:
    """Check whether the .netrc contains creds and whether token works."""
    creds = _get_saved_credentials()
    table = Table(title="Keyed status")
    table.add_column("Check")
    table.add_column("Value")

    if not creds:
        table.add_row(f"{PKG_HOST} {NETRC} entry", "[red]missing[/red]")
        console.print(table)
        return

    user, token = creds
    table.add_row("Saved user", user)

    try:
        _query_github_user(token)
        ok = True
    except requests.RequestException:
        ok = False

    table.add_row("Token valid", "✅" if ok else "❌")
    console.print(table)


def verify() -> None:
    """Verify that saved credentials can access the package repository."""
    creds = _get_saved_credentials()

    if not creds:
        console.print("[red]No saved credentials found[/red]")
        console.print("Run 'keyed login' first")
        sys.exit(1)

    user, token = creds
    console.print(f"Testing access for user: {user}")

    success, message = _test_package_repository_access(user, token)

    if success:
        console.print(f"[green]✅ {message}[/green]")
        console.print("You can install packages with:")
        console.print(f"  pip install --index-url https://{PKG_HOST}/simple/ keyed-extras")
    else:
        console.print(f"[red]❌ {message}[/red]")
        if "sponsorship" in message.lower():
            console.print("Make sure you're sponsoring/have access to https://github.com/dougmercer-yt/keyed-extras.")
        console.print("Try running 'keyed login' again")
        sys.exit(1)


def logout() -> None:
    """Remove the netrc entry for keyed package index."""
    creds = _get_saved_credentials()

    if not creds:
        console.print("[yellow]Not logged in[/yellow]")
        return

    user, _ = creds
    if Confirm.ask(f"Remove credentials for {user}?", default=False):
        _remove_credentials()

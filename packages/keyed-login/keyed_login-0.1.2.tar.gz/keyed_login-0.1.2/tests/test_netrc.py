from __future__ import annotations

import stat
from typing import TYPE_CHECKING

import pytest

import keyed_login.core as kl

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Pytest fixtures & helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _always_confirm(monkeypatch):
    """Silence all interactive prompts."""
    monkeypatch.setattr(kl.Confirm, "ask", staticmethod(lambda *a, **k: True))
    monkeypatch.setattr(kl, "_show_diff", lambda _old, _new: True)


@pytest.fixture
def netrc_path(tmp_path: Path, monkeypatch):
    """Patch kl.NETRC to point inside tmp_path and return that Path."""
    new_path = tmp_path / ".netrc"
    monkeypatch.setattr(kl, "NETRC", new_path)
    return new_path


def _read(path: Path) -> str:
    return path.read_text() if path.exists() else ""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_parse_netrc_block():
    block = "machine pkgs.keyed.dev\nlogin alice\npassword s3cret"
    assert kl._parse_netrc_block(block) == ("alice", "s3cret")


# ---- _save_credentials ----------------------------------------------------


def test_save_credentials_creates_new_file(netrc_path):
    kl._save_credentials("alice", "tok123")

    expected = kl.ENTRY_TEMPLATE.format(host=kl.PKG_HOST, login="alice", password="tok123") + "\n"
    assert _read(netrc_path) == expected
    # Permissions must be 0600
    assert stat.S_IMODE(netrc_path.stat().st_mode) == 0o600


def test_save_credentials_appends_block(netrc_path):
    # Prepopulate .netrc with an unrelated block
    netrc_path.write_text("machine other\n  login bob\n  password p\n")
    netrc_path.chmod(0o600)

    kl._save_credentials("alice", "tok123")

    expected = f"""machine other
  login bob
  password p

{kl.ENTRY_TEMPLATE.format(host=kl.PKG_HOST, login="alice", password="tok123")}
"""
    print(expected)
    print(_read(netrc_path))
    assert _read(netrc_path) == expected


def test_save_credentials_replaces_existing_block(netrc_path):
    old_block = kl.ENTRY_TEMPLATE.format(host=kl.PKG_HOST, login="old", password="oldtok")
    netrc_path.write_text(old_block + "\n")
    netrc_path.chmod(0o600)

    kl._save_credentials("alice", "newtok")

    expected = kl.ENTRY_TEMPLATE.format(host=kl.PKG_HOST, login="alice", password="newtok") + "\n"
    assert _read(netrc_path) == expected


# ---- _get_saved_credentials -----------------------------------------------


def test_get_saved_credentials(netrc_path):
    entry = kl.ENTRY_TEMPLATE.format(host=kl.PKG_HOST, login="alice", password="tok")
    netrc_path.write_text(entry + "\n")

    assert kl._get_saved_credentials() == ("alice", "tok")


# ---- _remove_credentials ---------------------------------------------------


def test_remove_credentials(netrc_path):
    """Host block is in the middle of the file — verify it disappears."""
    content = f"""machine first
login a
password a

{kl.ENTRY_TEMPLATE.format(host=kl.PKG_HOST, login="alice", password="tok")}

machine last
login z
password z
"""
    netrc_path.write_text(content)
    netrc_path.chmod(0o600)

    kl._remove_credentials()

    remaining = _read(netrc_path)
    assert "pkgs.keyed.dev" not in remaining  # removed
    assert "machine first" in remaining  # retained
    assert "machine last" in remaining  # retained


def test_remove_credentials_when_none(monkeypatch, netrc_path, capsys):
    # Empty file: no Keyed block
    netrc_path.touch(0o600)
    kl._remove_credentials()
    captured = capsys.readouterr().out
    assert "No credentials found" in captured


def test_get_saved_credentials_none_on_missing(monkeypatch, tmp_path):
    # Point to non‑existent file
    monkeypatch.setattr(kl, "NETRC", tmp_path / ".netrc-not-there")
    assert kl._get_saved_credentials() is None


def test_write_netrc_insecure_permissions(monkeypatch, netrc_path):
    # Pre‑create file with world‑readable perms
    netrc_path.write_text("dummy")
    netrc_path.chmod(0o644)

    # Simulate user refusing to fix perms
    monkeypatch.setattr(kl.Confirm, "ask", staticmethod(lambda *a, **k: False))

    with pytest.raises(SystemExit):
        kl._write_netrc("new")

    # File must remain unchanged
    assert _read(netrc_path) == "dummy"
    assert kl.S_IMODE(netrc_path.stat().st_mode) == 0o644


def test_parse_netrc_block_edge_cases():
    # Missing login
    assert kl._parse_netrc_block("machine host\npassword secret") == (None, "secret")

    # Missing password
    assert kl._parse_netrc_block("machine host\nlogin user") == ("user", None)

    # Malformed/empty block
    assert kl._parse_netrc_block("machine host") == (None, None)

    # Extra whitespace
    assert kl._parse_netrc_block("machine host\n  login   user  \n  password   secret  ") == ("user", "secret")

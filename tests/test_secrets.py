from __future__ import annotations

import subprocess
from pathlib import Path

from autotrade.exec.secrets import filled_secret_names, load_bybit_env, resolve_secrets_file


def test_filled_secret_names_ignores_empty():
    text = "BYBIT_API_KEY=\nBYBIT_API_SECRET=\n"
    assert filled_secret_names(text) == []


def test_filled_secret_names_detects_values():
    text = "BYBIT_API_KEY=abc\nBYBIT_API_SECRET=def\n"
    assert filled_secret_names(text) == ["BYBIT_API_KEY", "BYBIT_API_SECRET"]


def test_resolve_prefers_txt_when_env_missing(tmp_path: Path):
    txt = tmp_path / "bybit.txt"
    txt.write_text(
        "BYBIT_ENV=demo\nBYBIT_API_KEY=\nBYBIT_API_SECRET=\n"
        "BYBIT_BASE_URL=https://api-testnet.bybit.com\n",
        encoding="utf-8",
    )
    resolved = resolve_secrets_file(tmp_path / "bybit.env")
    assert resolved == txt
    creds = load_bybit_env(tmp_path / "bybit.env")
    assert creds.path == txt
    assert not creds.has_keys


def test_git_index_secrets_have_no_keys():
    files = subprocess.check_output(["git", "ls-files", "secrets"], text=True).splitlines()
    assert files, "secrets files should be tracked"
    for rel in files:
        blob = subprocess.check_output(["git", "show", f":{rel}"], text=True)
        assert filled_secret_names(blob) == [], rel

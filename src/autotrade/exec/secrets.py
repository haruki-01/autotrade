"""Load API keys from secrets/<env>/bybit.txt (visible) or bybit.env. Never log values."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

_KEY_NAMES = ("BYBIT_API_KEY", "BYBIT_API_SECRET")


@dataclass(frozen=True)
class BybitCreds:
    env: str
    api_key: str
    api_secret: str
    base_url: str
    path: Path

    @property
    def has_keys(self) -> bool:
        return bool(self.api_key and self.api_secret)


def parse_env_text(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def filled_secret_names(text: str) -> list[str]:
    data = parse_env_text(text)
    return [name for name in _KEY_NAMES if data.get(name)]


def resolve_secrets_file(path: str | Path) -> Path:
    path = Path(path)
    candidates = [path]
    if path.suffix == ".txt":
        candidates.append(path.with_suffix(".env"))
    elif path.suffix == ".env":
        candidates.append(path.with_name(f"{path.stem}.txt"))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"{path} がありません。左の一覧から secrets/demo/bybit.txt を開くか、"
        "PYTHONPATH=src python3 -m autotrade.cli secrets-init を実行してください。"
    )


def load_bybit_env(path: str | Path) -> BybitCreds:
    path = resolve_secrets_file(path)
    data = parse_env_text(path.read_text(encoding="utf-8"))
    env = (data.get("BYBIT_ENV") or "demo").lower()
    return BybitCreds(
        env=env,
        api_key=data.get("BYBIT_API_KEY") or "",
        api_secret=data.get("BYBIT_API_SECRET") or "",
        base_url=(data.get("BYBIT_BASE_URL") or "https://api-testnet.bybit.com").rstrip("/"),
        path=path,
    )


def protect_from_commit(path: str | Path) -> None:
    """Keep local key edits out of git status when the file is tracked."""
    path = Path(path)
    if not path.exists():
        return
    subprocess.run(
        ["git", "update-index", "--skip-worktree", str(path)],
        check=False,
        capture_output=True,
    )


def assert_demo_only(creds: BybitCreds) -> None:
    if "testnet" not in creds.base_url.lower():
        raise SystemExit(
            "demo コマンドは testnet の URL だけを受け付けます。"
            "secrets/demo/bybit.txt の BYBIT_BASE_URL=https://api-testnet.bybit.com"
        )
    if creds.env not in {"demo", "testnet"}:
        raise SystemExit(f"BYBIT_ENV={creds.env} は demo では使えません（demo|testnet）。")

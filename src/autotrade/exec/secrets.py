"""Load API keys from secrets/<env>/bybit.env. Never log values."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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


def load_bybit_env(path: str | Path) -> BybitCreds:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} がありません。cp secrets/demo/bybit.env.example secrets/demo/bybit.env"
        )
    data: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip('"').strip("'")
    env = (data.get("BYBIT_ENV") or "demo").lower()
    return BybitCreds(
        env=env,
        api_key=data.get("BYBIT_API_KEY") or "",
        api_secret=data.get("BYBIT_API_SECRET") or "",
        base_url=(data.get("BYBIT_BASE_URL") or "https://api-testnet.bybit.com").rstrip("/"),
        path=path,
    )


def assert_demo_only(creds: BybitCreds) -> None:
    if "testnet" not in creds.base_url.lower():
        raise SystemExit(
            "demo コマンドは testnet の URL だけを受け付けます。"
            "secrets/demo/bybit.env の BYBIT_BASE_URL=https://api-testnet.bybit.com"
        )
    if creds.env not in {"demo", "testnet"}:
        raise SystemExit(f"BYBIT_ENV={creds.env} は demo では使えません（demo|testnet）。")

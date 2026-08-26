"""Bybit v5 signed REST. Testnet only from the demo command."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from autotrade.exec.secrets import BybitCreds


def sign(secret: str, payload: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


class BybitPrivateClient:
    def __init__(self, creds: BybitCreds, *, recv_window: int = 5000, timeout: float = 20.0):
        self.creds = creds
        self.recv_window = recv_window
        self.timeout = timeout

    def _headers(self, timestamp: str, payload: str) -> dict[str, str]:
        prehash = f"{timestamp}{self.creds.api_key}{self.recv_window}{payload}"
        return {
            "X-BAPI-API-KEY": self.creds.api_key,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": str(self.recv_window),
            "X-BAPI-SIGN": sign(self.creds.api_secret, prehash),
            "Content-Type": "application/json",
        }

    def _timestamp_ms(self) -> str:
        return str(int(time.time() * 1000))

    def request(self, method: str, path: str, *, params: dict | None = None, body: dict | None = None) -> dict[str, Any]:
        url = f"{self.creds.base_url}{path}"
        params = params or {}
        timestamp = self._timestamp_ms()
        if method == "GET":
            payload = urlencode(params)
            headers = self._headers(timestamp, payload)
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, params=params, headers=headers)
        else:
            payload = json.dumps(body or {}, separators=(",", ":"))
            headers = self._headers(timestamp, payload)
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, content=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        if data.get("retCode") != 0:
            raise RuntimeError(f"Bybit {path}: {data.get('retMsg')} ({data.get('retCode')})")
        return data

    def instruments(self, symbol: str, category: str = "linear") -> dict[str, Any]:
        data = self.request(
            "GET",
            "/v5/market/instruments-info",
            params={"category": category, "symbol": symbol},
        )
        lst = data["result"]["list"]
        if not lst:
            raise RuntimeError(f"no instrument {symbol}")
        return lst[0]

    def set_leverage(self, symbol: str, leverage: float, category: str = "linear") -> None:
        lev = str(int(leverage) if leverage == int(leverage) else leverage)
        try:
            self.request(
                "POST",
                "/v5/position/set-leverage",
                body={
                    "category": category,
                    "symbol": symbol,
                    "buyLeverage": lev,
                    "sellLeverage": lev,
                },
            )
        except RuntimeError as exc:
            if "leverage not modified" in str(exc).lower() or "110043" in str(exc):
                return
            raise

    def position(self, symbol: str, category: str = "linear") -> dict[str, Any] | None:
        data = self.request(
            "GET",
            "/v5/position/list",
            params={"category": category, "symbol": symbol},
        )
        for row in data["result"]["list"]:
            size = float(row.get("size") or 0)
            if size > 0:
                return row
        return None

    def market_order(
        self,
        *,
        symbol: str,
        side: str,
        qty: str,
        reduce_only: bool = False,
        category: str = "linear",
    ) -> dict[str, Any]:
        body = {
            "category": category,
            "symbol": symbol,
            "side": "Buy" if side == "long" else "Sell",
            "orderType": "Market",
            "qty": qty,
            "timeInForce": "IOC",
            "reduceOnly": reduce_only,
        }
        return self.request("POST", "/v5/order/create", body=body)

    def set_trading_stop(
        self,
        *,
        symbol: str,
        stop: float,
        take_profit: float | None,
        category: str = "linear",
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "category": category,
            "symbol": symbol,
            "tpslMode": "Full",
            "stopLoss": f"{stop:.2f}",
            "slTriggerBy": "MarkPrice",
        }
        if take_profit is not None:
            body["takeProfit"] = f"{take_profit:.2f}"
            body["tpTriggerBy"] = "MarkPrice"
        return self.request("POST", "/v5/position/trading-stop", body=body)

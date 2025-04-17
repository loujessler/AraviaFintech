import json
import settings
from logging import Logger

from apps.adapters.ws_base import BaseWSClient


class BinanceWSClient(BaseWSClient):
    name = "BinanceWS"

    def __init__(self, symbol: str, logger: Logger):
        url = f"{settings.BINANCE_WS_URL}/{symbol.lower()}@trade"
        super().__init__(url, logger)
        self.symbol = symbol

    async def on_connect(self):
        self.logger.info(f"[{self.name}] Connected to {self.url}")

    async def on_message(self, message: str):
        data = json.loads(message)
        return data.get("p")

    async def on_disconnect(self):
        self.logger.info(f"[{self.name}] Disconnected from {self.url}")

    async def on_error(self, error: Exception):
        self.logger.info(f"[{self.name}] Error: {error}")
        return str(error)

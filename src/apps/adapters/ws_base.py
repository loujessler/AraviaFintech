import asyncio
import websockets
import ssl
from logging import Logger
from abc import ABC, abstractmethod


class BaseWSClient(ABC):
    name: str = NotImplemented

    def __init__(self, url: str, logger: Logger):
        self.logger = logger
        self.url = url
        self._ws = None
        self._connected = asyncio.Event()
        self._running = False

    async def connect(self, queue: asyncio.Queue):
        self.logger.info(f"[{self.name}] Start connection.")
        try:
            async with websockets.connect(self.url) as self._ws:
                self._connected.set()
                await self.on_connect()
                async for message in self._ws:
                    price = await self.on_message(message)
                    if price:
                        await queue.put(price)
        except Exception as e:
            await self.on_error(e)
        finally:
            if self._ws and not self._ws.close:
                await self._ws.close()
                await self.on_disconnect()
                self.logger.info("WebSocket client closed")

    async def listen(self):
        try:
            async for message in self._ws:
                await self.on_message(message)
        except Exception as e:
            await self.on_error(e)

    async def send(self, message: str):
        await self._connected.wait()
        await self._ws.send(message)

    async def close(self):
        if self._ws:
            await self._ws.close()
            self.logger.info(f"[{self.name}] Closed by user.")
        await self.on_disconnect()

    @abstractmethod
    async def on_connect(self) -> 'BaseWSClient':
        ...

    @abstractmethod
    async def on_message(self, message: str) -> str:
        ...

    @abstractmethod
    async def on_disconnect(self) -> 'BaseWSClient':
        ...

    @abstractmethod
    async def on_error(self, error: Exception) -> str:
        ...

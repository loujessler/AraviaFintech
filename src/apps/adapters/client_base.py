from logging import Logger

import aiohttp
import hashlib
import hmac
import urllib.parse
from abc import ABC, abstractmethod
from decimal import Decimal

from base.enum import BaseEnum


class SideType(BaseEnum):
    SELL = 'sell'
    BUY = 'buy'


class OrderType(BaseEnum):
    MARKET = 'market'
    LIMIT = 'limit'


class APIClient(ABC):
    """Общий класс для описания API клиентов внешних бирж"""
    exchange: str

    def __init__(self, logger: Logger):
        self.logger = logger
        self.session = aiohttp.ClientSession()

    @classmethod
    def _generate_signature(cls, secret: str, params: dict) -> str:
        """Генерация подписи для запросов"""
        query = urllib.parse.urlencode(params, doseq=True)
        return hmac.new(
            key=secret.encode(),
            msg=query.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

    @classmethod
    def get_headers(cls, key: str) -> dict:
        """Генерация заголовка для запросов"""
        return {
            'X-MBX-APIKEY': key
        }

    async def close(self):
        """Корректное закрытие HTTP-сессии"""
        if not self.session.closed:
            await self.session.close()
            self.logger.info("API client closed")

    @abstractmethod
    async def new_order(self,
                        symbol: str,
                        order_type: OrderType,
                        side: SideType,
                        quantity: Decimal,
                        price: Decimal = Decimal('0'),
                        ) -> dict:
        """Размещает ордер с параметрами:

        symbol - Тикер пары;
        order_type - Тип ордера: лимитный, рыночный;
        side -Тип операции: buy, sell;
        quantity - Количество в базовой валюте
        order_id - Клиентский номер заказа
        price - Цена исполнения ордера, указывается для лимитных заявок
        """
        pass

    @abstractmethod
    async def get_balances(self) -> dict: ...

    @abstractmethod
    async def get_order(self, order_id: str, symbol: str) -> dict: ...

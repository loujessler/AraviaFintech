import aiohttp
import time

from decimal import Decimal

import settings
from ...adapters.client_base import APIClient


class BinanceAPIClient(APIClient):
    """ Класс для взаимодействия с API биржи Binance"""

    exchange = 'Binance'
    url = settings.BINANCE_API_URL
    api_key = settings.BINANCE_API_KEY
    api_secret = settings.BINANCE_API_SECRET

    def __str__(self):
        return f'BinanceAPIClient({self})'

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.session.close()

    @staticmethod
    def _path(method: str, api: str = 'api', version: str = 'v3') -> str:
        """ Добавляет к строке запроса требуемую команду"""
        return f'/{api}/{version}/{method}'

    @classmethod
    def get_signature_params(cls, params: dict = None) -> dict:
        params = params or {}
        params.update({
            'timestamp': int(time.time() * 1000)
        })
        params['signature'] = cls._generate_signature(cls.api_secret, params)
        return params

    async def _request(self, method: str, endpoint: str, params: dict = None, signed: bool = True) -> dict:
        params = self.get_signature_params(params) if signed else params
        async with self.session.request(
                method=method,
                url=f"{self.url}{endpoint}",
                params=params,
                headers=self.get_headers(self.api_key)
        ) as response:
            try:
                response.raise_for_status()
                self.logger.info(f"Отправлен {method} запрос '{endpoint}'")
            except aiohttp.ClientResponseError as e:
                self.logger.error(f"Request failed: {e.status} {e.message}\n"
                                  f"Request URL: {e.request_info.url}\n"
                                  f"Params: {params}")
                raise
            return await response.json()

    async def new_order(self,
                        symbol: str,
                        order_type: str,
                        side: str,
                        quantity: Decimal,
                        price: Decimal = Decimal('0')) -> dict:
        params = {
            'symbol': symbol,
            'side': side.upper(),
            'type': order_type.upper(),
            'quantity': str(quantity)
        }

        if price:
            params['price'] = str(price)

        return await self._request('POST', self._path('order'), params)

    async def get_ping_response(self):
        return await self._request(
            method='GET',
            endpoint=self._path('ping'),
            signed=False
        )

    async def get_balances(self) -> dict[str, float]:
        result = await self._request('GET', self._path('account'))
        return {b['asset']: b['free'] for b in result['balances'] if float(b['free']) > 0}

    async def get_order(self, order_id: str, symbol: str) -> dict:
        return await self._request('GET', self._path('order'), {
            'symbol': symbol,
            'orderId': order_id
        })

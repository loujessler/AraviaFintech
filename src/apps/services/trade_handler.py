import asyncio
import time
from decimal import Decimal
from logging import Logger

from apps.adapters.client_base import OrderType, SideType


class TradeManager:
    def __init__(
            self,
            api_client,
            ws_client,
            symbol: str,
            quantity: Decimal,
            stop_loss: float,
            take_profit: float,
            timeout: int,
            cooldown: int,
            logger: Logger
    ):
        self.api_client = api_client
        self.ws_client = ws_client
        self.symbol = symbol
        self.quantity = quantity
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.timeout = timeout
        self.cooldown = cooldown
        self.logger = logger

        self.position_open = False
        self.cooldown_open = False
        self.entry_price: Decimal | None = None
        self.current_price: Decimal | None = None
        self.timer_task: asyncio.Task | None = None
        self.price_queue = asyncio.Queue()
        self.balance_crypto = Decimal('0')
        self.balance_usdt = Decimal('0')

    async def start_trading(self):
        """Запуск торгового процесса"""
        self.logger.info(f"{'#' * 10} Запуск бота! {'#' * 10}")
        await self._update_balances()
        try:
            tasks = [
                asyncio.create_task(self.ws_client.connect(self.price_queue)),
                asyncio.create_task(self._price_listener()),
                asyncio.create_task(self._trading_loop())
            ]
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Критическая ошибка: {str(e)}")
        finally:
            await self._shutdown()

    async def _shutdown(self):
        """Корректное завершение работы"""
        self.logger.info("Завершение работы...")
        if self.timer_task:
            self.timer_task.cancel()
        await self.ws_client.close()

    async def _trading_loop(self):
        """Основной торговый цикл"""
        while True:
            try:
                if self.current_price is None:
                    self.logger.warning("Цена не получена, ожидание...")
                    await asyncio.sleep(5)
                    continue

                if not self.position_open and not self.cooldown_open:
                    if await self._buy():
                        self._start_sell_timer()

                await asyncio.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Ошибка цикла: {str(e)}")

    async def _price_listener(self):
        """Обработчик обновлений цены"""
        while True:
            try:
                price = await asyncio.wait_for(
                    self.price_queue.get(),
                    timeout=30
                )
                self.current_price = Decimal(str(price))
                if self.position_open or self.current_price:
                    await self._check_conditions()
            except asyncio.TimeoutError:
                self.logger.warning("Нет новых данных цены 30 секунд")
            except Exception as e:
                self.logger.error(f"Ошибка получения цены: {str(e)}")

    def _start_sell_timer(self):
        """Запуск таймера"""
        if self.timer_task and not self.timer_task.done():
            self.logger.debug("Таймер уже активен")
            return

        self.timer_task = asyncio.create_task(self._sell_timer())

    async def _sell_timer(self):
        """Таймер продажи"""
        try:
            await asyncio.sleep(self.timeout)

            if self.position_open:
                await self._sell("Timeout")

        except Exception as e:
            self.logger.error(f"Ошибка таймера: {str(e)}")

    async def _start_cooldown(self):
        """Точный кулдаун между сделками"""
        self.cooldown_open = True
        await asyncio.sleep(self.cooldown)
        self.cooldown_open = False

    async def _buy(self) -> bool:
        """Выполнение покупки"""
        try:
            if self.balance_usdt < self.quantity * self.current_price:
                self.logger.warning("Недостаточно средств для покупки")
                return False

            order = await self.api_client.new_order(
                symbol=self.symbol,
                order_type=OrderType.MARKET.value,
                side=SideType.BUY.value,
                quantity=self.quantity
            )

            if order:
                total_quantity = Decimal(order['executedQty'])
                total_quote = Decimal(order['cummulativeQuoteQty'])
                self.entry_price = (total_quote / total_quantity).normalize()
                self.logger.info(
                    f"Покупка {self.quantity} {self.symbol} "
                    f"по цене {self.entry_price:.4f} "
                    f"Баланс: {self.balance_usdt:.4f} USDT"
                )
                return True

        except Exception as e:
            self.logger.error(f"Ошибка покупки: {str(e)}")
        finally:
            self.position_open = True
            await self._update_balances()

    async def _sell(self, reason: str):
        """Выполнение продажи"""
        try:
            if not self.position_open:
                return

            await self._execute_sell(reason=reason)

        except Exception as e:
            self.logger.error(f"Ошибка продажи: {str(e)}")
        finally:
            await self._post_sell_cleanup()

    async def _execute_sell(self, reason: str):
        """Выполнение продажи"""
        if self.balance_crypto <= Decimal('0'):
            self.logger.warning("Нет криптовалюты для продажи")
            return

        quantity = self.balance_crypto
        order = await self.api_client.new_order(
            symbol=self.symbol,
            order_type=OrderType.MARKET.value,
            side=SideType.SELL.value,
            quantity=quantity
        )

        if order:
            total_quantity = Decimal(order['executedQty'])
            total_quote = Decimal(order['cummulativeQuoteQty'])
            sell_price = total_quote / total_quantity
            profit = (sell_price - self.entry_price) * quantity
            self.logger.info(
                f"Продажа {quantity:.4f} {self.symbol} "
                f"по цене {sell_price:.4f} ({reason}) "
                f"Прибыль: {profit:.4f} USDT "
                f"Баланс: {self.balance_usdt:.4f} USDT"
            )

    async def _post_sell_cleanup(self):
        """Гарантированный сброс состояния"""
        await self._start_cooldown()

        if self.timer_task:
            self.timer_task.cancel()
        self.timer_task = None

        self.position_open = False
        self.entry_price = None
        await self._update_balances()

    async def _check_conditions(self):
        """Проверка торговых условий"""
        try:
            if not self.entry_price or self.entry_price == Decimal('0'):
                return

            price_change = ((self.current_price - self.entry_price) /
                            self.entry_price * 100)

            if price_change <= -self.stop_loss:
                await self._sell('Stop Loss')
            elif price_change >= self.take_profit:
                await self._sell('Take Profit')
        except ZeroDivisionError:
            self.logger.error("Ошибка: Нулевая цена входа")
            await self._sell('Error')

    async def _update_balances(self):
        """Обновление балансов"""
        try:
            balances = await self.api_client.get_balances()
            self.balance_usdt = Decimal(balances.get('USDT', '0'))
            crypto_asset = self.symbol.replace('USDT', '')
            self.balance_crypto = Decimal(balances.get(crypto_asset, '0'))
            self.logger.info(
                f"Баланс: {self.balance_usdt:.4f} USDT "
                f"Баланс: {self.balance_crypto:.4f} {crypto_asset}"
            )
        except Exception as e:
            self.logger.error(f"Ошибка получения баланса: {str(e)}")

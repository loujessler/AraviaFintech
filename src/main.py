import argparse
import asyncio
import logging
from decimal import Decimal

from apps.adapters import BinanceWSClient, BinanceAPIClient
from apps.services.custom_logger import CustomLogger
from apps.services.trade_handler import TradeManager


def parse_args():
    parser = argparse.ArgumentParser(description='Aravia Fintech Bot')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('--quantity', type=str, default='0.0001', help='Quantity to trade')
    parser.add_argument('--profit', type=float, default=0.25, help='Profit threshold in percentage')
    parser.add_argument('--loss', type=float, default=0.25, help='Loss threshold in percentage')
    parser.add_argument('--wait', type=int, default=60, help='Max wait time in seconds')
    parser.add_argument('--cooldown', type=int, default=30, help='Cooldown time in seconds')
    return parser.parse_args()


async def main():
    args = parse_args()

    logger = CustomLogger(name="TradingBot")
    api_client_logger = CustomLogger(name="BinanceAPIClient", log_file="api_logger.log")
    ws_client_logger = CustomLogger(name="BinanceWSClient", log_file="ws_logger.log")

    api_client = BinanceAPIClient(api_client_logger)
    ws_client = BinanceWSClient(symbol="BTCUSDT", logger=ws_client_logger)

    trade_manager = TradeManager(
        api_client=api_client,
        ws_client=ws_client,
        symbol=args.symbol,
        quantity=Decimal(args.quantity),
        stop_loss=args.loss,
        take_profit=args.profit,
        timeout=args.wait,
        cooldown=args.cooldown,
        logger=logger
    )

    try:
        await trade_manager.start_trading()
    except KeyboardInterrupt:
        logger.info("Торговля остановлена пользователем")
    finally:
        await api_client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program interrupted by user. Shutting down...")

# import argparse
# import asyncio
# from logging import Logger
#
# import settings
#
# from apps.adapters import BinanceWSClient, BinanceAPIClient
#
#
# # def parse_args():
# #     parser = argparse.ArgumentParser(description='Aravia Fintech Bot')
# #     parser.add_argument('--symbol', type=str, required=True, help='Trading symbol (e.g., BTCUSDT)')
# #     parser.add_argument('--quantity', type=float, required=True, help='Quantity to trade')
# #     parser.add_argument('--profit', type=float, default=0.25, help='Profit threshold in percentage')
# #     parser.add_argument('--loss', type=float, default=0.25, help='Loss threshold in percentage')
# #     parser.add_argument('--wait', type=int, default=60, help='Max wait time in seconds')
# #     parser.add_argument('--cooldown', type=int, default=30, help='Cooldown time in seconds')
# #     return parser.parse_args()
#
#
# async def price_handler(queue, symbol):
#     ws_client = BinanceWSClient(symbol)
#     await ws_client.connect(queue)
#
#
# # async def main():
# #     args = parse_args()
# #
# #     api_key = settings.BINANCE_API_KEY
# #     api_secret = settings.BINANCE_API_SECRET
# #
# #     if not api_key or not api_secret:
# #         raise ValueError("API keys not found in environment variables")
# #
# #     logger = Logger()
# #     price_queue = asyncio.Queue()
# #
# #     trade_manager = TradeManager(
# #         api_key=api_key,
# #         api_secret=api_secret,
# #         symbol=args.symbol,
# #         quantity=args.quantity,
# #         stop_loss=args.stop_loss,
# #         take_profit=args.take_profit,
# #         timeout=args.timeout,
# #         cooldown=args.cooldown,
# #         logger=logger
# #     )
# #
# #     await trade_manager.connect_api()
# #
# #     tasks = [
# #         asyncio.create_task(price_handler(price_queue, args.symbol)),
# #         asyncio.create_task(trade_manager.run(price_queue))
# #     ]
# #
# #     await asyncio.gather(*tasks)
# #
# #
# # if __name__ == '__main__':
# #     try:
# #         asyncio.run(main())
# #     except KeyboardInterrupt:
# #         pass
# #         # logger.info("Shutting down trading bot...")
# #     except Exception as e:
# #         pass
# #         # logger.error(f"Fatal error: {e}")
#
#
# async def check_balance():
#     async with BinanceAPIClient() as client:
#         # Проверка баланса
#         balance = await client.get_balances()
#         print(f"USDT balance: {balance.get('USDT', 0)}")
#
#
# async def main():
#     price_queue = asyncio.Queue()
#
#     tasks = [
#         asyncio.create_task(price_handler(price_queue, 'BTCUSDT@trade')),
#         asyncio.create_task(check_balance())
#     ]
#
#     await asyncio.gather(*tasks)
#     # async with BinanceAPIClient() as client:
#     #     # Проверка баланса
#     #     balance = await client.get_balances()
#     #     print(f"USDT balance: {balance.get('USDT', 0)}")
#
#
# async def main2():
#     price_queue = asyncio.Queue()
#     client = BinanceWSClient("btcusdt")
#     await client.connect(price_queue)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())

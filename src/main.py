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
    ws_client = BinanceWSClient(symbol=args.symbol, logger=ws_client_logger)

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
    finally:
        await api_client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program interrupted by user. Shutting down...")

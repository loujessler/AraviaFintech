import os
import logging


class CustomLogger(logging.Logger):
    """Кастомный логгер с записью в файл"""

    def __init__(self, name: str, log_file: str = 'loggers.log', log_dir: str = 'logs'):
        super().__init__(name)
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, log_file)
        self.setup_logger()

    def setup_logger(self):
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(formatter)
        self.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.addHandler(console_handler)

    def log_trade(self, event_type: str, details: dict):
        message = f"{event_type}: "
        message += " | ".join(f"{k}: {v}" for k, v in details.items())
        self.info(message)

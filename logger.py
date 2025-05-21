import logging
import sys
import requests
import os
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class TelegramLogHandler(logging.Handler):
    def __init__(self, token: str, chat_id: str, min_level: int = logging.ERROR):
        super().__init__(level=min_level)
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def emit(self, record):
        try:
            log_entry = self.format(record)
            payload = {
                "chat_id": self.chat_id,
                "text": f"🛠️ *{record.levelname}* из `{record.name}`:\n```\n{log_entry}\n```",
                "parse_mode": "Markdown"
            }
            requests.post(self.api_url, data=payload)
        except Exception:
            self.handleError(record)

def setup_logger(name: str = None, level: LogLevel = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger  # Уже настроен

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s")
    logger.setLevel(level)
    logger.propagate = False

    log_outputs = os.getenv("LOG_OUTPUTS", "console").lower().split(",")

    if "console" in log_outputs:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        handler.setLevel(level)
        logger.addHandler(handler)

    if "file" in log_outputs:
        log_dir = os.getenv("LOG_DIR", "./logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(f"{log_dir}/{name or 'app'}.log", mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    if "telegram" in log_outputs:
        tg_token = os.getenv("TELEGRAM_LOG_TOKEN")
        tg_chat_id = os.getenv("TELEGRAM_LOG_CHAT_ID")
        if tg_token and tg_chat_id:
            tg_handler = TelegramLogHandler(token=tg_token, chat_id=tg_chat_id)
            tg_handler.setFormatter(formatter)
            tg_handler.setLevel(level)
            logger.addHandler(tg_handler)

    return logger

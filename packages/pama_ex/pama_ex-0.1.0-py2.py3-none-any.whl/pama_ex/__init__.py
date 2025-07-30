"""Пакет pama_ex для работы с API."""
from pama_ex.client import models, q, get_last_response  # Абсолютный путь
__version__ = "0.1.0"  # Версия (т.к. dynamic = ["version"])
__all__ = ["models", "q", "get_last_response"]
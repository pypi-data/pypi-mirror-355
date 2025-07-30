"""
Простой клиент OpenRouter без контекста: любой запрос любой длины
к выбранной модели-алиасу. История не сохраняется.
"""

import requests
from typing import Union, Dict, List, Optional

# 1) API-ключ (жёстко вписан)
API_KEY = "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"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# 2) Алиасы и модель по умолчанию
_ALIAS = {
    "gpt":     "openai/gpt-4o-mini",
    "gemini":  "google/gemini-2.5-flash-preview-05-20",
    "deepseek":"deepseek/deepseek-chat-v3-0324",
    "llama":    "meta-llama/llama-4-maverick",
    "qwen":    "qwen/qwen3-235b-a22b",
    "claude":  "anthropic/claude-3.7-sonnet",
}
_DEFAULT = "gemini"

# Храним лишь последний ответ, если понадобится
_last_response: Union[Dict, None] = None


def models() -> List[str]:
    """
    Возвращает список доступных алиасов моделей:
      ['gpt', 'gemini', 'deepseek', 'grok', 'qwen', 'claude']
    """
    return list(_ALIAS.keys())


def q(
    prompt: str,
    *,
    model: Optional[str] = None,
    max_tokens: int = 2048,
) -> str:
    """
    Отправляет текстовый prompt в выбранную модель-алиас и возвращает ответ как строку.

    Аргументы:
      prompt     — ваш текстовый запрос (любой длины).
      model      — алиас модели ('gpt', 'gemini', 'deepseek', 'grok', 'qwen', 'claude').
                   Если не указан, используется алиас _DEFAULT ("gemini").
      max_tokens — максимальное число токенов для ответа (можете увеличить при необходимости).

    Возвращает:
      строку (ответ модели). Полный JSON-ответ сохраняется внутрь _last_response.
    """
    global _last_response

    alias = (model or _DEFAULT).lower()
    if alias not in _ALIAS:
        raise ValueError(
            f"Неизвестный алиас модели {alias!r}. Доступно: {', '.join(_ALIAS)}"
        )
    remote_model = _ALIAS[alias]

    payload = {
        "model": remote_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=HEADERS,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    _last_response = resp.json()

    # По спецификации OpenRouter: первый choice → message.content
    return _last_response["choices"][0]["message"]["content"]


def get_last_response() -> Optional[Dict]:
    """
    Возвращает полный JSON-ответ последнего вызова q(...) или None, если запросов ещё не было.
    Полезно для просмотра статистики токенов и прочего.
    """
    return _last_response
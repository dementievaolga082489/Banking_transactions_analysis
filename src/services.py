import json
import logging
import re
from typing import Any, Dict, List

import pandas as pd

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_transactions_from_excel(file_path: str) -> List[Dict[str, Any]]:
    """
    Загрузка транзакций из Excel-файла.

    Args:
        file_path: Путь к Excel-файлу

    Returns:
        Список словарей с транзакциями
    """
    try:
        logger.info(f"Загрузка данных из файла: {file_path}")

        # Чтение Excel файла
        df = pd.read_excel(file_path)

        # Преобразование в список словарей
        transactions = df.to_dict("records")

        logger.info(f"Загружено {len(transactions)} транзакций")
        return transactions

    except Exception as e:
        logger.error(f"Ошибка при загрузке Excel файла: {e}")
        raise


def search_by_phone_numbers(transactions: List[Dict[str, Any]]) -> str:
    """
    Поиск транзакций, содержащих в описании мобильные номера.

    Args:
        transactions: Список словарей с транзакциями

    Returns:
        JSON-строка с транзакциями, содержащими номера телефонов
    """

    # Регулярное выражение для поиска российских мобильных номеров
    # Поддерживает форматы:
    # +7 XXX XXX-XX-XX, +7 XXX XXX XX XX, +7XXXXXXXXXX
    # 8 XXX XXX-XX-XX, 8 XXX XXX XX XX, 8XXXXXXXXXX
    phone_pattern = re.compile(r"(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}")

    filtered_transactions = []

    for i, transaction in enumerate(transactions):
        # Получаем описание транзакции
        description = transaction.get("Описание", "")

        # Если описание отсутствует или это не строка, пропускаем
        if not isinstance(description, str):
            description = str(description) if description is not None else ""

        # Поиск номера телефона в описании
        if phone_pattern.search(description):
            filtered_transactions.append(transaction)

    logger.info(f"Найдено {len(filtered_transactions)} транзакций с телефонными номерами")

    # Возвращаем JSON с результатами
    return json.dumps(filtered_transactions, ensure_ascii=False, indent=2, default=str)

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from src.utils import (calculate_card_operations, get_currency_rates, get_greeting, get_stock_prices,
                       get_top_transactions, load_user_settings)

SRC_DIR = Path(__file__).resolve().parent

DATA_DIR = SRC_DIR.parent / "data"

JSON_FILE = SRC_DIR.parent / "user_settings.json"
EXL_FILE = DATA_DIR / "operations.xlsx"
# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main_page(date_time_str: str) -> Dict[str, Any]:
    """
    Главная функция для страницы "Главная".

    Args:
        date_time_str: Строка с датой и временем в формате 'YYYY-MM-DD HH:MM:SS'

    Returns:
        JSON-ответ с данными для главной страницы
    """
    try:
        # Парсим входную дату для фильтрации транзакций
        filter_datetime = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
        logger.info(f"Обработка запроса на получение даты и времени для фильтрации: {filter_datetime}")

        # Получаем приветствие на основе текущего системного времени
        current_datetime = datetime.now()
        greeting = get_greeting(current_datetime)
        logger.info(f"Приветствие на основе текущего времени {current_datetime}: {greeting}")

        # Загружаем настройки пользователя
        user_settings = load_user_settings()
        logger.info(f"Пользовательские настройки загружены: {user_settings}")

        # Получаем приветствие
       # greeting = get_greeting(current_datetime)

        # Загружаем данные транзакций
        df = pd.read_excel(EXL_FILE)
        logger.info(f"Загружены данные о транзакциях: {df.shape}")

        # Преобразуем дату операции в datetime
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)

        # Определяем диапазон для анализа (с начала месяца по входную дату)
        start_date = filter_datetime.replace(day=1, hour=0, minute=0, second=0)
        end_date = filter_datetime

        # Фильтруем транзакции по дате и статусу
        mask = (df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date) & (df["Статус"] == "OK")
        filtered_df = df[mask].copy()
        logger.info(f"Количество отфильтрованных транзакций: {len(filtered_df)}")

        # Рассчитываем данные по картам
        cards_data = calculate_card_operations(filtered_df)

        # Получаем топ-5 транзакций
        top_transactions = get_top_transactions(filtered_df)

        # Получаем курсы валют
        currency_rates = get_currency_rates(user_settings.get("user_currencies", []))

        # Получаем цены акций
        stock_prices = get_stock_prices(user_settings.get("user_stocks", []))

        # Формируем JSON-ответ
        response = {
            "greeting": greeting,
            "cards": cards_data,
            "top_transactions": top_transactions,
            "currency_rates": currency_rates,
            "stock_prices": stock_prices,
        }

        logger.info("Получен ответ")
        return response

    except Exception as e:
        logger.error(f"Ошибка в функции: {str(e)}")
        raise

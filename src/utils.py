import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv

# Загружаем переменную окружения
load_dotenv()

API_KEY = os.getenv("API_KEY")


logger = logging.getLogger(__name__)

SRC_DIR = Path(__file__).resolve().parent

DATA_DIR = SRC_DIR.parent / "data"

JSON_FILE = SRC_DIR.parent / "user_settings.json"
EXL_FILE = DATA_DIR / "operations.xlsx"


def load_user_settings() -> Dict[str, List[str]]:
    """
    Загружает пользовательские настройки из файла user_settings.json.

    Returns:
        Словарь с настройками пользователя
    """
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
        logger.info("Настройки успешно загружены")
        return settings
    except FileNotFoundError:
        logger.warning("Файл user_settings.json не найден")
        return {}


# print(load_user_settings())


def get_greeting(current_datetime: datetime) -> str:
    """
    Возвращает приветствие в зависимости от времени суток.

    Args:
        current_datetime: Текущее время

    Returns:
        Строка с приветствием
    """
    hour = current_datetime.hour
    if 6 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


# date_string = "2024-08-23 12:25:03"
# date_object = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
# print(get_greeting(date_object))


def calculate_card_operations(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Рассчитывает операции по картам: общая сумма расходов и кешбэк.

    Args:
        df: DataFrame с отфильтрованными транзакциями

    Returns:
        Список словарей с данными по картам
    """
    if df.empty:
        return []

    # Группируем по номеру карты
    cards_operations = []

    for card_number, group in df.groupby("Номер карты"):
        # Преобразуем номер карты в строку
        card_str = str(card_number).strip()

        # Убираем все нецифровые символы (звездочки, пробелы и т.д.)
        digits_only = "".join(filter(lambda x: x.isdigit(), card_str))

        if digits_only:
            # Если есть цифры, берем последние 4
            last_digits = digits_only[-4:]
        else:
            # Если цифр нет, используем исходную строку
            last_digits = card_str[-4:] if len(card_str) >= 4 else card_str

        # Суммируем расходы (отрицательные суммы - это расходы)
        total_spent = group["Сумма платежа"].apply(lambda x: abs(x) if x < 0 else 0).sum()

        # Кешбэк: 1 рубль на каждые 100 рублей расходов
        cashback = total_spent / 100

        cards_operations.append(
            {
                "last_digits": last_digits,
                "total_spent": float(round(total_spent, 2)),
                "cashback": float(round(cashback, 2)),
            }
        )

    return cards_operations


# df = (pd.read_excel(EXL_FILE)).head(10)

# print(calculate_card_operations(df))


def get_top_transactions(df: pd.DataFrame, top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Возвращает топ-N транзакций по сумме платежа.

    Args:
        df: DataFrame с отфильтрованными транзакциями
        top_n: Количество транзакций для возврата

    Returns:
        Список словарей с данными топ-транзакций
    """
    if df.empty:
        return []

    # Сортируем по абсолютной сумме платежа и берем топ-N
    top_transactions = df.nlargest(top_n, "Сумма платежа")

    result = []
    for _, row in top_transactions.iterrows():
        transaction = {
            "date": row["Дата операции"].strftime("%d.%m.%Y"),
            "amount": round(row["Сумма платежа"], 2),
            "category": row["Категория"] if pd.notnull(row["Категория"]) else "Не указана",
            "description": row["Описание"] if pd.notnull(row["Описание"]) else "Нет описания",
        }
        result.append(transaction)

    return result


# df = pd.read_excel(EXL_FILE)
# df['Дата операции'] = pd.to_datetime(df['Дата операции'], format='%d.%m.%Y %H:%M:%S')
# top_5 = get_top_transactions(df)
# for i in top_5:
#   print(i)


def get_currency_rates(currencies: List[str]) -> List[Dict[str, Any]]:
    """
    Получает текущие курсы валют через API.
    Использует API Центрального банка РФ.

    Args:
        currencies: Список кодов валют

    Returns:
        Список словарей с курсами валют
    """
    rates = []

    for currency in currencies:
        try:
            # Используем API Центрального банка РФ
            url = "https://www.cbr-xml-daily.ru/daily_json.js"
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()

            if currency in data["Valute"]:
                rate = data["Valute"][currency]["Value"]
                rates.append({"currency": currency, "rate": round(rate, 2)})
            else:
                logger.warning(f"Валюта {currency} не найдена в API ответе")
                rates.append({})

        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе курсов валют: {str(e)}")
            rates.append({})

    return rates


# user_settings = load_user_settings()  # Возвращает словарь
# currency_rates = get_currency_rates(user_settings.get('user_currencies', []))
# print(currency_rates)


def get_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    """
    Получает текущие цены акций через API.
    Использует Alpha Vantage API (требуется API ключ).

    Args:
        stocks: Список тикеров акций

    Returns:
        Список словарей с ценами акций
    """
    stock_prices = []

    for stock in stocks:
        try:
            # Используем Alpha Vantage API
            url = "https://www.alphavantage.co/query"
            params = {"function": "GLOBAL_QUOTE", "symbol": stock, "apikey": API_KEY}

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if "Global Quote" in data and data["Global Quote"]:
                price = float(data["Global Quote"]["05. price"])
                stock_prices.append({"stock": stock, "price": round(price, 2)})
            else:
                logger.warning(f"Акция {stock} не найдена в API ответе")
                stock_prices.append({"stock": stock, "price": "Акция не найдена"})

        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе акций: {str(e)}")
            stock_prices.append({})

    return stock_prices


# user_settings = load_user_settings()  # Возвращает словарь
# currency_stock = get_stock_prices(user_settings.get("user_stocks", []))
# print(currency_stock)

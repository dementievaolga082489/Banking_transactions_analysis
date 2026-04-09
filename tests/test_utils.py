import json
import pandas as pd
import requests
import pytest
from datetime import datetime
from src.utils import load_user_settings, get_greeting, calculate_card_operations, get_top_transactions, get_currency_rates, get_stock_prices
from unittest.mock import mock_open, patch, Mock


def test_load_user_settings_success(sample_settings) -> None:  # Фикстура как аргумент
    """Тест на успешное открытие json файла"""
    with patch("builtins.open", mock_open(read_data=json.dumps(sample_settings))):
        result = load_user_settings()
        assert result == sample_settings


def test_load_user_settings_file_not_found_alternative() -> None:
    """Тест: файл не найден (должен вернуть пустой словарь)"""
    with patch("builtins.open", side_effect=FileNotFoundError):
        result = load_user_settings()
        assert result == {}


@pytest.mark.parametrize("hour, expected", [
    (0, "Доброй ночи"),
    (1, "Доброй ночи"),
    (5, "Доброй ночи"),
    (6, "Доброе утро"),
    (7, "Доброе утро"),
    (11, "Доброе утро"),
    (12, "Добрый день"),
    (13, "Добрый день"),
    (17, "Добрый день"),
    (18, "Добрый вечер"),
    (19, "Добрый вечер"),
    (22, "Добрый вечер"),
    (23, "Доброй ночи"),
])
def test_get_greeting_parametrized(hour, expected):
    """Параметризованный тест - определение времени суток"""
    assert get_greeting(datetime(2024, 1, 1, hour, 30, 0)) == expected

def test_empty_dataframe():
    """Тест: пустой DataFrame"""
    df_empty = pd.DataFrame()
    result = calculate_card_operations(df_empty)
    assert result == []

def test_mixed_expenses_and_income():
    """Тест: смешанные операции (расходы и доходы)"""
    df = pd.DataFrame({
        "Номер карты": ["****9999", "****9999", "****9999", "****9999"],
        "Сумма платежа": [-1000, 500, -200, 1000]  # Расходы: 1200, доходы: 1500
    })

    result = calculate_card_operations(df)

    expected = [{
            "last_digits": "9999",
            "total_spent": 1200.0,  # Только расходы
            "cashback": 12.0
        }]
    assert result == expected



@pytest.mark.parametrize("card_number, expected_digits", [
    ("****1234", "1234"),
    ("1234567890123456", "3456"),
    ("1234", "1234"),
    ("12", "12"),
    ("**** **** 5678", "5678"),
    ("   ***9012   ", "9012"),
    ("", ""),  # Пустая строка
])
def test_card_number_extraction(card_number, expected_digits):
    """Параметризованный тест: извлечение последних цифр номера карты"""
    df = pd.DataFrame({
        "Номер карты": [card_number],
        "Сумма платежа": [-100]
    })

    result = calculate_card_operations(df)

    assert result[0]["last_digits"] == expected_digits


def test_get_top_transactions_empty_dataframe():
    """Тест с пустым DataFrame"""
    df = pd.DataFrame(columns=["Дата операции", "Сумма платежа", "Категория", "Описание"])

    result = get_top_transactions(df)

    assert result == []


def test_get_top_transactions_normal_case(transactions):
    """Тест нормального случая с несколькими транзакциями"""

    df = pd.DataFrame(transactions)

    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    result = get_top_transactions(df, top_n=3)

    assert result[0]["amount"] == 1000.00
    assert result[1]["amount"] == 500.75
    assert result[2]["amount"] == 250.00
    assert result[0]["category"] == "ЖКХ"
    assert result[0]["date"] == "04.01.2024"




def test_get_currency_rates_success(mock_success_response):
    """Тест успешного получения курсов нескольких валют"""
    currencies = ["USD", "EUR", "CNY"]
    # Настраиваем мок
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_success_response
    mock_response.raise_for_status.return_value = None

    with patch('requests.get', return_value=mock_response):

        result = get_currency_rates(currencies)

        # Проверяем результат
        assert result[0] == {"currency": "USD", "rate": 92.35}
        assert result[1] == {"currency": "EUR", "rate": 98.77}
        assert result[2] == {"currency": "CNY", "rate": 12.79}


def test_get_currency_rates_request_error():
    """Тест ошибки сетевого запроса"""
    currencies = ["USD", "EUR"]

    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException("Network error")

        result = get_currency_rates(currencies)

        # Для каждой валюты должна быть попытка запроса и ошибка
        assert result[0] == {}
        assert result[1] == {}



def test_get_currency_rates_currency_not_found(mock_success_response):
    """Тест когда валюта не найдена в ответе API"""
    currencies = ["USD", "JPY"]  # JPY нет в мок-данных

    mock_response = Mock()
    mock_response.json.return_value = mock_success_response
    mock_response.raise_for_status.return_value = None

    with patch('requests.get', return_value=mock_response):


        result = get_currency_rates(currencies)

        assert result[0] == {"currency": "USD", "rate": 92.35}
        assert result[1] == {}  # Для ненайденной валюты возвращается пустой словарь


@patch('requests.get')
def test_successful_price_retrieval(mock_get):
    """Тест успешного получения цен для нескольких акций"""
    # Подготовка мок-ответа для AAPL
    mock_response_aapl = Mock()
    mock_response_aapl.json.return_value = {
        "Global Quote": {
            "05. price": "150.25"
        }
    }
    mock_response_aapl.raise_for_status = Mock()

    # Подготовка мок-ответа для GOOGL
    mock_response_googl = Mock()
    mock_response_googl.json.return_value = {
        "Global Quote": {
            "05. price": "2750.50"
        }
    }
    mock_response_googl.raise_for_status = Mock()

    # Настройка последовательных ответов
    mock_get.side_effect = [mock_response_aapl, mock_response_googl]

    # Вызов функции
    stocks = ["AAPL", "GOOGL"]
    result = get_stock_prices(stocks)

    # Проверка результата
    expected = [
        {"stock": "AAPL", "price": 150.25},
        {"stock": "GOOGL", "price": 2750.50}
    ]
    assert result == expected

@patch('requests.get')
def test_stock_not_found(mock_get):
    """Тест ситуации, когда акция не найдена в ответе API"""
    mock_response = Mock()
    mock_response.json.return_value = {"Global Quote": {}}
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = get_stock_prices(["INVALID"])

    expected = [{"stock": "INVALID", "price": "Акция не найдена"}]
    assert result == expected


@patch('requests.get')
def test_request_exception_handling(mock_get):
    """Тест обработки исключений при запросе"""
    mock_get.side_effect = requests.RequestException("Connection error")

    result = get_stock_prices(["AAPL"])

    # Проверка, что вернулся пустой список при ошибке
    assert result == [{}]
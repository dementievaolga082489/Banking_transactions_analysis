import json
from unittest.mock import patch

import pandas as pd
import pytest

from src.services import load_transactions_from_excel, search_by_phone_numbers


@patch("pandas.read_excel")
def test_successful_load(mock_read_excel):
    """Тест успешной загрузки транзакций из Excel"""
    # Подготовка тестовых данных
    mock_df = pd.DataFrame(
        [{"Описание": "Оплата услуг +7 123 456-78-90", "Сумма": 100}, {"Описание": "Перевод на счет", "Сумма": 500}]
    )
    mock_read_excel.return_value = mock_df

    # Вызов функции
    result = load_transactions_from_excel("test.xlsx")

    # Проверки
    assert result[0]["Описание"] == "Оплата услуг +7 123 456-78-90"
    assert result[1]["Сумма"] == 500
    mock_read_excel.assert_called_once_with("test.xlsx")


@patch("pandas.read_excel")
def test_invalid_excel_format(mock_read_excel):
    """Тест обработки ошибки при неверном формате Excel"""
    mock_read_excel.side_effect = Exception("Invalid Excel format")

    with pytest.raises(Exception, match="Invalid Excel format"):
        load_transactions_from_excel("invalid.xlsx")


def test_phone_with_plus_seven_spaces():
    """Тест поиска номера с +7 и пробелами: +7 XXX XXX-XX-XX"""
    transactions = [
        {"Описание": "Оплата за телефон +7 123 456-78-90", "Сумма": 100},
        {"Описание": "Обычная транзакция", "Сумма": 200},
    ]

    result = json.loads(search_by_phone_numbers(transactions))

    assert len(result) == 1
    assert result[0]["Описание"] == "Оплата за телефон +7 123 456-78-90"

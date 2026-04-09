import pytest
import json

# Импортируем тестируемые функции
from src.reports import spending_by_category


def test_spending_by_category_success(sample_transactions):
    """Тест успешного формирования отчета по категории"""
    result = spending_by_category(sample_transactions, "Продукты", "2024-04-15")

    # Проверка, что результат - JSON строка
    assert isinstance(result, str)

    data = json.loads(result)

    # Проверки
    assert data["category"] == "Продукты"
    assert "period" in data
    assert "start" in data["period"]
    assert "end" in data["period"]
    assert "total_spent" in data
    assert isinstance(data["total_spent"], float)

    # Проверка суммы трат (должны быть только за последние 3 месяца)
    # С 15.01.2024 по 15.04.2024: продукты 15.01, 15.02, 15.03, 15.04
    # Сумма: 300 + 150.75 + 250 + 600 = 1300.75 (без учета знака)
    assert data["total_spent"] == 1300.75


def test_spending_by_category_different_date_formats(sample_transactions):
    """Тест различных форматов входной даты"""
    date_formats = [
        ("2024-04-15", "2024-04-15"),
        ("15.04.2024", "2024-04-15"),
        ("2024/04/15", "2024-04-15"),
        ("15/04/2024", "2024-04-15"),
    ]

    for input_date, expected_date in date_formats:
        result = spending_by_category(sample_transactions, "Продукты", input_date)
        data = json.loads(result)
        assert data["period"]["end"] == expected_date


def test_spending_by_category_invalid_date_format(sample_transactions):
    """Тест с неверным форматом даты"""
    with pytest.raises(ValueError) as exc_info:
        spending_by_category(sample_transactions, "Продукты", "15-04-2024")

    assert "Не удалось распознать формат даты" in str(exc_info.value)



import json
import logging
import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional

import pandas as pd

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def report_to_file(filename: Optional[str] = None):
    """
    Декоратор для сохранения результатов отчетов в файл.

    Args:
        filename: Имя файла для сохранения отчета.
                 Если не указано, генерируется автоматически.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Вызов оригинальной функции
            result = func(*args, **kwargs)

            # Определение имени файла
            if filename is None:
                # Генерация имени файла
                file_name = f"{func.__name__}.json"
            else:
                file_name = filename

            # Сохранение результата в файл
            try:
                # Определяем путь к файлу
                current_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(current_dir, file_name)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(result)

                logger.info(f"Отчет сохранен в файл: {file_path}")
            except Exception as e:
                logger.error(f"Ошибка при сохранении отчета: {e}")

            return result

        return wrapper

    return decorator


@report_to_file()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> str:
    """
    Отчет о тратах по заданной категории за последние 3 месяца.

    Args:
        transactions: DataFrame с транзакциями
        category: Название категории для анализа
        date: Опциональная дата отсчета (формат: 'YYYY-MM-DD' или 'DD.MM.YYYY')
              Если не указана, используется текущая дата

    Returns:
        JSON-строка с отчетом о тратах по категории
    """

    logger.info(f"Начало формирования отчета по категории '{category}'")

    # Определение даты отсчета
    if date is None:
        end_date = datetime.now()
        logger.info(f"Дата не указана, используем текущую: {end_date.strftime('%Y-%m-%d')}")
    else:
        try:
            # Пробуем разные форматы даты
            for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d", "%d/%m/%Y"]:
                try:
                    end_date = datetime.strptime(date, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Не удалось распознать формат даты: {date}")
        except Exception as e:
            logger.error(f"Ошибка парсинга даты: {e}")
            raise

    # Расчет даты начала периода (3 месяца назад)
    start_date = end_date - timedelta(days=90)

    logger.info(f"Период анализа: с {start_date.strftime('%Y-%m-%d')} по {end_date.strftime('%Y-%m-%d')}")

    # Преобразование колонки 'Дата операции' в datetime
    try:
        transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], dayfirst=True)
    except Exception as e:
        logger.error(f"Ошибка преобразования дат: {e}")
        raise

    # Фильтрация по категории и дате
    mask_category = transactions["Категория"] == category
    mask_date = (transactions["Дата операции"] >= start_date) & (transactions["Дата операции"] <= end_date)

    filtered_df = transactions[mask_category & mask_date].copy()

    logger.info(f"Найдено {len(filtered_df)} транзакций по категории '{category}' за указанный период")

    # Расчет общей суммы трат
    total_spent = abs(filtered_df["Сумма операции"].sum())

    # Подготовка результата
    result = {
        "category": category,
        "period": {"start": start_date.strftime("%Y-%m-%d"), "end": end_date.strftime("%Y-%m-%d")},
        "total_spent": float(total_spent),
    }

    logger.info(f"Отчет сформирован. Общая сумма трат: {total_spent}")

    # Возвращаем JSON
    return json.dumps(result, ensure_ascii=False, indent=2, default=str)

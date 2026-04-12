import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.reports import spending_by_category
from src.services import load_transactions_from_excel, search_by_phone_numbers
from src.views import EXL_FILE, main_page

SRC_DIR = Path(__file__).resolve().parent

if __name__ == "__main__":
    """
    Блок для запуска скрипта с вводом даты от пользователя
    """
    print("=" * 60)
    print("Программа для анализа банковских транзакций")
    print("=" * 60)
    print()

    while True:
        # Запрашиваем дату у пользователя
        print("Введите дату и время в формате: ГГГГ-ММ-ДД ЧЧ:ММ:СС")
        print("Например: 2024-01-15 12:00:00")

        user_input = input("Дата и время: ").strip()

        # Проверяем формат ввода
        try:
            datetime.strptime(user_input, "%Y-%m-%d %H:%M:%S")
            date_time_str = user_input
            break
        except ValueError:
            print("\nОшибка: Неверный формат даты!")
            print("Пожалуйста, используйте формат: ГГГГ-ММ-ДД ЧЧ:ММ:СС")
            print("Пример: 2024-01-15 12:00:00\n")
            continue

    print("\n" + "=" * 60)
    print("Выполняется анализ данных...")
    print("=" * 60 + "\n")

    try:
        # Вызываем основную функцию
        result = main_page(date_time_str)

        # Выводим результат в консоль в JSON формате
        print("\n" + "=" * 60)
        print("РЕЗУЛЬТАТ АНАЛИЗА:")
        print("=" * 60 + "\n")

        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

        # Сохраняем результат в файл
        output_file = SRC_DIR.parent / f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)

        print("\n" + "=" * 60)
        print(f"Результат сохранен в файл: {output_file}")
        print("=" * 60)

    except Exception as e:
        print(f"\nОшибка при выполнении анализа: {str(e)}")

df = pd.read_excel(EXL_FILE)
result = spending_by_category(df, "Супермаркеты", "2021-09-27")

# Загрузка и поиск
transactions = load_transactions_from_excel(str(EXL_FILE))
result_ = search_by_phone_numbers(transactions)

# Сохранение результата в файл
with open("phone_transactions.json", "w", encoding="utf-8") as f:
    f.write(result_)

print("Результат сохранен в phone_transactions.json")

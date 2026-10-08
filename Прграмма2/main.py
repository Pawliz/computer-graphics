"""Запуск формы: python main.py. Генерация примера: python main.py --demo."""
import argparse
from pathlib import Path

from processing import generate_example


def main():
    parser = argparse.ArgumentParser(description="Лабораторная № 2, вариант 8")
    parser.add_argument("--demo", action="store_true", help="Сформировать пример без открытия окна")
    args = parser.parse_args()
    examples = Path(__file__).resolve().parent / "examples"
    if args.demo:
        count = generate_example(examples)
        print(f"Готово. Скопировано пикселей: {count}. Результат: {examples / 'result.png'}")
    else:
        if not (examples / "source.png").exists():
            generate_example(examples)
        from runtime_support import configure_tk
        configure_tk()
        from gui import Application
        Application().mainloop()


if __name__ == "__main__":
    main()

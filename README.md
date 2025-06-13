Sakura AI

Сакура — локальний ШІ-асистент для керування ПК, торгівлі на Binance Testnet, сканування системи та роботи в хмарі Dataspaces. Підтримує голосові команди, Telegram-бот, графічний інтерфейс і веб-дашборд.

## Вимоги

- **ОС**: Windows 10/11 (64-біт)
- **Python**: 3.8+ (64-біт)
- **Docker**: Для хмарного розгортання (опціонально)
- **Visual C++ Redistributable**: [Завантажити (x64)](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)
- **Інтернет**: Для API та синхронізації
- **Модель GPT4All**: `mistral-7b-openorca.Q4_0.gguf` [](https://huggingface.co/nomic-ai)

## Встановлення

1. **Створіть папку**:
   - Створіть `C:\Zhanna\startup`.
   - Помістіть файли проєкту в цю папку.

2. **Розташуйте модель**:
   - Завантажте `mistral-7b-openorca.Q4_0.gguf`.
   - Помістіть у `C:\Zhanna\startup\models`.

3. **Налаштуйте змінні середовища**:
   - Скопіюйте `.env` до `C:\Zhanna\startup` або оновіть `config.py`.
   - Оновіть ключі:
     - `BINANCE_TESTNET_API_KEY`, `BINANCE_TESTNET_API_SECRET`: [testnet.binancefuture.com](https://testnet.binancefuture.com).
     - `DATASPACES_API_KEY`: [app.dataspaces.io](https://app.dataspaces.io).
   - Приклад `.env`:
TELEGRAM_TOKEN=7339214786:AAHIAywsmhBADReT2Oh_tS8XDcO-6-DkVGk
GITHUB_TOKEN=your_github_token
XAI_API_KEY=your_xai_api_key
OPENAI_API_KEY=your_openai_api_key
BINANCE_TESTNET_API_KEY=your_testnet_key
BINANCE_TESTNET_API_SECRET=your_testnet_secret
DATASPACES_API_KEY=your_dataspaces_key
ENCRYPTION_KEY=1234567890abcdef1234567890abcdef

text

Згорнути

Згорни

Копіювати
4. **Встановіть Python**:
- Завантажте Python 3.8+ (64-біт) із [python.org](https://python.org).
- Оновіть pip:
```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip
Встановіть Visual C++ Redistributable:
Завантажте x64 версію.
Встановіть і перезавантажте ПК, якщо потрібно.
Встановіть бібліотеки:
bash

Згорнути

Згорни

Виконати

Копіювати
cd C:\Zhanna\startup
pip install -r requirements.txt
Встановіть Docker (опціонально):
Завантажте Docker Desktop.
Увійдіть:
bash

Згорнути

Згорни

Виконати

Копіювати
docker login
Запуск
Відкрийте термінал:
bash

Згорнути

Згорни

Виконати

Копіювати
cd C:\Zhanna\startup
Запустіть Сакуру:
bash

Згорнути

Згорни

Виконати

Копіювати
python main.py
Запустіть GUI:
bash

Згорнути

Згорни

Виконати

Копіювати
python gui.py
Запустіть веб-сервер:
bash

Згорнути

Згорни

Виконати

Копіювати
python server.py
Відкрийте http://localhost:8000.
Використання
Telegram
Знайдіть бота (@YourBot).
Надішліть /start.
Кнопки: Система, Сканувати, Крипторинок, Мої угоди, Торгувати, Позиції, Testnet, Хмара.
GUI
Запустіть gui.py.
Використовуйте кнопки або голосові команди.
Веб-дашборд
Переглядайте дані на http://localhost:8000.
Ручне розгортання на Dataspaces
Побудуйте образ:
bash

Згорнути

Згорни

Виконати

Копіювати
docker build -t sakura-ai:latest .
Завантажте:
bash

Згорнути

Згорни

Виконати

Копіювати
docker push sakura-ai:latest
Розгорніть через app.dataspaces.io.
Діагностика
Логи: C:\Zhanna\startup\sakura.log.
Помилки з GPT4All:
Переконайтеся, що mistral-7b-openorca.Q4_0.gguf є в C:\Zhanna\startup\models.
Перевстановіть бібліотеку:
bash

Згорнути

Згорни

Виконати

Копіювати
pip uninstall gpt4all -y
pip install gpt4all==2.8.2
Встановіть Visual C++ Redistributable (x64).
Перевірте архітектуру:
bash

Згорнути

Згорни

Виконати

Копіювати
python -c "import platform; print(platform.architecture())"
Помилки з бібліотеками:
bash

Згорнути

Згорни

Виконати

Копіювати
pip install -r requirements.txt --force-reinstall
Віртуальне середовище:
bash

Згорнути

Згорни

Виконати

Копіювати
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
deactivate
Розробник
Версія: 1.0
Дата: Червень 2025
Контакт: Telegram для підтримки
Удачі з Сакурою! 😊


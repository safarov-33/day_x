# Qarz — учёт долгов магазина

Веб-приложение на Django для учёта покупателей, долгов и платежей.
Поддерживает роли владельца, кассира и клиента, журнал действий и интерфейс
на русском, английском и таджикском языках.

## Локальный запуск

Нужен Python 3.12 или новее. Проект проверен на Python 3.14.

```bash
git clone https://github.com/safarov-33/day_x.git
cd day_x
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

В Windows используйте `python` вместо `python3` и активируйте окружение
командой `.venv\Scripts\activate` в командной строке.

Откройте http://127.0.0.1:8000/ и зарегистрируйте владельца магазина.
Для доступа к панели `/admin/` создайте отдельного администратора:

```bash
python manage.py createsuperuser
```

SQLite-база создаётся при миграции. Локальные данные, резервные копии,
виртуальное окружение и файлы `.env` исключены из Git.

## Настройки

Настройки читаются из переменных окружения. Файлы `.env` автоматически
не загружаются. По умолчанию включён режим разработки, письма для сброса
пароля выводятся в терминал.

- `DJANGO_DEBUG`: `1` для разработки, `0` для сервера.
- `DJANGO_SECRET_KEY`: собственный секретный ключ; обязателен при `DJANGO_DEBUG=0`.
- `DJANGO_ALLOWED_HOSTS`: допустимые домены через запятую.
- `DJANGO_EMAIL_BACKEND`, `DJANGO_EMAIL_HOST`, `DJANGO_EMAIL_PORT`,
  `DJANGO_EMAIL_USER`, `DJANGO_EMAIL_PASSWORD`, `DJANGO_EMAIL_TLS`,
  `DJANGO_FROM_EMAIL`: настройки отправки писем.

Встроенный ключ предназначен только для локальной разработки.
`runserver` используется для разработки; конфигурация серверного размещения
в этот репозиторий не включена.

## Проверки и обслуживание

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py backup_db backups/manual.sqlite3
```

Команда резервного копирования сохраняет SQLite-базу по указанному пути.
Для каждой копии укажите новое имя файла.
Инструкции по переводам находятся в [locale/README.md](locale/README.md).
`project_explanation.txt` содержит заметки для защиты и снимок кода на момент
их подготовки; актуальная реализация находится в исходных файлах проекта.

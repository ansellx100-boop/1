# Rostekhnadzor Research Agent

Прототип ресейч-агента, который отслеживает обновления на сайте Ростехнадзора (`https://www.gosnadzor.ru`), скачивает свежие материалы и формирует краткий дайджест.

## Быстрый старт

```bash
pip3 install -e .
python3 -m rostekhnadzor_agent.cli run --limit 10
```

Альтернативно, без установки пакета:

```bash
PYTHONPATH=src python3 -m rostekhnadzor_agent.cli run --limit 10
```

## Ключевые возможности

- Поддержка RSS и HTML листинга (`/news/`).
- Сохранение состояния в `state/rostekhnadzor_news.json` с хэшами материалов.
- Простая эвристическая суммаризация текста и генерация Markdown-дайджеста (`reports/<дата>.md`).
- Флаг `--no-report` для отключения отчёта и `--force` для переобработки известных материалов.
- Email-уведомления через SMTP (параметры `--email-to`, `--smtp-host`, `--smtp-user`, `--smtp-password`).

## Полезные команды

```bash
# Разовый запуск без создания отчёта
PYTHONPATH=src python3 -m rostekhnadzor_agent.cli run --limit 5 --no-report

# Смена директории состояния и базового URL (например для тестов)
PYTHONPATH=src python3 -m rostekhnadzor_agent.cli run --state-path tmp/state.json --base-url https://www.gosnadzor.ru

# Отправка дайджеста на почту (SMTP, STARTTLS)
PYTHONPATH=src python3 -m rostekhnadzor_agent.cli run --limit 5 \
  --email-to ansellx@mail.ru \
  --smtp-host smtp.example.com --smtp-user user@example.com --smtp-password secret \
  --email-from digest@example.com

# Можно использовать переменные окружения SMTP_HOST, SMTP_USER, SMTP_PASSWORD.
```

Подробности по архитектуре см. в `docs/rostekhnadzor_research_agent.md`.


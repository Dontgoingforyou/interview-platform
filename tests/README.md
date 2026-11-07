# Автоматические тесты

- `test_<app>/` — backend unit и integration тесты Django-приложений.
- `test_security/` — проверки исправлений безопасности.
- `helpers.py` и `conftest.py` — общие фикстуры.

Запуск из корня:

```bash
poetry run pytest
```

`pyproject.toml` добавляет `project/` в Python path, поэтому импорты Django-приложений
остаются плоскими после миграции.

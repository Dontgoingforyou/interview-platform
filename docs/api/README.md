# API

`openapi.yaml` генерируется из DRF/drf-spectacular и хранится в Git.

```bash
DJANGO_TESTING=1 DISABLE_VECTOR_SIGNALS=1 \
poetry run python project/manage.py spectacular \
  --file docs/api/openapi.yaml --validate
```

Изменение endpoint, схемы запроса или ответа должно обновлять контракт в том же MR.

# Авторизация и роли в vector_search API

## Обзор

Все эндпоинты vector_search API защищены локальной сессией с поддержкой ролей.

## Роли и права доступа

### Роль: Admin (`manager_role='admin'`)
**Группа:** `role_admin`

**Права:**
- Видит ВСЕ результаты поиска
- Может искать по любым данным
- Может просматривать похожие сущности для любых объектов
- Видит статистику по всем данным

### Роль: Manager (`manager_role='manager'`)
**Группы:** `employment-managers`, `cv-managers`

**Права:**
- Видит ТОЛЬКО свои данные (где `manager_email` = его email)
- Не может искать данные других менеджеров
- Не может просматривать похожие сущности для чужих объектов
- Видит статистику только по своим данным

## Эндпоинты

### 1. POST `/api/vector/search/` - Семантический поиск

**Авторизация:** Обязательна (локальная сессия)

**Фильтрация по ролям:**
- **Админ:** Поиск по всей БД
- **Менеджер:** Автоматически добавляется фильтр `manager_email=<его email>`

**Пример запроса (менеджер):**
```json
{
  "query": "студенты по Python",
  "entity_type": "intern",
  "top_k": 10
}
```

**Поведение:**
- Менеджер получит только студентов, где `metadata.manager_email` = его email
- Если менеджер попытается указать `manager_email` другого менеджера - получит `403 Forbidden`

**Пример ответа с ошибкой:**
```json
{
  "error": "Доступ запрещен",
  "details": "Вы можете искать только свои данные"
}
```

---

### 2. POST `/api/vector/similar/` - Поиск похожих сущностей

**Авторизация:** Обязательна (локальная сессия)

**Фильтрация по ролям:**
- **Админ:** Может искать похожие для любых сущностей
- **Менеджер:** Сначала проверяется, принадлежит ли сущность менеджеру (по `metadata.manager_email`)

**Пример запроса:**
```json
{
  "entity_type": "interview",
  "entity_id": 123,
  "top_k": 5
}
```

**Поведение:**
- Проверяется, принадлежит ли `interview #123` текущему менеджеру
- Если нет - возвращается `403 Forbidden`
- Если да - ищутся похожие интервью ТОЛЬКО среди его данных

---

### 3. GET `/api/vector/stats/` - Статистика векторизации

**Авторизация:** Обязательна (локальная сессия)

**Фильтрация по ролям:**
- **Админ:** Статистика по всем векторизованным объектам
- **Менеджер:** Статистика только по объектам с `metadata.manager_email` = его email

**Пример ответа (менеджер):**
```json
{
  "total_embeddings": 150,
  "by_type": {
    "interview": 100,
    "intern": 30,
    "offer": 20
  },
  "last_updated": "2026-01-29T18:42:58.510Z",
  "embedding_dimension": 1536,
  "role": "manager"
}
```

---

## Коды ответов

| Код | Описание |
|-----|----------|
| `200 OK` | Успешный запрос |
| `400 Bad Request` | Некорректные параметры |
| `401 Unauthorized` | Не авторизован (нет сессии) |
| `403 Forbidden` | Доступ запрещен (попытка доступа к чужим данным) |
| `404 Not Found` | Сущность не найдена |
| `500 Internal Server Error` | Внутренняя ошибка сервера |

---

## Технические детали

### Permission Class: `IsManagerOrAdmin`

Расположение: `vector_search/permissions.py`

**Проверяет:**
1. Наличие `keycloak_id` в сессии
2. Флаг `keycloak_user = True`

### Логика фильтрации

**В `SemanticSearchAPIView`:**
```python
manager_role = request.session.get('manager_role', 'manager')
manager_email = request.session.get('manager_email')

if manager_role != 'admin' and manager_email:
    filters['manager_email'] = manager_email
```

**В `SimilarEntitiesAPIView`:**
1. Проверяется принадлежность запрашиваемой сущности
2. При поиске похожих применяется фильтр по `manager_email`

**В `VectorStatsAPIView`:**
```python
if manager_role != 'admin' and manager_email:
    queryset = queryset.filter(metadata__manager_email=manager_email)
```

---

## Тестирование

### Тест авторизации

```bash
# Без авторизации - должен вернуть 401
curl -X POST http://localhost:82/api/vector/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

### Тест с авторизацией (через браузер)

1. Войти локально: `http://localhost:82/login`
2. Выполнить поиск: `POST /api/vector/search/`
3. Проверить, что возвращаются только свои данные

### Тест прав админа vs менеджера

```python
# Админ
session['manager_role'] = 'admin'
response = client.post('/api/vector/search/', data={'query': 'test'})
# Должен видеть все данные

# Менеджер
session['manager_role'] = 'manager'
session['manager_email'] = 'manager@example.com'
response = client.post('/api/vector/search/', data={'query': 'test'})
# Должен видеть только свои данные
```

---

## Безопасность

### Что проверяется

- Проверка сессии на всех эндпоинтах
- Автоматическая фильтрация по `manager_email` для менеджеров
- Проверка доступа при просмотре похожих сущностей
- Логирование попыток несанкционированного доступа

### На что смотреть

1. **Метаданные должны содержать `manager_email`**
   - При векторизации убедитесь, что `metadata` содержит `manager_email`
   - См. `vector_search/utils.py::extract_metadata()`

2. **Читаемые имена в метаданных: `company_name`, `direction_name`**
   - В `metadata` для interview добавлены `company_name` и `direction_name` (помимо `company_id`, `direction_id`)
   - Для entity_type `company` добавлен `company_name`
   - Эти поля можно показать вместо числового id

3. **Проверка на уровне БД**
   - Используется `metadata->>'manager_email'` для фильтрации
   - Работает только если PostgreSQL с JSON поддержкой

4. **Логирование**
   - Запросы пишутся в `SearchLog`: фильтры и число результатов. Email пользователя в лог не попадает.

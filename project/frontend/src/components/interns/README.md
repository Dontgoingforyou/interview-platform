# Раздел «Студенты» (React) — архитектура

Цель: **тонкие страницы** (`pages/interns/*`) только склеивают данные и секции; вся разметка и локальная логика UI — в `components/interns/*`.

## Слои и зависимости (строго сверху вниз)

1. **`pages/interns/`** — маршрут, хуки данных (`useInternsList` и т.д.), `useSearchParams`, модалки уровня страницы. **Не** содержит разметку таблицы, полей формы.
2. **`components/interns/`** — презентация по зонам:
   - `list/` — десктоп-таблица, мобильный список, скелетон, шапка/строка таблицы, пустое состояние
   - `form/` — поля формы создания/редактирования
   - В корне фичи — общие виджеты списка (`InternFilters.tsx`); при росте фильтров — **`filters/`**
3. **`hooks/interns/`** — TanStack Query, мутации. **Не** импортируют компоненты из `components/interns`.
4. **`api/internsApi.ts`**, **`types/intern.ts`** — контракт с бэкендом.
5. **`utils/interns/`** — чистые функции для студентов: `internListParams.ts`, `internTelegram.ts` (`internTelegramHref` — URL Telegram по username).

**Запрещено:** компоненты из `components/interns` импортируют файлы из `pages/`.

## Утилиты именно этой фичи

Хелперы студентов в **`src/utils/interns/`** (`internListParams`, `internTelegram`, …).

Опционально только для студентов и нигде больше: **`components/interns/utils/`** — см. глобальные правила.

## Текущая структура папок компонентов

```
components/interns/
  InternFilters.tsx
  form/
  list/
```

Общие UI-атомы (`Pagination`, `TableScroll`, `CollapsibleSection`) — в `components/ui/`.

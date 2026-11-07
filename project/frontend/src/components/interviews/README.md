# Раздел «Собеседования» (React) — архитектура

Цель: **тонкие страницы** (`pages/interviews/*`) только склеивают данные и секции; вся разметка и локальная логика UI — в `components/interviews/*`.

## Слои и зависимости (строго сверху вниз)

1. **`pages/interviews/`** — маршрут, хуки данных (`useInterviewList` и т.д.), `useSearchParams`, модалки уровня страницы. **Не** содержит разметку таблицы, метрик, полей формы.
2. **`components/interviews/`** — презентация по зонам:
   - `list/` — десктоп-таблица, мобильный список, скелетон, тулбар, пустое состояние, шапка/строка таблицы
   - `analytics/` — блоки метрик и сводок по типам
   - `form/` — поля формы создания/редактирования, типы опций селектов
   - В корне фичи — общие виджеты списка (`InterviewFilters.tsx`, `TranscriptionCell.tsx`, …); при росте фильтров — **`filters/`**
3. **`hooks/interviews/`** — TanStack Query, мутации. **Не** импортируют компоненты из `components/interviews`.
4. **`api/interviewsApi.ts`**, **`types/interview.ts`** — контракт с бэкендом.
5. **`utils/interviews/`** — чистые функции для собеседований (`interviewListParams`, `interviewCells`, …). См. **`.cursor/rules/react-frontend.mdc`** → «Утилиты».

**Запрещено:** компоненты из `components/interviews` импортируют файлы из `pages/`.

## Утилиты именно этой фичи

Доменные хелперы собеседований лежат в **`src/utils/interviews/`** (импорты вида `../../utils/interviews/...`).

Опционально только для интервью и нигде больше: **`components/interviews/utils/`** — см. глобальные правила.

## Текущая структура папок компонентов

```
components/interviews/
  InterviewFilters.tsx
  InterviewMobileCard.tsx
  TranscriptionCell.tsx
  analytics/
  form/
  list/
```

Общие UI-атомы (`Pagination`, `TableScroll`, `CollapsibleSection`, `MetricCard`, `MetricAnimatedStrong`, `MetricsGridSection`) — в `components/ui/`.

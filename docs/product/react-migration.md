# Раздел в React

Портал — React SPA. Вход локальный.

Новый раздел:

1. Маршрут в `project/frontend/src/appRoutes.tsx`. Тяжёлую страницу подключать через `React.lazy`.
2. Страница в `project/frontend/src/pages/`.
3. Запросы в `project/frontend/src/api/`, клиент `api/client.ts`.
4. Типы в `project/frontend/src/types/`. Список с пагинацией — `Paginated<T>` из `types/common.ts`.
5. Данные через TanStack Query, ключ вида `['debts', 'list', filters]`.
6. Общие классы — `styles/components.css` и `styles/tables.css`. Свои стили раздела — отдельный файл.
7. Кнопки, таблицы и фильтры — из `components/ui/`.
8. Пункт меню — `constants/navigation.ts`, путь совпадает с маршрутом.

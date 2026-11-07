# Реестр экранов

Реестр описывает React UI.

| screen_id | Назначение | Требования | Реализация |
|---|---|---|---|
| sign-in | Локальный вход | FR-001 | `project/frontend/src/` |
| interns-list | Список и поиск стажёров | FR-002 | `project/frontend/src/components/interns/` |
| interviews-list | Список собеседований | FR-003 | `project/frontend/src/pages/InterviewsListPage.tsx` |
| offers-list | Работа с офферами | FR-004 | `project/frontend/src/` |
| manager-dashboard | Аналитика менеджера | FR-005 | `project/frontend/src/components/managers/` |
| whats-new | Журнал «Что нового» в оболочке, без отдельного маршрута; студенту портала не показывается | FR-010 | `project/frontend/src/components/layout/ChangelogButton.tsx` |

При видимом изменении экрана синхронно обновляются FR, TC, этот реестр и прототип.

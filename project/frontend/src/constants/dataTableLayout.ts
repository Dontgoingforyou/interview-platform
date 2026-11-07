/**
 * Модификатор для `.data-table`: две левые колонки липкие при горизонтальном скролле.
 * Стили и фон при скролле — `tables.css` (+ TableScroll → `table-scroll--h-scrolled`).
 */
export const DATA_TABLE_STICKY_LEADING = 'data-table--sticky-leading'

/**
 * Вместе со `data-table--sticky-leading`: липкой остаётся только первая колонка.
 * Нужно для table-layout:fixed + % ширин — иначе вторая липкая с left в rem не совпадает с фактической шириной первой (наложение, «полоса», просвечивание).
 */
export const DATA_TABLE_STICKY_FIRST_COL_ONLY = 'data-table--sticky-first-col-only'

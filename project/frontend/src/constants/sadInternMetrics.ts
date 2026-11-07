/** Карточки аналитики «грустят» (ключи ответа API). */
export const SAD_INTERN_METRICS_MAIN = [
  { key: 'total', label: 'Всего в списке', format: 'integer' as const },
  { key: 'with_contact', label: 'Есть контакт в Telegram', format: 'integer' as const },
  { key: 'avg_wait', label: 'Среднее ожидание', format: 'days' as const },
  {
    key: 'longest_wait_days',
    label: 'Дольше всех ждёт',
    format: 'days' as const,
    subtitleKey: 'longest_wait_name' as const,
    light: true,
  },
] as const

/** Ключ tooltips в ответе API для info-иконки. */
export const SAD_INTERN_METRIC_TOOLTIP_KEYS: Record<string, string> = {
  total: 'total',
  with_contact: 'with-contact',
  avg_wait: 'avg-wait',
  longest_wait_days: 'longest',
}

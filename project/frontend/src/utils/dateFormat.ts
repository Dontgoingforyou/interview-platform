/**
 * Форматирование ISO-дат (YYYY-MM-DD) для отображения в таблицах.
 */

/** Формат DD.MM.YYYY (полный год) — для страницы студентов. */
export function formatRuDate(iso: string | null | undefined): string {
  if (!iso) {
    return '—'
  }
  const d = String(iso).slice(0, 10)
  const [y, m, day] = d.split('-')
  if (!y || !m || !day) {
    return String(iso)
  }
  return `${day}.${m}.${y}`
}

/** Формат DD.MM.YY (короткий год) — для страницы собеседований. */
export function formatShortRuDate(iso: string | null | undefined): string {
  if (!iso || !String(iso).trim()) {
    return '—'
  }
  const s = String(iso).trim()
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(s)
  if (match) {
    const [, y, mo, d] = match
    return `${d}.${mo}.${y.slice(-2)}`
  }
  return s
}

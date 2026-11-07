/** Ссылка на Telegram по username студента в списке офферов. */
export function offerTelegramHref(username: string | null | undefined): string | null {
  if (!username || !String(username).trim()) {
    return null
  }
  const h = String(username).trim()
  const uname = h.startsWith('@') ? h.slice(1) : h
  return `https://t.me/${uname}`
}

/** Форматирование суммы оффера для ячейки таблицы / карточки. */
export function formatOfferAmountCell(amount: string | null): string {
  if (amount == null || amount === '') {
    return '—'
  }
  const n = Number(amount)
  if (!Number.isFinite(n)) {
    return '—'
  }
  return Math.round(n).toLocaleString('ru-RU')
}

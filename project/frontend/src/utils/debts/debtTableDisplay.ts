import type { DebtRowHighlight } from '../../types/debt'

export function debtRowClassName(row: { row_highlight: DebtRowHighlight }): string {
  if (row.row_highlight === 'paid_fully') {
    return 'row-paid-fully'
  }
  if (row.row_highlight === 'not_paying') {
    return 'row-not-paying'
  }
  return ''
}

export function formatPaymentStatusLabel(status: string): string {
  if (status === 'searching') {
    return 'Снова ищем'
  }
  if (status === 'paying') {
    return 'Платит'
  }
  return 'Без статуса'
}

export function telegramHref(username: string): string | null {
  const t = username.trim()
  if (!t) {
    return null
  }
  const handle = t.startsWith('@') ? t.slice(1) : t
  return `https://t.me/${handle}`
}

export function balanceCellClass(balanceStr: string): string {
  const n = parseFloat(balanceStr.replace(',', '.'))
  if (Number.isNaN(n)) {
    return ''
  }
  if (n < 0) {
    return 'text-danger'
  }
  if (n === 0) {
    return 'text-success'
  }
  return ''
}

export function paymentStatusCellClass(status: string): string {
  if (status === 'searching') {
    return 'text-danger'
  }
  if (status === 'paying') {
    return 'text-success'
  }
  return ''
}

/** Дата акта из ISO (YYYY-MM-DD) в ДД.ММ.ГГГГ для таблицы и карточек «по месяцам». */
export function formatActDate(iso: string | null): string {
  if (!iso) {
    return '—'
  }
  const [y, m, d] = iso.split('-')
  if (!y || !m || !d) {
    return iso
  }
  return `${d}.${m}.${y}`
}

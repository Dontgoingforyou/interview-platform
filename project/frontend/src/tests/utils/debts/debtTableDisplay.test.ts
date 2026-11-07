import { describe, expect, it } from 'vitest'

import {
  balanceCellClass,
  debtRowClassName,
  formatActDate,
  formatPaymentStatusLabel,
  paymentStatusCellClass,
  telegramHref,
} from '../../../utils/debts/debtTableDisplay'

describe('debtRowClassName', () => {
  it('классы highlight', () => {
    expect(debtRowClassName({ row_highlight: 'paid_fully' })).toBe('row-paid-fully')
    expect(debtRowClassName({ row_highlight: 'not_paying' })).toBe('row-not-paying')
    expect(debtRowClassName({ row_highlight: 'default' })).toBe('')
  })
})

describe('formatPaymentStatusLabel', () => {
  it('известные и fallback', () => {
    expect(formatPaymentStatusLabel('searching')).toBe('Снова ищем')
    expect(formatPaymentStatusLabel('paying')).toBe('Платит')
    expect(formatPaymentStatusLabel('other')).toBe('Без статуса')
  })
})

describe('telegramHref', () => {
  it('null для пустого; снимает @', () => {
    expect(telegramHref('')).toBeNull()
    expect(telegramHref('  ')).toBeNull()
    expect(telegramHref('@user')).toBe('https://t.me/user')
    expect(telegramHref('user')).toBe('https://t.me/user')
  })
})

describe('balanceCellClass / paymentStatusCellClass', () => {
  it('цвет остатка и статуса', () => {
    expect(balanceCellClass('-10')).toBe('text-danger')
    expect(balanceCellClass('0')).toBe('text-success')
    expect(balanceCellClass('1,5')).toBe('')
    expect(balanceCellClass('x')).toBe('')
    expect(paymentStatusCellClass('searching')).toBe('text-danger')
    expect(paymentStatusCellClass('paying')).toBe('text-success')
    expect(paymentStatusCellClass('unknown')).toBe('')
  })
})

describe('formatActDate', () => {
  it('ISO → ДД.ММ.ГГГГ; null и битый → fallback', () => {
    expect(formatActDate(null)).toBe('—')
    expect(formatActDate('2025-03-09')).toBe('09.03.2025')
    expect(formatActDate('bad')).toBe('bad')
  })
})

import type { SelectOption } from '../types/common'

/** Согласовано с debts.models.Debt.PAYMENT_STATUS_CHOICES */
export const DEBT_PAYMENT_STATUS_OPTIONS: SelectOption[] = [
  { value: 'searching', label: 'Снова ищем' },
  { value: 'paying', label: 'Платит' },
  { value: 'unknown', label: 'Без статуса' },
]

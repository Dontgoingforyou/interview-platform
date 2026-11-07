import type { InternOption } from '../../../api/referenceApi'

/** Опция для react-select: студент. */
export interface InternSelectOption {
  value: number
  label: string
  directionId: number | null
  directionName: string | null
}

/** Опция менеджера: email + отображаемое имя. */
export interface ManagerSelectOption {
  value: string
  label: string
}

export interface DirectionSelectOption {
  value: number
  label: string
}

export interface CompanySelectOption {
  value: number | string
  label: string
}

/** Статичные списки (тип / формат). */
export interface ChoiceSelectOption {
  value: string
  label: string
}

export function internToOption(i: InternOption): InternSelectOption {
  return {
    value: i.id,
    label: `${i.full_name} (id ${i.id})`,
    directionId: i.direction_id,
    directionName: i.direction_name,
  }
}

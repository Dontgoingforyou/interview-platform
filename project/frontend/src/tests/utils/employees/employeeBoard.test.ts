import { describe, expect, it } from 'vitest'

import { employeeBoardDirectionLabel } from '../../../utils/employees/employeeBoard'

describe('employeeBoardDirectionLabel', () => {
  const dict = { '1': 'Java', '2': 'QA' }

  it('возвращает название или —', () => {
    expect(employeeBoardDirectionLabel(dict, 1)).toBe('Java')
    expect(employeeBoardDirectionLabel(dict, null)).toBe('—')
    expect(employeeBoardDirectionLabel(dict, 99)).toBe('—')
  })
})

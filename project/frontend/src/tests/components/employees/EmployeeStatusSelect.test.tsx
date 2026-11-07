import { fireEvent, render, screen } from '@testing-library/react'
import type { ComponentProps } from 'react'
import { describe, expect, it, vi } from 'vitest'

import EmployeeStatusSelect from '../../../components/employees/board/EmployeeStatusSelect'
import { INTERN_STATUS_ACTIVE, INTERN_STATUS_LEFT } from '../../../constants/internStatuses'

function renderSelect(props: Partial<ComponentProps<typeof EmployeeStatusSelect>> = {}) {
  const onChange = vi.fn()
  render(
    <EmployeeStatusSelect
      status={INTERN_STATUS_ACTIVE}
      statusDisplay="Активный"
      onChange={onChange}
      {...props}
    />,
  )
  return { onChange }
}

describe('EmployeeStatusSelect', () => {
  it('открывает список и не закрывает его тем же жестом', () => {
    renderSelect()
    fireEvent.pointerDown(screen.getByRole('button', { name: 'Статус: Активный. Нажмите для изменения' }))
    const select = screen.getByRole('combobox', { name: 'Статус: Активный' })
    fireEvent.click(select)
    expect(screen.getByRole('combobox', { name: 'Статус: Активный' })).toBeInTheDocument()
  })

  it('сохраняет выбор, если blur пришёл раньше change', () => {
    const { onChange } = renderSelect()
    fireEvent.pointerDown(screen.getByRole('button', { name: 'Статус: Активный. Нажмите для изменения' }))
    const select = screen.getByRole('combobox', { name: 'Статус: Активный' })
    fireEvent.blur(select)
    fireEvent.change(select, { target: { value: INTERN_STATUS_LEFT } })
    expect(onChange).toHaveBeenCalledTimes(1)
    expect(onChange).toHaveBeenCalledWith(INTERN_STATUS_LEFT)
  })

  it('не открывает список, когда правка запрещена', () => {
    renderSelect({ disabled: true })
    fireEvent.pointerDown(screen.getByRole('button', { name: 'Статус: Активный. Нажмите для изменения' }))
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
  })
})

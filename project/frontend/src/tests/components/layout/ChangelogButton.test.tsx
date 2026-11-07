import { beforeEach, describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import ChangelogButton from '../../../components/layout/ChangelogButton'
import { changelogSeenStorageKey, type WhatsNewEntry } from '../../../constants/changelog'
import { KEYCLOAK_GROUP_EMPLOYMENT, KEYCLOAK_GROUP_STUDENTS } from '../../../constants/keycloakGroups'
import { useAuthStore, type AuthUser } from '../../../store/authStore'

function user(username: string, managerRole = 'manager', groups: string[] = []): AuthUser {
  return {
    email: `${username}@test`,
    username,
    full_name: username,
    manager_role: managerRole,
    groups,
  }
}

function entries(count: number): WhatsNewEntry[] {
  return Array.from({ length: count }, (_, index) => ({
    version: `1.1.${400 - index}`,
    date: '2026-03-21',
    text: `Запись ${index + 1}`,
  }))
}

describe('ChangelogButton', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({ user: user('anna') })
  })

  it('при пустом списке не зажигает огонёк и показывает пустую фразу', async () => {
    const clicker = userEvent.setup()
    render(<ChangelogButton entries={[]} />)

    expect(screen.getByRole('button', { name: 'Что нового' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /непрочитанное/ })).not.toBeInTheDocument()

    await clicker.click(screen.getByRole('button', { name: 'Что нового' }))
    expect(screen.getByRole('dialog', { name: 'Что нового' })).toBeInTheDocument()
    expect(screen.getByText('Пока нет заметных обновлений')).toBeInTheDocument()
    expect(document.documentElement.hasAttribute('data-scroll-lock')).toBe(false)
    expect(document.documentElement.style.overflow).toBe('hidden')
    expect(document.body.style.overflow).toBe('hidden')
  })

  it('гасит огонёк после открытия и не переносит отметку на другую учётку', async () => {
    const clicker = userEvent.setup()
    const list = entries(11)
    const { rerender } = render(<ChangelogButton entries={list} />)

    expect(screen.getByRole('button', { name: 'Что нового, есть непрочитанное обновление' })).toBeInTheDocument()

    await clicker.click(screen.getByRole('button', { name: 'Что нового, есть непрочитанное обновление' }))

    expect(screen.getByRole('button', { name: 'Что нового' })).toBeInTheDocument()
    expect(localStorage.getItem(changelogSeenStorageKey('anna'))).toBe('1.1.400')
    expect(screen.getAllByRole('listitem')).toHaveLength(10)
    expect(screen.getByRole('button', { name: 'Показать предыдущие' })).toBeInTheDocument()

    await clicker.click(screen.getByRole('button', { name: 'Показать предыдущие' }))
    expect(screen.getAllByRole('listitem')).toHaveLength(11)

    useAuthStore.setState({ user: user('boris') })
    rerender(<ChangelogButton entries={list} />)

    expect(screen.getByRole('button', { name: 'Что нового, есть непрочитанное обновление' })).toBeInTheDocument()
    expect(localStorage.getItem(changelogSeenStorageKey('boris'))).toBeNull()
  })

  it('не показывает журнал студенту портала', () => {
    useAuthStore.setState({
      user: user('student', 'student', [KEYCLOAK_GROUP_STUDENTS]),
    })
    render(<ChangelogButton entries={entries(1)} />)

    expect(screen.queryByRole('button', { name: /Что нового/ })).not.toBeInTheDocument()
  })

  it('показывает журнал, если у студента есть менеджерская группа', () => {
    useAuthStore.setState({
      user: user('lead', 'manager', [KEYCLOAK_GROUP_STUDENTS, KEYCLOAK_GROUP_EMPLOYMENT]),
    })
    render(<ChangelogButton entries={entries(1)} />)

    expect(screen.getByRole('button', { name: /Что нового/ })).toBeInTheDocument()
  })
})

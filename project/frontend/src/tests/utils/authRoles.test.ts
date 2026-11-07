import { describe, expect, it } from 'vitest'

import { KEYCLOAK_GROUP_ADMIN, KEYCLOAK_ROLE_NO_ACCESS } from '../../constants/keycloakRoles'
import {
  KEYCLOAK_GROUP_EMPLOYMENT,
  KEYCLOAK_GROUP_HR,
  KEYCLOAK_GROUP_MENTORS,
  KEYCLOAK_GROUP_OUTSTAFF,
  KEYCLOAK_GROUP_STUDENTS,
} from '../../constants/keycloakGroups'
import type { AuthUser } from '../../store/authStore'
import {
  canWriteInterviews,
  emailsEqualIgnoreCase,
  isAdminUser,
  isHrOrOutstaffUser,
  isMentorUser,
  isPureStudentPortalUser,
} from '../../utils/authRoles'

function user(partial: Partial<AuthUser> = {}): AuthUser {
  return {
    email: 'm@example.com',
    username: 'manager',
    full_name: 'Менеджер',
    manager_role: 'manager',
    groups: [],
    ...partial,
  }
}

describe('isAdminUser', () => {
  it('возвращает false для null', () => {
    expect(isAdminUser(null)).toBe(false)
  })

  it('возвращает true при manager_role === admin', () => {
    expect(isAdminUser(user({ manager_role: 'admin' }))).toBe(true)
  })

  it('возвращает true при наличии группы администратора Keycloak', () => {
    expect(isAdminUser(user({ groups: [KEYCLOAK_GROUP_ADMIN] }))).toBe(true)
  })

  it('возвращает false для обычного менеджера без группы admin', () => {
    expect(isAdminUser(user())).toBe(false)
  })
})

describe('canWriteInterviews', () => {
  it('возвращает false для null', () => {
    expect(canWriteInterviews(null)).toBe(false)
  })

  it('возвращает false для manager_role hr (как в сессии SSO)', () => {
    expect(canWriteInterviews(user({ manager_role: 'hr', groups: [KEYCLOAK_GROUP_HR] }))).toBe(false)
  })

  it('возвращает true для менеджера', () => {
    expect(canWriteInterviews(user())).toBe(true)
  })

  it('true при manager_role manager, даже если в группах есть hrs (как hrs + employment-managers)', () => {
    expect(
      canWriteInterviews(
        user({
          manager_role: 'manager',
          groups: [KEYCLOAK_GROUP_HR, KEYCLOAK_GROUP_EMPLOYMENT],
        }),
      ),
    ).toBe(true)
  })

  it('возвращает true для admin по manager_role', () => {
    expect(canWriteInterviews(user({ manager_role: 'admin' }))).toBe(true)
  })

  it('true при группе admin Keycloak, даже если manager_role ещё hr (рассинхрон payload)', () => {
    expect(
      canWriteInterviews(
        user({
          manager_role: 'hr',
          groups: [KEYCLOAK_GROUP_ADMIN, KEYCLOAK_GROUP_HR],
        }),
      ),
    ).toBe(true)
  })

  it('возвращает false для outstaff по manager_role', () => {
    expect(canWriteInterviews(user({ manager_role: 'outstaff', groups: [KEYCLOAK_GROUP_OUTSTAFF] }))).toBe(
      false,
    )
  })

  it('возвращает false для mentor по manager_role', () => {
    expect(canWriteInterviews(user({ manager_role: 'mentor', groups: [KEYCLOAK_GROUP_MENTORS] }))).toBe(
      false,
    )
  })

  it('возвращает false для студента портала (роль student)', () => {
    expect(
      canWriteInterviews(user({ manager_role: 'student', groups: [KEYCLOAK_GROUP_STUDENTS] })),
    ).toBe(false)
  })

  it('возвращает false для роли no_access', () => {
    expect(canWriteInterviews(user({ manager_role: KEYCLOAK_ROLE_NO_ACCESS, groups: [] }))).toBe(false)
  })
})

describe('isPureStudentPortalUser', () => {
  it('true при группе students без менеджерских групп', () => {
    expect(isPureStudentPortalUser(user({ groups: [KEYCLOAK_GROUP_STUDENTS], manager_role: 'student' }))).toBe(
      true,
    )
  })

  it('true при manager_role student (группы могут прийти позже)', () => {
    expect(isPureStudentPortalUser(user({ manager_role: 'student', groups: [] }))).toBe(true)
  })

  it('false при employment-managers', () => {
    expect(
      isPureStudentPortalUser(
        user({ groups: [KEYCLOAK_GROUP_STUDENTS, KEYCLOAK_GROUP_EMPLOYMENT], manager_role: 'manager' }),
      ),
    ).toBe(false)
  })

  it('false при manager_role no_access', () => {
    expect(isPureStudentPortalUser(user({ manager_role: KEYCLOAK_ROLE_NO_ACCESS, groups: [] }))).toBe(false)
  })
})

describe('isHrOrOutstaffUser', () => {
  it('false для null', () => {
    expect(isHrOrOutstaffUser(null)).toBe(false)
  })

  it('true при группе hrs', () => {
    expect(isHrOrOutstaffUser(user({ groups: [KEYCLOAK_GROUP_HR] }))).toBe(true)
  })

  it('true при группе outstaff', () => {
    expect(isHrOrOutstaffUser(user({ groups: [KEYCLOAK_GROUP_OUTSTAFF] }))).toBe(true)
  })

  it('true при manager_role hr', () => {
    expect(isHrOrOutstaffUser(user({ manager_role: 'hr', groups: [] }))).toBe(true)
  })

  it('true при группе mentors', () => {
    expect(isHrOrOutstaffUser(user({ manager_role: 'mentor', groups: [KEYCLOAK_GROUP_MENTORS] }))).toBe(true)
  })

  it('false для админа с группой hrs (двойное членство — не режим только HR)', () => {
    expect(
      isHrOrOutstaffUser(
        user({
          manager_role: 'admin',
          groups: [KEYCLOAK_GROUP_HR],
        }),
      ),
    ).toBe(false)
  })

  it('false при группе admin и hrs, даже если manager_role hr в payload', () => {
    expect(
      isHrOrOutstaffUser(
        user({
          manager_role: 'hr',
          groups: [KEYCLOAK_GROUP_ADMIN, KEYCLOAK_GROUP_HR],
        }),
      ),
    ).toBe(false)
  })
})

describe('isMentorUser', () => {
  it('false для null', () => {
    expect(isMentorUser(null)).toBe(false)
  })

  it('true при manager_role mentor', () => {
    expect(isMentorUser(user({ manager_role: 'mentor', groups: [KEYCLOAK_GROUP_MENTORS] }))).toBe(true)
  })

  it('false для админа', () => {
    expect(
      isMentorUser(user({ manager_role: 'admin', groups: [KEYCLOAK_GROUP_ADMIN, KEYCLOAK_GROUP_MENTORS] })),
    ).toBe(false)
  })
})

describe('emailsEqualIgnoreCase', () => {
  it('игнорирует регистр и пробелы по краям', () => {
    expect(emailsEqualIgnoreCase('A@B.C', 'a@b.c')).toBe(true)
    expect(emailsEqualIgnoreCase('  x@y.z  ', 'x@y.z')).toBe(true)
  })

  it('false при пустых значениях', () => {
    expect(emailsEqualIgnoreCase('', 'a@b.c')).toBe(false)
    expect(emailsEqualIgnoreCase('a@b.c', undefined)).toBe(false)
  })
})

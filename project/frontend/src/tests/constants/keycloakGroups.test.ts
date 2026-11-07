import { describe, expect, it } from 'vitest'

import {
  KEYCLOAK_GROUP_CV,
  KEYCLOAK_GROUP_EDUCATION,
  KEYCLOAK_GROUP_EMPLOYMENT,
  KEYCLOAK_GROUP_HR,
  KEYCLOAK_GROUP_MENTORS,
  KEYCLOAK_GROUP_OUTSTAFF,
  KEYCLOAK_GROUP_STUDENTS,
  KEYCLOAK_MANAGER_GROUPS,
} from '../../constants/keycloakGroups'
import {
  KEYCLOAK_GROUP_ADMIN,
  KEYCLOAK_ROLE_MENTOR,
  KEYCLOAK_ROLE_NO_ACCESS,
} from '../../constants/keycloakRoles'

describe('keycloakGroups', () => {
  it('менеджерские группы входят в Set', () => {
    expect(KEYCLOAK_MANAGER_GROUPS.has(KEYCLOAK_GROUP_EMPLOYMENT)).toBe(true)
    expect(KEYCLOAK_MANAGER_GROUPS.has(KEYCLOAK_GROUP_CV)).toBe(true)
    expect(KEYCLOAK_MANAGER_GROUPS.has(KEYCLOAK_GROUP_EDUCATION)).toBe(true)
    expect(KEYCLOAK_MANAGER_GROUPS.has(KEYCLOAK_GROUP_HR)).toBe(false)
  })

  it('строковые константы групп не пустые', () => {
    expect(KEYCLOAK_GROUP_STUDENTS).toBe('students')
    expect(KEYCLOAK_GROUP_OUTSTAFF).toBe('outstaff')
    expect(KEYCLOAK_GROUP_MENTORS).toBe('mentors')
  })
})

describe('keycloakRoles', () => {
  it('роли синхронизированы с бэкенд-именами', () => {
    expect(KEYCLOAK_GROUP_ADMIN).toBe('role_admin')
    expect(KEYCLOAK_ROLE_NO_ACCESS).toBe('no_access')
    expect(KEYCLOAK_ROLE_MENTOR).toBe('mentor')
  })
})

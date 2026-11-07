import { KEYCLOAK_GROUP_ADMIN, KEYCLOAK_ROLE_NO_ACCESS } from '../constants/keycloakRoles'
import {
  KEYCLOAK_GROUP_HR,
  KEYCLOAK_GROUP_MENTORS,
  KEYCLOAK_GROUP_OUTSTAFF,
  KEYCLOAK_GROUP_STUDENTS,
  KEYCLOAK_MANAGER_GROUPS,
} from '../constants/keycloakGroups'
import type { AuthUser } from '../store/authStore'

/** Полные права на CRUD собеседований (создание/редактирование) — только admin в API. */
export function isAdminUser(user: AuthUser | null): boolean {
  if (!user) {
    return false
  }
  if (user.manager_role === 'admin') {
    return true
  }
  return user.groups.includes(KEYCLOAK_GROUP_ADMIN)
}

/**
 * Полные права на создание/редактирование собеседований в UI.
 * Согласовано с core.context_processors.can_write: только admin и manager;
 * hr и outstaff — только просмотр (по manager_role из сессии, а не только по группам).
 * Администратор по группе role_admin (как в isAdminUser) всегда может писать, даже если
 * manager_role в payload ещё hr/outstaff из-за устаревшей сессии или двойного членства.
 */
export function canWriteInterviews(user: AuthUser | null): boolean {
  if (!user) {
    return false
  }
  if (isAdminUser(user)) {
    return true
  }
  if (
    user.manager_role === 'hr' ||
    user.manager_role === 'outstaff' ||
    user.manager_role === 'mentor' ||
    user.manager_role === 'student' ||
    user.manager_role === KEYCLOAK_ROLE_NO_ACCESS
  ) {
    return false
  }
  return user.manager_role === 'admin' || user.manager_role === 'manager'
}

/** Роль HR, outstaff или mentor — read-only просмотр (колонка транскрибации без редактирования). */
export function isHrOrOutstaffUser(user: AuthUser | null): boolean {
  if (!user) {
    return false
  }
  if (isAdminUser(user)) {
    return false
  }
  return (
    user.groups.includes(KEYCLOAK_GROUP_HR) ||
    user.groups.includes(KEYCLOAK_GROUP_OUTSTAFF) ||
    user.groups.includes(KEYCLOAK_GROUP_MENTORS) ||
    user.manager_role === 'hr' ||
    user.manager_role === 'outstaff' ||
    user.manager_role === 'mentor'
  )
}

/** Пользователь с ролью mentor (только «База собеседований»). */
export function isMentorUser(user: AuthUser | null): boolean {
  if (!user) {
    return false
  }
  if (isAdminUser(user)) {
    return false
  }
  return user.manager_role === 'mentor' || user.groups.includes(KEYCLOAK_GROUP_MENTORS)
}

/**
 * Только портал студента: группа students, без админа и без менеджерских групп.
 * Согласовано с InternPortalRequiredMixin / IsInternPortalStudent.
 */
export function isPureStudentPortalUser(user: AuthUser | null): boolean {
  if (!user) {
    return false
  }
  if (user.manager_role === KEYCLOAK_ROLE_NO_ACCESS) {
    return false
  }
  const hasStudentClaim =
    user.groups.includes(KEYCLOAK_GROUP_STUDENTS) || user.manager_role === 'student'
  if (!hasStudentClaim) {
    return false
  }
  if (isAdminUser(user)) {
    return false
  }
  return !user.groups.some((g) => KEYCLOAK_MANAGER_GROUPS.has(g))
}

/** Сравнение email для UI и API без учёта регистра. */
export function emailsEqualIgnoreCase(
  a: string | null | undefined,
  b: string | null | undefined,
): boolean {
  if (!a || !b) {
    return false
  }
  return a.trim().toLowerCase() === b.trim().toLowerCase()
}

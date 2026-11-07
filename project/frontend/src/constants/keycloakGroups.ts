/** Синхрон с core.constants KEYCLOAK_GROUP_STUDENTS */
export const KEYCLOAK_GROUP_STUDENTS = 'students'

/** Синхрон с core.constants KEYCLOAK_GROUP_HR — только просмотр, без записи */
export const KEYCLOAK_GROUP_HR = 'hrs'

/** Синхрон с core.constants KEYCLOAK_GROUP_OUTSTAFF */
export const KEYCLOAK_GROUP_OUTSTAFF = 'outstaff'

/** Синхрон с core.constants KEYCLOAK_GROUP_MENTORS */
export const KEYCLOAK_GROUP_MENTORS = 'mentors'

/** Синхрон с core.constants KEYCLOAK_MANAGER_GROUPS (менеджерские группы) */
export const KEYCLOAK_GROUP_EMPLOYMENT = 'employment-managers'
export const KEYCLOAK_GROUP_CV = 'cv-managers'
export const KEYCLOAK_GROUP_EDUCATION = 'education'

export const KEYCLOAK_MANAGER_GROUPS: ReadonlySet<string> = new Set([
  KEYCLOAK_GROUP_EMPLOYMENT,
  KEYCLOAK_GROUP_CV,
  KEYCLOAK_GROUP_EDUCATION,
])

export const SAD_INTERN_STATUS = {
  rejected: 'rejected',
  accepted: 'accepted',
  offered: 'offered',
  fired: 'fired',
  on_project: 'on_project',
} as const

/** Подписи для селектов и фильтров (как в модели). */
export const SAD_INTERN_STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: SAD_INTERN_STATUS.rejected, label: 'Отказ' },
  { value: SAD_INTERN_STATUS.accepted, label: 'Взяли' },
  { value: SAD_INTERN_STATUS.offered, label: 'Предложили' },
  { value: SAD_INTERN_STATUS.fired, label: 'Уволили' },
  { value: SAD_INTERN_STATUS.on_project, label: 'Вышел на проект' },
]

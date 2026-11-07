import type { ManagersObservations } from '../../types/managerDashboard'

function formatNumber(num: number | null | undefined, decimals: number): string {
  if (num === null || num === undefined || Number.isNaN(num)) {
    return '—'
  }
  return num.toFixed(decimals)
}

function formatPercent(num: number | null | undefined, decimals: number): string {
  if (num === null || num === undefined || Number.isNaN(num)) {
    return '—'
  }
  return `${(num * 100).toFixed(decimals)}%`
}

/**
 * Тексты наблюдений.
 */
export function buildManagersObservationLines(data: ManagersObservations): string[] {
  const {
    list,
    totalManagers,
    totalCandidates,
    totalInterviews,
    fastest,
    slowest,
    successSorted,
    busiest,
    biggestPortfolio,
    upcomingChamp,
    cancelledChamp,
    noSuccessYet,
  } = data

  if (totalManagers === 0) {
    return []
  }

  return [
    `1. В работе ${totalManagers} менеджеров и ${totalCandidates} кандидатов (в среднем ${formatNumber(totalCandidates / totalManagers, 2)} на менеджера).`,
    `2. Общее число интервью — ${totalInterviews}, среднее на менеджера — ${formatNumber(totalInterviews / totalManagers, 2)}.`,
    fastest
      ? `3. Самый быстрый по найму — ${fastest.manager} (≈ ${Math.round(fastest.avgSpeed ?? 0)} дн. до успеха).`
      : '3. Пока нет завершённых наймов для оценки скорости.',
    slowest
      ? `4. Требует дополнительной поддержки: ${slowest.manager}, среднее время до успеха ${Math.round(slowest.avgSpeed ?? 0)} дн.`
      : '4. Все менеджеры работают без завершённых кейсов.',
    successSorted[0]
      ? `5. Лучший по конверсии — ${successSorted[0].manager} (${formatPercent(successSorted[0].successRate, 1)} успешных кандидатов).`
      : '5. Данных по конверсии ещё нет.',
    successSorted[successSorted.length - 1]
      ? `6. Минимальная конверсия сейчас у ${successSorted[successSorted.length - 1].manager} (${formatPercent(successSorted[successSorted.length - 1].successRate, 1)}).`
      : '6. Все менеджеры имеют одинаковую конверсию.',
    busiest
      ? `7. По количеству интервью лидирует ${busiest.manager} (${busiest.interviews}).`
      : '7. Нет лидеров по количеству интервью.',
    biggestPortfolio
      ? `8. Самый большой портфель кандидатов — у ${biggestPortfolio.manager} (${biggestPortfolio.candidates}).`
      : '8. Все портфели одинаковые.',
    upcomingChamp
      ? `9. Больше всего предстоящих встреч у ${upcomingChamp.manager} (${upcomingChamp.upcoming}).`
      : '9. Предстоящих интервью нет.',
    cancelledChamp
      ? `10. Больше отмен у ${cancelledChamp.manager} (${cancelledChamp.cancelled}) — стоит проверить причины.`
      : '10. Отмен пока не зафиксировано.',
    `11. Менеджеров без успешных кейсов: ${noSuccessYet.length}.`,
    `12. Направлений на менеджера: в среднем ${formatNumber(list.reduce((acc, item) => acc + item.directions, 0) / totalManagers, 2)}.`,
    `13. ${list.filter((item) => item.avgSpeed !== null).length} менеджеров уже довели кандидатов до оффера.`,
    `14. ${list.filter((item) => item.upcoming > 0).length} менеджеров имеют в календаре будущие интервью.`,
    `15. ${list.filter((item) => item.week_count > 0).length} менеджеров задействованы в текущей неделе.`,
    `16. Средний процент отмен по команде — ${formatPercent(totalInterviews ? list.reduce((acc, item) => acc + item.cancelled, 0) / totalInterviews : 0, 1)}.`,
    `17. ${list.filter((item) => item.successRate >= 0.5).length} менеджеров имеют конверсию 50% и выше.`,
    `18. ${list.filter((item) => item.candidates >= 5).length} менеджеров ведут 5+ кандидатов одновременно.`,
    `19. ${list.filter((item) => item.interviews >= 20).length} менеджеров уже провели 20+ интервью.`,
    `20. ${list.filter((item) => item.avgSpeed !== null && item.avgSpeed <= 14).length} менеджеров укладываются в две недели до оффера.`,
  ]
}

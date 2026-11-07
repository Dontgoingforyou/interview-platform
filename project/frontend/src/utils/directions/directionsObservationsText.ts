import type { DirectionObservationsResponse } from '../../types/direction'

function formatNumber(num: number, decimals: number): string {
  if (Number.isNaN(num)) {
    return '—'
  }
  return num.toFixed(decimals)
}

function formatPercent(num: number, decimals: number): string {
  if (Number.isNaN(num)) {
    return '—'
  }
  return `${(num * 100).toFixed(decimals)}%`
}

/**
 * Тексты наблюдений по направлениям.
 */
export function buildDirectionObservationsLines(data: DirectionObservationsResponse): string[] {
  const {
    list,
    totalDirections,
    totalInterviews,
    fastest,
    slowest,
    mostManagers,
    highestUpcoming,
    bestConversion,
    worstConversion,
    focusNeeded,
    bestMonth,
    worstMonth,
    highestCancel,
  } = data

  if (totalDirections === 0) {
    return []
  }

  const insights: string[] = [
    `1. ${totalDirections} направлений охватывают ${totalInterviews} собеседований (в среднем ${formatNumber(totalInterviews / totalDirections, 2)} на направление).`,
    bestConversion &&
      bestConversion.direction &&
      typeof bestConversion.successRate === 'number' &&
      !Number.isNaN(bestConversion.successRate)
      ? `2. Лучший коэффициент у направления ${bestConversion.direction} — ${formatPercent(bestConversion.successRate, 1)}.`
      : '2. Нет направлений с устойчивой конверсией (мало данных).',
    worstConversion &&
      worstConversion.direction &&
      typeof worstConversion.successRate === 'number' &&
      !Number.isNaN(worstConversion.successRate)
      ? `3. Направление ${worstConversion.direction} показывает наименьшую конверсию — ${formatPercent(worstConversion.successRate, 1)}.`
      : '3. Все направления имеют одинаковую конверсию.',
    fastest &&
      fastest.direction &&
      typeof fastest.avgSpeed === 'number' &&
      !Number.isNaN(fastest.avgSpeed)
      ? `4. Быстрее всего проводится найм в ${fastest.direction}: ≈ ${Math.round(fastest.avgSpeed)} дн. до успеха.`
      : '4. Скорость закрытия пока не измерима.',
    slowest &&
      slowest.direction &&
      typeof slowest.avgSpeed === 'number' &&
      !Number.isNaN(slowest.avgSpeed)
      ? `5. Самый длинный цикл у ${slowest.direction}: ≈ ${Math.round(slowest.avgSpeed)} дн.`
      : '5. Все направления закрываются с одинаковой скоростью.',
    mostManagers && mostManagers.direction
      ? `6. ${mostManagers.direction} задействует максимальное число менеджеров (${mostManagers.managers}).`
      : '6. Везде работает по одному менеджеру.',
    highestUpcoming && highestUpcoming.direction
      ? `7. По количеству будущих интервью лидирует ${highestUpcoming.direction} (${highestUpcoming.upcoming}).`
      : '7. Нет предстоящих интервью.',
    highestCancel &&
      highestCancel.direction &&
      typeof highestCancel.cancelRate === 'number' &&
      !Number.isNaN(highestCancel.cancelRate)
      ? `8. Самое большое число отмен у направления ${highestCancel.direction} (${formatPercent(highestCancel.cancelRate, 1)}).`
      : '8. Пока отмены не фиксируются.',
    `9. Направлений с конверсией ниже 20% — ${focusNeeded}; стоит усилить работу.`,
    bestMonth
      ? `10. Пиковый месяц активности — ${bestMonth[0]} (${bestMonth[1]} интервью).`
      : '10. Месячная активность распределена равномерно.',
    worstMonth
      ? `11. Наименьшая активность была в ${worstMonth[0]} (${worstMonth[1]} интервью).`
      : '11. Нет месяцев с провалами.',
    `12. ${list.filter((item) => item.interviews >= 50).length} направлений уже набрали 50+ интервью.`,
    `13. ${list.filter((item) => item.successRate >= 0.5).length} направлений имеют конверсию 50% и выше.`,
    `14. ${list.filter((item) => item.avgSpeed !== null && typeof item.avgSpeed === 'number' && !Number.isNaN(item.avgSpeed) && item.avgSpeed <= 14).length} направлений закрывают кандидатов ≤ 14 дней.`,
    `15. ${list.filter((item) => item.cancelRate <= 0.1).length} направлений практически без отмен (≤10%).`,
    `16. ${list.filter((item) => item.upcoming > 0).length} направлений имеют собеседования в календаре.`,
    `17. ${list.filter((item) => item.managers >= 3).length} направлений ведут три и более менеджера.`,
    `18. ${list.filter((item) => item.candidates >= 20).length} направлений охватывают ≥ 20 кандидатов.`,
    `19. ${list.filter((item) => item.interviews <= 5).length} направлений с низкой активностью (≤5 интервью).`,
    `20. Доля технических направлений составляет ${formatPercent(
      list
        .filter(
          (item) =>
            item.direction.toLowerCase().includes('tech') || item.direction.toLowerCase().includes('тех'),
        )
        .reduce((acc, item) => acc + item.interviews, 0) / (totalInterviews || 1),
      1,
    )}.`,
  ]

  return insights
}

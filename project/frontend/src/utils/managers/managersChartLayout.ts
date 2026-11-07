/** Общая высота области графиков в ряду «Топ интервью» / «Сводка активности» */

export const MANAGERS_INTERVIEWS_CHART_TOP_N = 10
export const MANAGERS_CHART_ROW_PX = 34
export const MANAGERS_CHART_MIN_PLOT_H = 280
export const MANAGERS_CHART_VERTICAL_EXTRA = 48

export function computeManagersInterviewsChartPlotHeight(rowsCount: number): number {
  const n = Math.min(MANAGERS_INTERVIEWS_CHART_TOP_N, Math.max(0, rowsCount))
  return Math.max(MANAGERS_CHART_MIN_PLOT_H, n * MANAGERS_CHART_ROW_PX + MANAGERS_CHART_VERTICAL_EXTRA)
}

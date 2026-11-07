import { useMemo } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Rectangle,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { useThemeStore } from '../../../store/themeStore'
import type { ManagersDashboardTableRow } from '../../../types/managerDashboard'
import { readManagerChartColors } from '../../../utils/managers/managerChartColors'
import { MANAGERS_CHART_MIN_PLOT_H } from '../../../utils/managers/managersChartLayout'
import {
  managersRechartsTooltipContentStyle,
  managersRechartsTooltipCursor,
  managersRechartsTooltipItemStyle,
  managersRechartsTooltipLabelStyle,
  managersRechartsTooltipWrapperStyle,
} from '../../../utils/managers/rechartsManagersTheme'
import ManagersChartCollapsibleBlock from './ManagersChartCollapsibleBlock'

interface TeamActivityDatum {
  name: string
  value: number
  fill: string
}

interface ManagersTeamActivityBarChartProps {
  rows: ManagersDashboardTableRow[]
  /** Совпадает с высотой графика «Топ менеджеров по интервью» */
  plotHeight?: number
}

/**
 * Суммарные уникальные кандидаты по уровням активности (команда).
 * Соответствует логике «горячие / в работе / в портфеле» на странице.
 */
function ManagersTeamActivityBarChart({ rows, plotHeight }: ManagersTeamActivityBarChartProps) {
  const theme = useThemeStore((s) => s.theme)
  const colors = useMemo(() => {
    void theme
    return readManagerChartColors()
  }, [theme])

  const data = useMemo((): TeamActivityDatum[] => {
    const hot = rows.reduce((s, r) => s + r.hot_candidates_count, 0)
    const active = rows.reduce((s, r) => s + r.active_candidates_count, 0)
    const portfolio = rows.reduce((s, r) => s + r.portfolio_candidates_count, 0)
    return [
      { name: 'Горячие (7 дн.)', value: hot, fill: colors.hot },
      { name: 'В работе (20 дн.)', value: active, fill: colors.active },
      { name: 'В портфеле (60 дн.)', value: portfolio, fill: colors.portfolio },
    ]
  }, [rows, colors.hot, colors.active, colors.portfolio])

  const total = data.reduce((s, d) => s + d.value, 0)
  const chartHeight = plotHeight ?? MANAGERS_CHART_MIN_PLOT_H

  return (
    <ManagersChartCollapsibleBlock title="Сводка активности кандидатов (команда)" panelId="team-activity">
      {total === 0 ? (
        <p className="managers-chart-empty muted">Нет данных для сводки активности.</p>
      ) : (
        <div
          className="managers-chart-wrap"
          style={{ minHeight: chartHeight }}
          role="img"
          aria-label="Столбчатая диаграмма: горячие, в работе, в портфеле"
        >
          <ResponsiveContainer width="100%" height={chartHeight}>
            <BarChart data={data} margin={{ left: 6, right: 10, top: 6, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" className="recharts-cartesian-grid-stroke" />
              <XAxis
                dataKey="name"
                tick={{ fill: 'var(--text-secondary)', fontSize: 10 }}
                interval={0}
                angle={-16}
                textAnchor="end"
                height={34}
                tickMargin={2}
              />
              <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} allowDecimals={false} />
              <Tooltip
                cursor={managersRechartsTooltipCursor}
                formatter={(value: number | string) => [value, 'Кандидатов']}
                contentStyle={managersRechartsTooltipContentStyle}
                labelStyle={managersRechartsTooltipLabelStyle}
                itemStyle={managersRechartsTooltipItemStyle}
                wrapperStyle={managersRechartsTooltipWrapperStyle}
              />
              <Bar
                dataKey="value"
                name="Кандидатов"
                radius={[4, 4, 0, 0]}
                activeBar={(props: unknown) => {
                  const p = props as Record<string, unknown> & { payload?: TeamActivityDatum }
                  const fromShape = typeof p.fill === 'string' ? p.fill : null
                  const c = fromShape ?? p.payload?.fill ?? colors.active
                  return (
                    <Rectangle
                      {...p}
                      fill={c}
                      fillOpacity={0.92}
                      stroke="var(--accent-primary)"
                      strokeWidth={2}
                      radius={[4, 4, 0, 0]}
                    />
                  )
                }}
              >
                {data.map((entry) => (
                  <Cell key={entry.name} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </ManagersChartCollapsibleBlock>
  )
}

export default ManagersTeamActivityBarChart

import { useId, useMemo } from 'react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import ManagersChartCollapsibleBlock from '../../managers/charts/ManagersChartCollapsibleBlock'
import { useThemeStore } from '../../../store/themeStore'
import type { DirectionMetricsResponse } from '../../../types/direction'
import { readManagerChartColors } from '../../../utils/managers/managerChartColors'
import {
  managersRechartsTooltipContentStyle,
  managersRechartsTooltipCursor,
  managersRechartsTooltipItemStyle,
  managersRechartsTooltipLabelStyle,
  managersRechartsTooltipWrapperStyle,
} from '../../../utils/managers/rechartsManagersTheme'

const DEFAULT_MONTH_CHART_HEIGHT = 420

interface DirectionInterviewsByMonthChartProps {
  analytics: DirectionMetricsResponse
  plotHeight?: number
}

/** График собеседований по месяцам за последний год. */
function DirectionInterviewsByMonthChart({
  analytics,
  plotHeight: plotHeightProp,
}: DirectionInterviewsByMonthChartProps) {
  const theme = useThemeStore((s) => s.theme)
  const gradientId = useId().replace(/:/g, '')
  const { labels, data } = analytics.chart_months ?? { labels: [], data: [] }
  const chartData = labels.map((name, i) => ({ name, value: data[i] ?? 0 }))

  const colors = useMemo(() => {
    void theme
    return readManagerChartColors()
  }, [theme])

  const chartHeight = plotHeightProp ?? DEFAULT_MONTH_CHART_HEIGHT

  return (
    <ManagersChartCollapsibleBlock
      title="Собеседования по месяцам (последний год)"
      panelId="directions-by-month"
    >
      {chartData.length === 0 ? (
        <p className="managers-chart-empty muted">Нет данных для графика.</p>
      ) : (
        <div
          className="managers-chart-wrap"
          style={{ minHeight: chartHeight }}
          role="img"
          aria-label="Диаграмма: собеседования по месяцам"
        >
          <ResponsiveContainer width="100%" height={chartHeight}>
            <AreaChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
              <defs>
                <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={colors.primary} stopOpacity={0.38} />
                  <stop offset="100%" stopColor={colors.primary} stopOpacity={0.04} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="recharts-cartesian-grid-stroke" />
              <XAxis
                dataKey="name"
                tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
                interval={0}
                angle={-40}
                textAnchor="end"
                height={90}
              />
              <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} allowDecimals={false} />
              <Tooltip
                cursor={managersRechartsTooltipCursor}
                formatter={(v: number) => [v, 'Интервью']}
                labelFormatter={(l) => String(l)}
                contentStyle={managersRechartsTooltipContentStyle}
                labelStyle={managersRechartsTooltipLabelStyle}
                itemStyle={managersRechartsTooltipItemStyle}
                wrapperStyle={managersRechartsTooltipWrapperStyle}
              />
              <Area
                type="monotone"
                dataKey="value"
                name="Интервью"
                stroke={colors.primary}
                strokeWidth={2}
                fill={`url(#${gradientId})`}
                dot={{ r: 4, fill: colors.primary }}
                activeDot={{ r: 6 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </ManagersChartCollapsibleBlock>
  )
}

export default DirectionInterviewsByMonthChart

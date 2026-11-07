import { useMemo } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Rectangle,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import ManagersChartCollapsibleBlock from '../../managers/charts/ManagersChartCollapsibleBlock'
import { useThemeStore } from '../../../store/themeStore'
import type { DirectionMetricsResponse } from '../../../types/direction'
import { readManagerChartColors } from '../../../utils/managers/managerChartColors'
import { computeManagersInterviewsChartPlotHeight } from '../../../utils/managers/managersChartLayout'
import {
  managersRechartsTooltipContentStyle,
  managersRechartsTooltipCursor,
  managersRechartsTooltipItemStyle,
  managersRechartsTooltipLabelStyle,
  managersRechartsTooltipWrapperStyle,
} from '../../../utils/managers/rechartsManagersTheme'

interface DirectionBarDatum {
  name: string
  fullName: string
  value: number
}

interface DirectionInterviewsByDirectionChartProps {
  analytics: DirectionMetricsResponse
  /** Общая высота области графика в паре с графиком по месяцам. */
  plotHeight?: number
}

/** Горизонтальные столбцы: собеседования по направлениям за 30 дней. */
function DirectionInterviewsByDirectionChart({
  analytics,
  plotHeight: plotHeightProp,
}: DirectionInterviewsByDirectionChartProps) {
  const theme = useThemeStore((s) => s.theme)
  const { labels, data } = analytics.chart_directions ?? { labels: [], data: [] }

  const chartData = useMemo((): DirectionBarDatum[] => {
    return labels.map((rawName, i) => {
      const name = rawName.length > 24 ? `${rawName.slice(0, 22)}…` : rawName
      return { name, fullName: rawName, value: data[i] ?? 0 }
    })
  }, [labels, data])

  const fill = useMemo(() => {
    void theme
    return readManagerChartColors().primary
  }, [theme])

  const chartHeight =
    plotHeightProp ?? computeManagersInterviewsChartPlotHeight(chartData.length)

  return (
    <ManagersChartCollapsibleBlock
      title="Собеседования по направлениям (последние 30 дней)"
      panelId="directions-by-direction"
    >
      {chartData.length === 0 ? (
        <p className="managers-chart-empty muted">Нет данных для графика.</p>
      ) : (
        <div
          className="managers-chart-wrap"
          style={{ minHeight: chartHeight }}
          role="img"
          aria-label="Столбчатая диаграмма: собеседования по направлениям"
        >
          <ResponsiveContainer width="100%" height={chartHeight}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" className="recharts-cartesian-grid-stroke" />
              <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="name"
                width={168}
                tick={{ fill: 'var(--text-primary)', fontSize: 10 }}
                interval={0}
              />
              <Tooltip
                cursor={managersRechartsTooltipCursor}
                formatter={(v: number | string) => [`${v} шт.`, 'Собеседования']}
                contentStyle={managersRechartsTooltipContentStyle}
                labelStyle={managersRechartsTooltipLabelStyle}
                itemStyle={managersRechartsTooltipItemStyle}
                wrapperStyle={managersRechartsTooltipWrapperStyle}
                labelFormatter={(_, payload) => {
                  const row = payload?.[0]?.payload as DirectionBarDatum | undefined
                  return row?.fullName ?? row?.name ?? ''
                }}
              />
              <Bar
                dataKey="value"
                name="Количество"
                fill={fill}
                radius={[0, 4, 4, 0]}
                activeBar={(props: unknown) => {
                  const p = props as Record<string, unknown>
                  return (
                    <Rectangle
                      {...p}
                      fill={fill}
                      fillOpacity={0.92}
                      stroke="var(--accent-primary)"
                      strokeWidth={2}
                      radius={[0, 4, 4, 0]}
                    />
                  )
                }}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </ManagersChartCollapsibleBlock>
  )
}

export default DirectionInterviewsByDirectionChart

import { useMemo } from 'react'
import { Bar, BarChart, CartesianGrid, Rectangle, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { useThemeStore } from '../../../store/themeStore'
import type { ManagersDashboardTableRow } from '../../../types/managerDashboard'
import { readManagerChartColors } from '../../../utils/managers/managerChartColors'
import {
  computeManagersInterviewsChartPlotHeight,
  MANAGERS_INTERVIEWS_CHART_TOP_N,
} from '../../../utils/managers/managersChartLayout'
import {
  managersRechartsTooltipContentStyle,
  managersRechartsTooltipCursor,
  managersRechartsTooltipItemStyle,
  managersRechartsTooltipLabelStyle,
  managersRechartsTooltipWrapperStyle,
} from '../../../utils/managers/rechartsManagersTheme'
import { useMediaQuery } from '../../../hooks/useMediaQuery'
import ManagersChartCollapsibleBlock from './ManagersChartCollapsibleBlock'

interface ManagersInterviewsBarChartProps {
  rows: ManagersDashboardTableRow[]
  /** Общая высота области графика в паре с «Сводкой активности» */
  plotHeight?: number
}

interface InterviewBarDatum {
  name: string
  fullName: string
  interviews: number
}

/** Топ менеджеров по числу интервью */
function ManagersInterviewsBarChart({ rows, plotHeight: plotHeightProp }: ManagersInterviewsBarChartProps) {
  const theme = useThemeStore((s) => s.theme)
  const isMobile = useMediaQuery('(max-width: 600px)')
  const fill = useMemo(() => {
    void theme
    return readManagerChartColors().primary
  }, [theme])

  const data = useMemo((): InterviewBarDatum[] => {
    return [...rows]
      .sort((a, b) => b.interviews_count - a.interviews_count)
      .slice(0, MANAGERS_INTERVIEWS_CHART_TOP_N)
      .map((r) => {
        const raw = r.full_name || r.email
        const name = raw.length > 24 ? `${raw.slice(0, 22)}…` : raw
        return { name, fullName: raw, interviews: r.interviews_count }
      })
  }, [rows])

  const chartHeight =
    plotHeightProp ?? computeManagersInterviewsChartPlotHeight(rows.length)

  return (
    <ManagersChartCollapsibleBlock title="Топ менеджеров по числу интервью" panelId="interviews">
      {data.length === 0 ? (
        <p className="managers-chart-empty muted">Нет данных для графика по интервью.</p>
      ) : (
        <div
          className="managers-chart-wrap"
          style={{ minHeight: chartHeight }}
          role="img"
          aria-label="Столбчатая диаграмма: интервью по менеджерам"
        >
          <ResponsiveContainer width="100%" height={chartHeight}>
            <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" className="recharts-cartesian-grid-stroke" />
              <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} />
              <YAxis
                type="category"
                dataKey="name"
                width={isMobile ? 100 : 168}
                tick={{ fill: 'var(--text-primary)', fontSize: 10 }}
                interval={0}
              />
              <Tooltip
                cursor={managersRechartsTooltipCursor}
                formatter={(value: number | string) => [value, 'Интервью']}
                contentStyle={managersRechartsTooltipContentStyle}
                labelStyle={managersRechartsTooltipLabelStyle}
                itemStyle={managersRechartsTooltipItemStyle}
                wrapperStyle={managersRechartsTooltipWrapperStyle}
                labelFormatter={(_, payload) => {
                  const row = payload?.[0]?.payload as InterviewBarDatum | undefined
                  return row?.fullName ?? row?.name ?? ''
                }}
              />
              <Bar
                dataKey="interviews"
                name="Интервью"
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

export default ManagersInterviewsBarChart

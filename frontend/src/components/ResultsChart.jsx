import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useCurrency } from '../context/CurrencyContext'
import { formatMonth } from '../lib/format'

// Chart-only tokens. --accent (#2d9596) is tuned for buttons and reads slightly
// gray as a large data fill, so marks use the same teal stepped up in chroma.
// Grid and axis text stay one step off the surface so the data is the only
// thing that's loud.
const MARK = '#0d9488'
const GRID = '#e5e3dd'
const AXIS_TEXT = '#6b7280'
const SURFACE = '#ffffff'

// Both charts plot a single series, so there is no legend: the card heading
// already says what is being measured, and a one-swatch legend box would just
// restate it.

function ChartTooltip({ active, payload, label, labelFormatter, money }) {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-label">
        {labelFormatter ? labelFormatter(label) : label}
      </div>
      <div className="chart-tooltip-value">{money(payload[0].value)}</div>
    </div>
  )
}

export default function ResultsChart({ result }) {
  const { summary, by_category, monthly_spending, rows_dropped } = result
  // Amounts are stored in USD; conversion happens here at render time only.
  const { money, moneyCompact } = useCurrency()

  // Horizontal bars: category names are words, and laying them along the y-axis
  // keeps them readable without rotating the labels.
  const barHeight = Math.max(by_category.length * 44, 160)

  return (
    <>
      <div className="card">
        <h2>Summary</h2>
        <p className="card-subtitle">
          {summary.date_range.start} to {summary.date_range.end} ·{' '}
          {summary.months_covered} month{summary.months_covered === 1 ? '' : 's'}
        </p>

        <div className="stat-grid">
          <div className="stat">
            <div className="stat-label">Total spend</div>
            <div className="stat-value">{money(summary.total_spend)}</div>
          </div>
          <div className="stat">
            <div className="stat-label">Average / month</div>
            <div className="stat-value">
              {money(summary.average_monthly_spend)}
            </div>
          </div>
          <div className="stat">
            <div className="stat-label">Transactions</div>
            <div className="stat-value">{summary.transaction_count}</div>
          </div>
          <div className="stat">
            <div className="stat-label">Categories</div>
            <div className="stat-value">{summary.category_count}</div>
          </div>
        </div>

        {/* The parser silently drops rows with unparseable dates or amounts.
            Say so, rather than letting totals quietly under-report. */}
        {rows_dropped > 0 && (
          <p className="chart-note">
            {rows_dropped} row{rows_dropped === 1 ? '' : 's'} skipped — bad date,
            amount, or missing category.
          </p>
        )}
      </div>

      <div className="chart-row">
        <div className="card">
          <h2>Spending by category</h2>
          <p className="card-subtitle">Total across the whole period</p>
          <ResponsiveContainer width="100%" height={barHeight}>
            <BarChart
              data={by_category}
              layout="vertical"
              margin={{ top: 4, right: 64, bottom: 4, left: 4 }}
            >
              {/* Solid hairlines, never dashed - Recharts defaults to "3 3". */}
              <CartesianGrid horizontal={false} stroke={GRID} />
              <XAxis
                type="number"
                tickFormatter={moneyCompact}
                stroke={GRID}
                tick={{ fill: AXIS_TEXT, fontSize: 12 }}
              />
              <YAxis
                type="category"
                dataKey="category"
                width={94}
                stroke={GRID}
                tick={{ fill: AXIS_TEXT, fontSize: 12 }}
              />
              <Tooltip
                content={<ChartTooltip money={money} />}
                cursor={{ fill: 'rgba(13, 148, 136, 0.06)' }}
              />
              <Bar
                dataKey="total"
                fill={MARK}
                maxBarSize={24}
                // Recharts mounts its marks through an rAF entrance animation.
                // Off here: the chart re-renders on every poll and on every
                // currency toggle, and replaying a grow-in each time is noise.
                // The deliberate motion in this app lives on the landing page.
                isAnimationActive={false}
                // Rounded data-end, square where it meets the baseline.
                radius={[0, 4, 4, 0]}
              >
                {/* Few enough bars that every tip can carry its value; the
                    axis and tooltip would otherwise do the work. */}
                <LabelList
                  dataKey="total"
                  position="right"
                  formatter={money}
                  style={{ fill: AXIS_TEXT, fontSize: 12 }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2>Spending over time</h2>
          <p className="card-subtitle">Monthly total</p>
          {/* A trend needs at least two points. With one month the chart is a
              lone dot in an empty grid, which reads as broken rather than as
              "not enough data" - so say that instead. */}
          {monthly_spending.length < 2 ? (
            <p className="chart-empty">
              Only one month of data ({formatMonth(monthly_spending[0].month)}).
              Upload a wider date range to see a trend.
            </p>
          ) : (
          <ResponsiveContainer width="100%" height={barHeight}>
            <AreaChart
              data={monthly_spending}
              margin={{ top: 8, right: 16, bottom: 4, left: 4 }}
            >
              <CartesianGrid vertical={false} stroke={GRID} />
              <XAxis
                dataKey="month"
                tickFormatter={formatMonth}
                stroke={GRID}
                tick={{ fill: AXIS_TEXT, fontSize: 12 }}
              />
              <YAxis
                tickFormatter={moneyCompact}
                stroke={GRID}
                tick={{ fill: AXIS_TEXT, fontSize: 12 }}
              />
              <Tooltip
                content={<ChartTooltip labelFormatter={formatMonth} money={money} />}
                cursor={{ stroke: MARK, strokeWidth: 1 }}
              />
              <Area
                // Linear, not a spline: these are discrete monthly buckets, and
                // a smooth curve would imply within-month movement we don't have.
                type="linear"
                dataKey="total"
                stroke={MARK}
                strokeWidth={2}
                // A wash, not a saturated block.
                fill={MARK}
                fillOpacity={0.1}
                // Surface ring keeps the dots legible where they cross the line.
                dot={{ r: 4, fill: MARK, stroke: SURFACE, strokeWidth: 2 }}
                activeDot={{ r: 6, fill: MARK, stroke: SURFACE, strokeWidth: 2 }}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
          )}
        </div>
      </div>
    </>
  )
}

import { motion, useReducedMotion } from 'framer-motion'
import { formatMoney } from '../lib/format'

/**
 * A miniature of the dashboard, shown to signed-out visitors so they can see
 * what the app produces before creating an account.
 *
 * The numbers are real: this is the actual analysis of the sample_transactions.csv
 * in this repo, so nothing here overstates what the app returns.
 *
 * Drawn directly rather than by mounting Recharts. At this size the axes and
 * ticks a real chart carries would be noise, and the bars need to grow in on
 * load as part of the page's entrance - which is exactly the animation that is
 * switched off on the dashboard, where the chart re-renders on every poll.
 */
const CATEGORIES = [
  { category: 'Groceries', total: 951.9 },
  { category: 'Dining', total: 434.0 },
  { category: 'Entertainment', total: 86.94 },
  { category: 'Transport', total: 72.0 },
]
const MONTHLY = [
  { month: 'Jan', total: 483.68 },
  { month: 'Feb', total: 525.9 },
  { month: 'Mar', total: 535.26 },
]
const TOTAL = 1544.84
const MAX = Math.max(...CATEGORIES.map((c) => c.total))

// The sparkline is drawn in a 100x32 box, baseline at the bottom.
const sparkPoints = MONTHLY.map((m, i) => {
  const min = Math.min(...MONTHLY.map((d) => d.total))
  const max = Math.max(...MONTHLY.map((d) => d.total))
  const x = (i / (MONTHLY.length - 1)) * 100
  // Padded so the flattest series still reads as a line, not a rule.
  const y = 28 - ((m.total - min) / (max - min || 1)) * 22
  return [x, y]
})
const sparkPath = sparkPoints.map(([x, y], i) => `${i ? 'L' : 'M'}${x},${y}`).join(' ')

export default function LandingPreview({ delay = 0 }) {
  const reduced = useReducedMotion()

  return (
    <motion.div
      className="card preview-card"
      variants={{
        hidden: { opacity: 0, y: reduced ? 0 : 18 },
        shown: {
          opacity: 1,
          y: 0,
          transition: reduced
            ? { duration: 0.2, delay: 0 }
            : { type: 'spring', stiffness: 240, damping: 28, delay,
                when: 'beforeChildren', staggerChildren: 0.07 },
        },
      }}
    >
      <div className="preview-head">
        <span className="preview-label">Sample analysis</span>
        <span className="preview-total">{formatMoney(TOTAL)}</span>
      </div>

      <ul className="preview-bars">
        {CATEGORIES.map(({ category, total }) => (
          <li key={category}>
            <span className="preview-cat">{category}</span>
            <span className="preview-track">
              <motion.span
                className="preview-bar"
                variants={{
                  hidden: { scaleX: reduced ? total / MAX : 0 },
                  shown: {
                    scaleX: total / MAX,
                    transition: reduced
                      ? { duration: 0 }
                      : { type: 'spring', stiffness: 120, damping: 20 },
                  },
                }}
                // Grow from the baseline, like the real chart's bars.
                style={{ transformOrigin: 'left center' }}
              />
            </span>
            <span className="preview-amount">{formatMoney(total)}</span>
          </li>
        ))}
      </ul>

      <motion.div
        className="preview-trend"
        variants={{
          hidden: { opacity: 0 },
          shown: { opacity: 1, transition: { duration: reduced ? 0.2 : 0.5 } },
        }}
      >
        <svg viewBox="0 0 100 32" preserveAspectRatio="none" aria-hidden="true">
          {/* The line is revealed by sweeping a clip rectangle across it,
              not by animating pathLength. pathLength draws with stroke
              dashes, and this viewBox is scaled non-uniformly
              (preserveAspectRatio="none"), which stretches the dash pattern
              horizontally and shatters the line into visible segments. A
              clip has no such problem. */}
          <defs>
            <clipPath id="spark-reveal" clipPathUnits="userSpaceOnUse">
              <motion.rect
                x="-2"
                y="-4"
                height="40"
                variants={{
                  hidden: { width: reduced ? 104 : 0 },
                  shown: {
                    width: 104,
                    transition: { duration: reduced ? 0 : 0.9, ease: 'easeOut' },
                  },
                }}
              />
            </clipPath>
          </defs>
          <g clipPath="url(#spark-reveal)">
            <path
              d={sparkPath}
              fill="none"
              stroke="var(--accent)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              vectorEffect="non-scaling-stroke"
            />
            {/* No end marker: this viewBox is scaled non-uniformly, which
                turns a circle into a flat ellipse. vectorEffect protects the
                stroke width, not the geometry. The line reads fine alone. */}
          </g>
        </svg>
        <div className="preview-months">
          {MONTHLY.map((m) => <span key={m.month}>{m.month}</span>)}
        </div>
      </motion.div>

      <p className="preview-caption">
        Real output from the sample CSV included in this repo.
      </p>
    </motion.div>
  )
}

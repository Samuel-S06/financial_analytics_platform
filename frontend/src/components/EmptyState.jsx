/**
 * Placeholder shown before anything has been uploaded.
 *
 * The page had a large blank area under the upload card while waiting for
 * input, which reads as broken rather than as empty. This shows the shape of
 * what's coming - a muted skeleton of the breakdown - so the space is clearly
 * reserved rather than missing.
 *
 * Inert by design: no real numbers, nothing that could be mistaken for data.
 */
const SKELETON = [0.9, 0.62, 0.34, 0.2]

export default function EmptyState() {
  return (
    <div className="empty-state" aria-hidden="true">
      <div className="empty-skeleton">
        {SKELETON.map((width, i) => (
          <div className="empty-row" key={i}>
            <span className="empty-label" />
            <span className="empty-track">
              <span className="empty-bar" style={{ width: `${width * 100}%` }} />
            </span>
          </div>
        ))}
      </div>
      <p className="empty-title">Your spending breakdown will appear here</p>
      <p className="empty-body">
        Upload a CSV above to see totals by category, a month-by-month trend,
        and a savings simulation.
      </p>
    </div>
  )
}

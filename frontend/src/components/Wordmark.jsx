/**
 * Spendline wordmark.
 *
 * The mark is three ascending bars - the same shape the spending breakdown
 * draws - so the logo is derived from the product rather than decoration
 * bolted onto it. Geometric on purpose: no illustration, no icon set.
 */
export default function Wordmark() {
  return (
    <div className="brand">
      <svg
        className="brand-mark"
        viewBox="0 0 24 24"
        role="img"
        aria-label="Spendline"
      >
        <rect x="2"  y="14" width="5" height="8"  rx="2" />
        <rect x="9.5" y="9"  width="5" height="13" rx="2" />
        <rect x="17" y="3"  width="5" height="19" rx="2" />
      </svg>
      <span className="brand-name">Spendline</span>
    </div>
  )
}

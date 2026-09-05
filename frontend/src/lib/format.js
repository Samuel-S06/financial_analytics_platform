// Money formatting lives here so the currency toggle has exactly one place to
// hook into. Everything that renders an amount goes through formatMoney.

/**
 * Format an amount that is stored in USD.
 *
 * @param value    the amount, in USD (the currency the CSVs are assumed to be in)
 * @param currency ISO code to display in
 * @param rate     USD -> currency multiplier (1 when displaying USD)
 */
export const formatMoney = (value, currency = 'USD', rate = 1) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(value * rate)

/** Shorter form for axis ticks, where "$1.2K" beats "$1,234.56". */
export const formatMoneyCompact = (value, currency = 'USD', rate = 1) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value * rate)

/** "2024-01" -> "Jan 2024". Recharts gets the raw key; humans get this. */
export const formatMonth = (period) => {
  const [year, month] = period.split('-')
  const date = new Date(Number(year), Number(month) - 1)
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}

import { useCurrency } from '../context/CurrencyContext'

/**
 * Switches the display currency. Conversion is presentational only - the
 * uploaded data and every analysis stay in USD.
 */
export default function CurrencyPicker() {
  const { currency, setCurrency, currencies, asOf, stale, error } = useCurrency()

  if (error) {
    return <span className="currency-note" title={error}>USD</span>
  }

  return (
    <label className="currency-picker">
      <span className="visually-hidden">Display currency</span>
      <select
        value={currency}
        onChange={(e) => setCurrency(e.target.value)}
        aria-label="Display currency"
      >
        {currencies.map((code) => (
          <option key={code} value={code}>{code}</option>
        ))}
      </select>
      {asOf && (
        <span className="currency-note">
          {stale ? 'rates may be out of date' : `rates ${asOf}`}
        </span>
      )}
    </label>
  )
}

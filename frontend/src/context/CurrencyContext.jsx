import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { getRates } from '../api'
import { formatMoney, formatMoneyCompact } from '../lib/format'

const CurrencyContext = createContext(null)

export const useCurrency = () => {
  const value = useContext(CurrencyContext)
  if (!value) throw new Error('useCurrency must be used inside <CurrencyProvider>')
  return value
}

const BASE = 'USD'
const STORAGE_KEY = 'display-currency'

/**
 * Holds the display currency and the rates to convert into it.
 *
 * Amounts are stored in USD; nothing is converted at rest. Conversion happens
 * only at render, through `money`, so switching currency never touches the
 * uploaded data or the analysis behind it.
 */
export function CurrencyProvider({ children }) {
  const [currency, setCurrencyState] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) || BASE
    } catch {
      // Private windows and blocked site data both throw here.
      return BASE
    }
  })
  const [rates, setRates] = useState({ [BASE]: 1 })
  const [error, setError] = useState(null)
  const [stale, setStale] = useState(false)
  const [asOf, setAsOf] = useState(null)

  useEffect(() => {
    let cancelled = false
    getRates(BASE)
      .then((data) => {
        if (cancelled) return
        // Never replace the rate table with something that isn't one. A
        // malformed response used to land here as undefined and take the
        // whole app down on the next read.
        if (!data?.rates || typeof data.rates !== 'object') {
          throw new Error('Rate response did not contain a rates object')
        }
        setRates({ [BASE]: 1, ...data.rates })
        setStale(data.stale)
        setAsOf(data.date)
        setError(null)
      })
      .catch(() => {
        if (cancelled) return
        // Not fatal: the app stays fully usable in USD.
        setError('Exchange rates unavailable — showing USD.')
      })
    return () => { cancelled = true }
  }, [])

  const setCurrency = useCallback((next) => {
    setCurrencyState(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // A remembered preference is a convenience, not a requirement.
    }
  }, [])

  // Fall back to the base if rates haven't loaded or lack the selection, so a
  // partial response can never render a wrong number.
  // Belt and braces: even if something upstream sets this badly, reading a
  // currency out of it must not be able to crash the page.
  const safeRates = rates && typeof rates === 'object' ? rates : { [BASE]: 1 }
  const rate = safeRates[currency] ?? 1
  const active = safeRates[currency] ? currency : BASE

  const value = useMemo(() => ({
    currency: active,
    setCurrency,
    currencies: Object.keys(safeRates).sort(),
    rate,
    asOf,
    stale,
    error,
    isConverted: active !== BASE,
    money: (amount) => formatMoney(amount, active, rate),
    moneyCompact: (amount) => formatMoneyCompact(amount, active, rate),
  }), [active, setCurrency, safeRates, rate, asOf, stale, error])

  return <CurrencyContext.Provider value={value}>{children}</CurrencyContext.Provider>
}

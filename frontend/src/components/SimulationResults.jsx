import { useCurrency } from '../context/CurrencyContext'

/**
 * Renders the result of a simulation: a feasibility banner if needed, plus
 * a table of per-category recommendations.
 */
export default function SimulationResults({ result }) {
  const { money } = useCurrency()
  const { feasible, required_monthly_savings, total_cuttable_monthly, cuts, warning } = result

  return (
    <div className="card">
      <h2>Simulation results</h2>

      {!feasible && warning && (
        <div className="status-banner warning">
          {warning}
        </div>
      )}

      {feasible && (
        <div className="status-banner info">
          Your goal is feasible. Required cuts:{' '}
          <strong>{money(required_monthly_savings)}/month</strong>{' '}
          (selected categories total {money(total_cuttable_monthly)}/month).
        </div>
      )}

      {cuts.length > 0 && (
        <table className="cuts-table">
          <thead>
            <tr>
              <th>Category</th>
              <th className="numeric">Current / mo</th>
              <th className="numeric">Recommended / mo</th>
              <th className="numeric">Cut</th>
              <th className="numeric">Reduction</th>
            </tr>
          </thead>
          <tbody>
            {cuts.map((cut) => (
              <tr key={cut.category}>
                <td>{cut.category}</td>
                <td className="numeric">{money(cut.current_monthly)}</td>
                <td className="numeric">{money(cut.recommended_monthly)}</td>
                <td className="numeric">{money(cut.reduction_amount)}</td>
                <td className="numeric">{cut.reduction_percentage.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
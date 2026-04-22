const BOROUGHS = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island']

// `selected` is an array of borough names; null or empty = "All NYC".
// Behaviour:
//   - Clicking a borough toggles it in/out of the selection. The set is never empty; emptying reverts to All NYC.
//   - Clicking "All NYC" explicitly clears all borough selections.
export default function BoroughSelector({ selected, onChange }) {
  const allActive = !selected || selected.length === 0
  const toggle = (b) => {
    const set = new Set(selected || [])
    if (set.has(b)) set.delete(b); else set.add(b)
    onChange(set.size === 0 ? null : Array.from(set))
  }
  const pickAll = () => onChange(null)
  return (
    <div>
      <div className="borough-row">
        <button
          className={'borough-chip all' + (allActive ? ' active' : '')}
          onClick={pickAll}
        >All NYC</button>
        {BOROUGHS.map((b) => {
          const isOn = !allActive && selected?.includes(b)
          return (
            <button
              key={b}
              className={'borough-chip' + (isOn ? ' active' : '')}
              onClick={() => toggle(b)}
            >{b}</button>
          )
        })}
      </div>
      <p className="mono-meta" style={{ marginTop: 12 }}>
        {allActive
          ? 'Searching all 5 boroughs.'
          : `${selected.length} borough${selected.length === 1 ? '' : 's'} selected.`}
      </p>
    </div>
  )
}

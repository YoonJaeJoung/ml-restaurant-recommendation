export default function Spinner({ size = 'md', label = 'Searching' }) {
  return (
    <div className="loading-overlay">
      <div className={'spinner' + (size === 'sm' ? ' sm' : '')} />
      <div className="loading-label">{label}…</div>
    </div>
  )
}

export function SpinnerInline() {
  return <span className="spinner sm" />
}

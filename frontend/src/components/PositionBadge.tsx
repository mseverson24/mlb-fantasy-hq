export default function PositionBadge({ position }: { position: string | null | undefined }) {
  if (!position) return <span className="muted">—</span>
  const knownClass = ['C', '1B', '2B', '3B', 'SS', 'OF', 'DH', 'SP', 'RP'].includes(position)
    ? `position-badge-${position}`
    : 'position-badge-default'
  return <span className={`position-badge ${knownClass}`}>{position}</span>
}

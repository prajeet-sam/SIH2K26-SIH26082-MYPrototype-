export function LoadingSkeleton({ rows = 3, className }: { rows?: number; className?: string }) {
  return (
    <div className={className} role="status" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="mb-2 h-4 animate-pulse rounded bg-slate-800"
          style={{ width: `${90 - i * 12}%` }}
        />
      ))}
    </div>
  )
}

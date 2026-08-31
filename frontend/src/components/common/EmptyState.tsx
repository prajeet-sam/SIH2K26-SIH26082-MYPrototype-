export function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-700 px-4 py-8 text-center text-sm text-slate-500">
      {message}
    </div>
  )
}

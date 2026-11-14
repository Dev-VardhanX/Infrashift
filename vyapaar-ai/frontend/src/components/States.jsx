export function Loading({ label = "Loading..." }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-ink-500" role="status" aria-live="polite">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-ink-200 border-t-brand-600" />
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function ErrorState({ error, onRetry }) {
  return (
    <div className="card mx-auto my-8 max-w-md p-6 text-center" role="alert">
      <div className="text-3xl">⚠️</div>
      <h3 className="mt-2 font-semibold">Something went wrong</h3>
      <p className="mt-1 text-sm text-ink-500">{error?.message || "Please try again."}</p>
      {onRetry && (
        <button className="btn-primary mt-4" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ icon = "📭", title, hint, action }) {
  return (
    <div className="card mx-auto my-8 max-w-md p-6 text-center">
      <div className="text-3xl">{icon}</div>
      <h3 className="mt-2 font-semibold">{title}</h3>
      {hint && <p className="mt-1 text-sm text-ink-500">{hint}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

/** Wraps the three async states so every page handles them the same way. */
export function Async({ state, isEmpty, empty, children }) {
  if (state.loading && !state.data) return <Loading />;
  if (state.error) return <ErrorState error={state.error} onRetry={state.reload} />;
  if (state.data && isEmpty?.(state.data)) return empty;
  return state.data ? children(state.data) : null;
}

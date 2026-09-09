import type { ReactNode } from "react";

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-border py-14 text-center">
      <p className="font-heading text-lg font-semibold">{title}</p>
      {description ? <p className="max-w-sm text-sm text-ink/60">{description}</p> : null}
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-coral/30 bg-coral/5 py-10 text-center">
      <p className="font-medium text-coral">{message}</p>
      {onRetry ? (
        <button onClick={onRetry} className="text-sm font-semibold text-primary underline underline-offset-2">
          Try again
        </button>
      ) : null}
    </div>
  );
}

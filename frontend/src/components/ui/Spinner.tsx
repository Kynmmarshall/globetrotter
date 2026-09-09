import { Loader2 } from "lucide-react";
import clsx from "clsx";

export function Spinner({ label = "Loading", className }: { label?: string; className?: string }) {
  return (
    <div className={clsx("flex items-center justify-center gap-2 py-10 text-ink/60", className)} role="status">
      <Loader2 className="animate-spin" size={20} aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

import { InspectMode } from '../inspect';

export function StudioInspectPanel() {
  return (
    <div className="space-y-4">
      <p className="text-xs text-slate-500">
        Open a run from Review or the job tray to inspect steps, lineage, and attempts.
      </p>
      <InspectMode />
    </div>
  );
}

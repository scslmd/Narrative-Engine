import type { CanonCustomizationProfile } from '../../types/canonCustomization';

interface CanonProfileListProps {
  profiles: CanonCustomizationProfile[];
  selectedProfileId: string;
  onSelect: (profileId: string) => void;
}

export function CanonProfileList({ profiles, selectedProfileId, onSelect }: CanonProfileListProps) {
  return (
    <div className="rounded border border-slate-200 bg-white p-3 space-y-2">
      <div className="text-sm font-semibold text-slate-900">Profiles</div>
      {profiles.map((profile) => (
        <button
          key={profile.profile_id}
          type="button"
          onClick={() => onSelect(profile.profile_id)}
          className={`w-full text-left rounded border px-2 py-1.5 text-sm ${
            selectedProfileId === profile.profile_id ? 'border-indigo-400 bg-indigo-50' : 'border-slate-200'
          }`}
        >
          {profile.name}
        </button>
      ))}
      {profiles.length === 0 && <div className="text-xs text-slate-500">No profiles yet.</div>}
    </div>
  );
}

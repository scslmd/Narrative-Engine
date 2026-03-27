import { useProjectManifest } from '../hooks/useProjects';
import { SkeletonCard } from './skeleton';

interface Props {
  projectId: string;
}

export function ManifestViewer({ projectId }: Props): React.ReactElement {
  const { data: manifest, isLoading } = useProjectManifest(projectId);

  if (isLoading) {
    return <SkeletonCard />;
  }

  if (!manifest) {
    return <div className="text-gray-500 text-center py-8">No manifest available</div>;
  }

  const config = manifest.config || {};

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-4">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Project Manifest</h2>

      <div className="space-y-3">
        <ManifestField label="Project ID" value={manifest.project_id} />
        <ManifestField label="Project Name" value={manifest.project_name} />
        <ManifestField label="Genre" value={config.genre || 'N/A'} />
        <ManifestField label="Tone Profile" value={config.tone_profile || 'N/A'} />
        <ManifestField label="Point of View" value={formatPov(config.pov)} />
        <ManifestField label="Story Structure" value={formatStructure(config.story_structure)} />
        <ManifestField label="Primary Language" value={config.primary_language || 'N/A'} />
        <ManifestField label="Secondary Language" value={config.secondary_language || 'N/A'} />

        {manifest.premise_text && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Premise</label>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">{manifest.premise_text}</p>
          </div>
        )}

        {manifest.constraints && manifest.constraints.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Constraints</label>
            <ul className="mt-1 space-y-1">
              {manifest.constraints.map((constraint, index) => (
                <li key={index} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                  <span className="text-blue-500 mt-1">•</span>
                  {constraint}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Last updated: {new Date(manifest.updated_at).toLocaleString()}
        </p>
      </div>
    </div>
  );
}

interface ManifestFieldProps {
  label: string;
  value: string;
}

function ManifestField({ label, value }: ManifestFieldProps): React.ReactElement {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label>
      <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{value}</p>
    </div>
  );
}

function formatPov(pov: string): string {
  switch (pov) {
    case 'First': return 'First Person';
    case 'Third_Limited': return 'Third Person Limited';
    case 'Third_Omni': return 'Third Person Omniscient';
    default: return pov;
  }
}

function formatStructure(structure: string): string {
  switch (structure) {
    case 'THREE_ACT': return 'Three Act Structure';
    case 'SAVE_THE_CAT': return 'Save the Cat';
    default: return structure;
  }
}

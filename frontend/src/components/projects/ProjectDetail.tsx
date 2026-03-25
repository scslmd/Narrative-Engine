import { useState, useEffect } from 'react';
import type { ProjectDetailResponse } from '../../types/project';
import { getProject } from '../../services/projects';
import { SkeletonCard } from '../skeleton';
import ErrorBoundary from '../ErrorBoundary';

interface ProjectDetailProps {
  projectId: string;
}

export default function ProjectDetail({ projectId }: ProjectDetailProps) {
  const [project, setProject] = useState<ProjectDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const loadProject = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getProject(projectId);
      setProject(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load project');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <SkeletonCard withHeader />;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        <p>{error}</p>
        <button
          onClick={loadProject}
          className="mt-2 text-sm font-medium hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!project) {
    return null;
  }

  const formatDate = (isoString: string): string => {
    return new Date(isoString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const StatusBadge = ({ status, label }: { status: boolean; label: string }) => (
    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
      status ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
    }`}>
      {label}
    </span>
  );

  return (
    <ErrorBoundary>
      <div className="space-y-4">
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">
            {project.project_name}
          </h2>

          <div className="flex items-center gap-2 mb-3">
            <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm font-medium">
              {project.genre}
            </span>
            <span className="text-xs text-gray-500">
              {project.story_structure.structure_type.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            </span>
          </div>

          <div className="space-y-2 text-sm">
            <p>
              <strong className="text-gray-700">Primary Tone:</strong>{' '}
              {project.tone_profile.primary_tone}
            </p>
            
            {project.tone_profile.secondary_tones.length > 0 && (
              <p>
                <strong className="text-gray-700">Secondary Tones:</strong>{' '}
                {project.tone_profile.secondary_tones.join(', ')}
              </p>
            )}

            <div className="pt-3 border-t mt-3">
              <p className="text-xs text-gray-500 mb-2">Created: {formatDate(project.created_at)}</p>
              <p className="text-xs text-gray-500">Updated: {formatDate(project.updated_at)}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Project Status</h3>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Database</span>
              <StatusBadge status={project.database_exists} label={project.database_exists ? 'Ready' : 'Not created'} />
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Sequence</span>
              <StatusBadge status={project.sequence_exists} label={project.sequence_exists ? 'Exists' : 'Not started'} />
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Chapters</span>
              <StatusBadge status={project.chapter_exists} label={project.chapter_exists ? 'Started' : 'None yet'} />
            </div>
          </div>

          {project.manifest_path && (
            <div className="mt-4 pt-3 border-t">
              <p className="text-xs text-gray-500 mb-1">Manifest:</p>
              <code className="block p-2 bg-gray-100 rounded text-xs break-all">
                {project.manifest_path}
              </code>
            </div>
          )}

          {project.project_dir && (
            <div className="mt-3">
              <p className="text-xs text-gray-500 mb-1">Project Directory:</p>
              <code className="block p-2 bg-gray-100 rounded text-xs break-all">
                {project.project_dir}
              </code>
            </div>
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
}

import { useState, useEffect } from 'react';
import type { ProjectSummaryResponse } from '../../types/project';
import { getProjects } from '../../services/projects';
import { SkeletonList } from '../skeleton';
import ErrorBoundary from '../ErrorBoundary';

interface ProjectListProps {
  onSelectProject: (projectId: string) => void;
}

export default function ProjectList({ onSelectProject }: ProjectListProps) {
  const [projects, setProjects] = useState<ProjectSummaryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getProjects();
      setProjects(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (isoString: string): string => {
    return new Date(isoString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (loading) {
    return <SkeletonList count={3} />;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        <p>{error}</p>
        <button
          onClick={loadProjects}
          className="mt-2 text-sm font-medium hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="text-center p-8">
        <p className="text-gray-500 dark:text-slate-400 mb-4">No projects found</p>
        <button
          onClick={() => onSelectProject('')}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
        >
          Create New Project
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {projects.map((project) => (
        <ErrorBoundary key={project.project_id}>
          <button
            onClick={() => onSelectProject(project.project_id)}
            className="w-full text-left bg-white dark:bg-slate-800 hover:bg-gray-50 dark:hover:bg-slate-700 border rounded-lg p-4 transition-colors shadow-sm"
          >
            <h3 className="font-semibold text-gray-900 dark:text-slate-100 mb-1">
              {project.project_name}
            </h3>

            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-slate-400 mb-2">
              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                {project.genre}
              </span>
            </div>

            <p className="text-xs text-gray-500 dark:text-slate-400 line-clamp-2 mb-2">
              Tone: {project.tone_profile.primary_tone}
              {project.tone_profile.secondary_tones.length > 0 && (
                <span>, {project.tone_profile.secondary_tones.join(', ')}</span>
              )}
            </p>

            <div className="flex items-center justify-between text-xs text-gray-400 dark:text-slate-500">
              <span>{project.story_structure.structure_type.replace('_', ' ')}</span>
              <span>Created {formatDate(project.created_at)}</span>
            </div>
          </button>
        </ErrorBoundary>
      ))}
    </div>
  );
}

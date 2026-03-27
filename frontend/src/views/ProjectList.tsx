import { useProjects, useCreateProject } from '../hooks/useProjects';
import { SkeletonList } from '../components/skeleton';
import { ManifestConfig } from '../lib/projectsApi';

export function ProjectList(): React.ReactElement {
  const { data: projects, isLoading } = useProjects();
  const createMutation = useCreateProject();

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    const config: ManifestConfig = {
      genre: formData.get('genre') as string,
      tone_profile: formData.get('tone_profile') as string,
      pov: formData.get('pov') as 'First' | 'Third_Limited' | 'Third_Omni',
      primary_language: formData.get('primary_language') as string,
      secondary_language: formData.get('secondary_language') as string,
      story_structure: formData.get('story_structure') as 'SAVE_THE_CAT' | 'THREE_ACT',
    };

    createMutation.mutate({
      project_name: formData.get('project_name') as string,
      config,
      premise_text: formData.get('premise_text') as string || undefined,
    });
  };

  if (isLoading) {
    return <SkeletonList count={3} />;
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Create New Project</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="project_name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Project Name
            </label>
            <input
              type="text"
              id="project_name"
              name="project_name"
              required
              className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2"
            />
          </div>

          <div>
            <label htmlFor="genre" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Genre
            </label>
            <input
              type="text"
              id="genre"
              name="genre"
              required
              placeholder="e.g., Science Fiction, Fantasy"
              className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2"
            />
          </div>

          <div>
            <label htmlFor="tone_profile" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Tone Profile
            </label>
            <input
              type="text"
              id="tone_profile"
              name="tone_profile"
              required
              placeholder="e.g., Dark and Gritty, Lighthearted"
              className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2"
            />
          </div>

          <div>
            <label htmlFor="story_structure" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Story Structure
            </label>
            <select
              id="story_structure"
              name="story_structure"
              required
              className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2"
            >
              <option value="THREE_ACT">Three Act</option>
              <option value="SAVE_THE_CAT">Save the Cat</option>
            </select>
          </div>

          <div>
            <label htmlFor="pov" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Point of View
            </label>
            <select
              id="pov"
              name="pov"
              required
              className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2"
            >
              <option value="Third_Limited">Third Person Limited</option>
              <option value="Third_Omni">Third Person Omniscient</option>
              <option value="First">First Person</option>
            </select>
          </div>

          <div>
            <label htmlFor="primary_language" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Primary Language
            </label>
            <input
              type="text"
              id="primary_language"
              name="primary_language"
              required
              defaultValue="English"
              className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2"
            />
          </div>

          <div>
            <label htmlFor="secondary_language" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Secondary Language (Optional)
            </label>
            <input
              type="text"
              id="secondary_language"
              name="secondary_language"
              placeholder="e.g., Spanish, French"
              className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2"
            />
          </div>
        </div>

        <div>
          <label htmlFor="premise_text" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Premise (Optional)
          </label>
          <textarea
            id="premise_text"
            name="premise_text"
            rows={4}
            placeholder="Briefly describe your story premise..."
            className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2"
          />
        </div>

        <button
          type="submit"
          disabled={createMutation.isPending}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {createMutation.isPending ? 'Creating...' : 'Create Project'}
        </button>
      </form>

      <div className="space-y-3">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Your Projects</h2>
        
        {projects && projects.length > 0 ? (
          <ul className="space-y-3">
            {projects.map((project) => (
              <li key={project.project_id}>
                <a
                  href={`/workspace/${project.project_id}`}
                  className="block bg-white dark:bg-gray-800 rounded-lg shadow p-4 hover:shadow-md transition-shadow"
                >
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    {project.project_name}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {project.genre} • {project.tone_profile}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    Updated: {new Date(project.updated_at).toLocaleDateString()}
                  </p>
                </a>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-600 dark:text-gray-400 text-center py-8">
            No projects yet. Create your first project above!
          </p>
        )}
      </div>
    </div>
  );
}

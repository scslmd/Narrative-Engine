import { useProjects, useCreateProject } from '../hooks/useProjects';
import { SkeletonList } from '../components/skeleton';
import { ManifestConfig } from '../lib/projectsApi';
import { BookOpen, Plus, Sparkles, Palette, Compass, Languages, Eye, LayoutTemplate, FileText } from 'lucide-react';
import { useThemeStore } from '../stores/themeStore';

export function ProjectList(): React.ReactElement {
  const { data: projects, isLoading } = useProjects();
  const createMutation = useCreateProject();
  const { mode } = useThemeStore();
  const isDark = mode === 'dark';

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
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center py-4">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-indigo-500/10 to-violet-500/10 border border-indigo-500/20 mb-4">
          <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
          <span className={`text-xs font-medium ${isDark ? 'text-indigo-400' : 'text-indigo-600'}`}>AI-Powered Story Development</span>
        </div>
        <h1 className={`text-2xl font-bold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
          Welcome to Narrative Engine
        </h1>
        <p className={`text-sm mt-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
          Create a new project to start developing your story
        </p>
      </div>

      <form onSubmit={handleSubmit} className={`rounded-xl border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} shadow-card p-6 space-y-5`}>
        <div className="flex items-center gap-2.5 mb-1">
          <BookOpen className={`w-5 h-5 ${isDark ? 'text-indigo-400' : 'text-indigo-500'}`} />
          <h2 className={`text-base font-semibold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>New Project</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Project Name" icon={FileText} isDark={isDark}>
            <input
              type="text"
              id="project_name"
              name="project_name"
              required
              placeholder="Enter project title..."
              className={`w-full rounded-lg border text-sm px-3 py-2.5 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 ${
                isDark ? 'bg-slate-800 border-slate-700 text-slate-200 placeholder-slate-500 hover:border-slate-600' : 'bg-white border-slate-300 text-slate-900 placeholder-slate-400 hover:border-slate-400'
              }`}
            />
          </Field>

          <Field label="Genre" icon={Palette} isDark={isDark}>
            <input
              type="text"
              id="genre"
              name="genre"
              required
              placeholder="e.g., Science Fiction, Fantasy"
              className={`w-full rounded-lg border text-sm px-3 py-2.5 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 ${
                isDark ? 'bg-slate-800 border-slate-700 text-slate-200 placeholder-slate-500 hover:border-slate-600' : 'bg-white border-slate-300 text-slate-900 placeholder-slate-400 hover:border-slate-400'
              }`}
            />
          </Field>

          <Field label="Tone Profile" icon={Compass} isDark={isDark}>
            <input
              type="text"
              id="tone_profile"
              name="tone_profile"
              required
              placeholder="e.g., Dark and Gritty, Lighthearted"
              className={`w-full rounded-lg border text-sm px-3 py-2.5 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 ${
                isDark ? 'bg-slate-800 border-slate-700 text-slate-200 placeholder-slate-500 hover:border-slate-600' : 'bg-white border-slate-300 text-slate-900 placeholder-slate-400 hover:border-slate-400'
              }`}
            />
          </Field>

          <Field label="Story Structure" icon={LayoutTemplate} isDark={isDark}>
            <select
              id="story_structure"
              name="story_structure"
              required
              className={`w-full rounded-lg border text-sm px-3 py-2.5 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 ${
                isDark ? 'bg-slate-800 border-slate-700 text-slate-200 hover:border-slate-600' : 'bg-white border-slate-300 text-slate-900 hover:border-slate-400'
              }`}
            >
              <option value="THREE_ACT">Three Act</option>
              <option value="SAVE_THE_CAT">Save the Cat</option>
            </select>
          </Field>

          <Field label="Point of View" icon={Eye} isDark={isDark}>
            <select
              id="pov"
              name="pov"
              required
              className={`w-full rounded-lg border text-sm px-3 py-2.5 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 ${
                isDark ? 'bg-slate-800 border-slate-700 text-slate-200 hover:border-slate-600' : 'bg-white border-slate-300 text-slate-900 hover:border-slate-400'
              }`}
            >
              <option value="Third_Limited">Third Person Limited</option>
              <option value="Third_Omni">Third Person Omniscient</option>
              <option value="First">First Person</option>
            </select>
          </Field>

          <Field label="Primary Language" icon={Languages} isDark={isDark}>
            <input
              type="text"
              id="primary_language"
              name="primary_language"
              required
              defaultValue="English"
              className={`w-full rounded-lg border text-sm px-3 py-2.5 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 ${
                isDark ? 'bg-slate-800 border-slate-700 text-slate-200 placeholder-slate-500 hover:border-slate-600' : 'bg-white border-slate-300 text-slate-900 placeholder-slate-400 hover:border-slate-400'
              }`}
            />
          </Field>

          <Field label="Secondary Language (Optional)" icon={Languages} isDark={isDark}>
            <input
              type="text"
              id="secondary_language"
              name="secondary_language"
              placeholder="e.g., Spanish, French"
              className={`w-full rounded-lg border text-sm px-3 py-2.5 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 ${
                isDark ? 'bg-slate-800 border-slate-700 text-slate-200 placeholder-slate-500 hover:border-slate-600' : 'bg-white border-slate-300 text-slate-900 placeholder-slate-400 hover:border-slate-400'
              }`}
            />
          </Field>
        </div>

        <Field label="Premise (Optional)" icon={FileText} isDark={isDark}>
          <textarea
            id="premise_text"
            name="premise_text"
            rows={3}
            placeholder="Briefly describe your story premise..."
            className={`w-full rounded-lg border text-sm px-3 py-2.5 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 resize-none ${
              isDark ? 'bg-slate-800 border-slate-700 text-slate-200 placeholder-slate-500 hover:border-slate-600' : 'bg-white border-slate-300 text-slate-900 placeholder-slate-400 hover:border-slate-400'
            }`}
          />
        </Field>

        <button
          type="submit"
          disabled={createMutation.isPending}
          className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-500 to-violet-600 text-white text-sm font-medium rounded-lg hover:from-indigo-600 hover:to-violet-700 shadow-sm hover:shadow-md transition-all disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {createMutation.isPending ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Creating...
            </>
          ) : (
            <>
              <Plus className="w-4 h-4" />
              Create Project
            </>
          )}
        </button>
      </form>

      <div>
        <h2 className={`text-lg font-semibold mb-4 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>Your Projects</h2>
        
        {projects && projects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {projects.map((project) => (
              <a
                key={project.project_id}
                href={`/workspace/${project.project_id}`}
                className={`group block rounded-xl border p-4 transition-all duration-200 ${
                  isDark
                    ? 'bg-slate-900 border-slate-800 hover:border-slate-700 hover:shadow-card-hover'
                    : 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-card-hover'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className={`font-semibold group-hover:text-indigo-500 transition-colors ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                      {project.project_name}
                    </h3>
                    <div className={`flex items-center gap-2 mt-1 text-xs ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
                      <span>{project.genre}</span>
                      <span>•</span>
                      <span>{project.tone_profile}</span>
                    </div>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${isDark ? 'bg-slate-800 text-slate-500' : 'bg-slate-100 text-slate-400'}`}>
                    {new Date(project.updated_at).toLocaleDateString()}
                  </span>
                </div>
              </a>
            ))}
          </div>
        ) : (
          <div className={`text-center py-12 rounded-xl border ${isDark ? 'bg-slate-900/50 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
            <BookOpen className={`w-10 h-10 mx-auto mb-3 ${isDark ? 'text-slate-700' : 'text-slate-300'}`} />
            <p className={`text-sm ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>No projects yet. Create your first project above!</p>
          </div>
        )}
      </div>
    </div>
  );
}

function Field({
  label,
  icon: Icon,
  children,
  isDark,
}: {
  label: string;
  icon: typeof BookOpen;
  children: React.ReactNode;
  isDark: boolean;
}) {
  return (
    <div className="space-y-1.5">
      <label className={`flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
        <Icon className="w-3.5 h-3.5" />
        {label}
      </label>
      {children}
    </div>
  );
}

import { useState, useEffect } from 'react';
import { useProjects, useCreateProject } from '../hooks/useProjects';
import { SkeletonList } from '../components/skeleton';
import { ManifestConfig } from '../lib/projectsApi';
import { BookOpen, Plus, Sparkles, Palette, Compass, Languages, Eye, LayoutTemplate, FileText, Upload, Trash2, X } from 'lucide-react';
import { useThemeStore } from '../stores/themeStore';
import { StoryImportModal } from '../components/projects/StoryImportModal';
import { useApiMutation } from '../hooks/useApiMutation';
import { useToast } from '../hooks/useToast';
import { deleteProject } from '../services/projects';
import type { ProjectSummary } from '../lib/projectsApi';

export function ProjectList(): React.ReactElement {
  const { data: projects, isLoading } = useProjects();
  const createMutation = useCreateProject();
  const { mode } = useThemeStore();
  const isDark = mode === 'dark';
  const [selectedPov, setSelectedPov] = useState<string>('Third_Limited');
  const [selectedStructure, setSelectedStructure] = useState<string>('THREE_ACT');
  const [showImportModal, setShowImportModal] = useState(false);
  const [deletingProject, setDeletingProject] = useState<ProjectSummary | null>(null);
  const { addToast } = useToast();

  const deleteMutation = useApiMutation({
    mutationFn: (projectId: string) => deleteProject(projectId),
    invalidateKeys: [['projects']],
    onSuccessToast: 'Project deleted successfully',
    onErrorToast: false,
  });

  useEffect(() => {
    if (!deleteMutation.error) return;
    const status = deleteMutation.error.status;
    if (status === 409) {
      addToast('Cannot delete project with active jobs. Complete or cancel jobs first.', 'error');
    } else if (status === 404) {
      addToast('Project not found', 'error');
    } else if (status === 403) {
      addToast('Access denied', 'error');
    } else {
      addToast(deleteMutation.error.message, 'error');
    }
  }, [deleteMutation.error, addToast]);

  const handleDeleteConfirm = () => {
    if (!deletingProject) return;
    deleteMutation.mutate(deletingProject.project_id);
    setDeletingProject(null);
  };

  const handleDeleteCancel = () => {
    setDeletingProject(null);
  };

  const handleDeleteClick = (project: ProjectSummary) => {
    setDeletingProject(project);
  };

  const POV_DESCRIPTIONS: Record<string, string> = {
    First: '"I" — narrator is a character in the story',
    Second: '"You" — narrator addresses the reader as a character',
    Third_Limited: '"He/She" — follows one character\'s thoughts and perceptions',
    Third_Omni: '"He/She" — narrator knows all characters\' thoughts and feelings',
    Third_Objective: '"He/She" — camera-like, reports only observable actions and dialogue',
    Third_Multiple: '"He/She" — alternates limited POV across multiple characters',
    Other: 'Custom point of view not listed above',
  };

  const STRUCTURE_DESCRIPTIONS: Record<string, string> = {
    THREE_ACT: 'Setup, Confrontation, Resolution — the classic three-act dramatic arc',
    SAVE_THE_CAT: "Blake Snyder's 15-beat sheet for screenwriting and prose",
    HERO_JOURNEY: "Campbell's monomyth: Departure, Initiation, Return with 17 stages",
    FREYTAGS_PYRAMID: 'Five-act arc: Introduction, Rising Action, Climax, Falling Action, Catastrophe',
    KISHOTENKETSU: 'Four-act East Asian structure: Intro, Development, Twist, Conclusion',
    FICHTEAN_CURVE: 'Series of escalating crises building to a single climax, no exposition',
    SEVEN_POINT_STRUCTURE: 'Beginning, Plot Turn 1, Pinch 1, Midpoint, Pinch 2, Plot Turn 2, Resolution',
    SEVEN_KEY_STEPS: 'Want, Need, Plan, Opponent, Self-Assertion, Revelation, New Equilibrium',
    SNOWFLAKE_METHOD: 'Iterative expansion from one sentence to full chapter summaries',
    OTHER: 'Custom structure not listed above',
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    const config: ManifestConfig = {
      genre: formData.get('genre') as string,
      tone_profile: formData.get('tone_profile') as string,
      pov: formData.get('pov') as 'First' | 'Second' | 'Third_Limited' | 'Third_Omni' | 'Third_Objective' | 'Third_Multiple' | 'Other',
      primary_language: formData.get('primary_language') as string,
      secondary_language: formData.get('secondary_language') as string,
      story_structure: formData.get('story_structure') as string,
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
              value={selectedStructure}
              onChange={(e) => setSelectedStructure(e.target.value)}
              className={`w-full rounded-lg border text-sm px-3 py-2.5 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 ${
                isDark ? 'bg-slate-800 border-slate-700 text-slate-200 hover:border-slate-600' : 'bg-white border-slate-300 text-slate-900 hover:border-slate-400'
              }`}
            >
              <option value="THREE_ACT">Three Act Structure</option>
              <option value="SAVE_THE_CAT">Save the Cat</option>
              <option value="HERO_JOURNEY">Hero's Journey</option>
              <option value="FREYTAGS_PYRAMID">Freytag's Pyramid</option>
              <option value="KISHOTENKETSU">Kishōtenketsu</option>
              <option value="FICHTEAN_CURVE">Fichtean Curve</option>
              <option value="SEVEN_POINT_STRUCTURE">Seven-Point Structure</option>
              <option value="SEVEN_KEY_STEPS">Seven Key Steps</option>
              <option value="SNOWFLAKE_METHOD">Snowflake Method</option>
              <option value="OTHER">Other</option>
            </select>
            <p className={`mt-1 text-xs ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
              {STRUCTURE_DESCRIPTIONS[selectedStructure]}
            </p>
          </Field>

          <Field label="Point of View" icon={Eye} isDark={isDark}>
            <select
              id="pov"
              name="pov"
              required
              value={selectedPov}
              onChange={(e) => setSelectedPov(e.target.value)}
              className={`w-full rounded-lg border text-sm px-3 py-2.5 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 ${
                isDark ? 'bg-slate-800 border-slate-700 text-slate-200 hover:border-slate-600' : 'bg-white border-slate-300 text-slate-900 hover:border-slate-400'
              }`}
            >
              <option value="First">First Person</option>
              <option value="Second">Second Person</option>
              <option value="Third_Limited">Third Person Limited</option>
              <option value="Third_Omni">Third Person Omniscient</option>
              <option value="Third_Objective">Third Person Objective</option>
              <option value="Third_Multiple">Third Person Multiple</option>
              <option value="Other">Other</option>
            </select>
            <p className={`mt-1 text-xs ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
              {POV_DESCRIPTIONS[selectedPov]}
            </p>
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

        <button
          type="button"
          onClick={() => setShowImportModal(true)}
          disabled={createMutation.isPending}
          className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white text-sm font-medium rounded-lg hover:from-emerald-600 hover:to-teal-700 shadow-sm hover:shadow-md transition-all disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <Upload className="w-4 h-4" />
          Import Existing Story
        </button>
      </form>

      <div>
        <h2 className={`text-lg font-semibold mb-4 ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>Your Projects</h2>
        
        {projects && projects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
           {projects.map((project) => (
               <div
                 key={project.project_id}
                 className={`group rounded-xl border p-4 transition-all duration-200 ${
                   isDark
                     ? 'bg-slate-900 border-slate-800 hover:border-slate-700 hover:shadow-card-hover'
                     : 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-card-hover'
                 }`}
               >
                 <div className="flex items-start justify-between">
                   <a
                     href={`/workspace/${project.project_id}`}
                     className="flex-1 min-w-0"
                   >
                     <h3 className={`font-semibold group-hover:text-indigo-500 transition-colors ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                       {project.project_name}
                     </h3>
                     <div className={`flex items-center gap-2 mt-1 text-xs ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
                       <span>{project.genre}</span>
                       <span>•</span>
                       <span>{project.tone_profile}</span>
                     </div>
                   </a>
                   <div className="flex items-center gap-2">
                     <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${isDark ? 'bg-slate-800 text-slate-500' : 'bg-slate-100 text-slate-400'}`}>
                       {new Date(project.updated_at).toLocaleDateString()}
                     </span>
                     <button
                       onClick={() => handleDeleteClick(project)}
                       disabled={deleteMutation.isPending}
                       className={`p-1 rounded transition-colors ${
                         isDark
                           ? 'text-slate-600 hover:text-red-400 hover:bg-slate-800'
                           : 'text-slate-400 hover:text-red-500 hover:bg-slate-100'
                       } disabled:opacity-50`}
                       title="Delete project"
                       aria-label={`Delete ${project.project_name}`}
                     >
                       <Trash2 className="w-3.5 h-3.5" />
                     </button>
                   </div>
                 </div>
               </div>
             ))}
          </div>
        ) : (
          <div className={`text-center py-12 rounded-xl border ${isDark ? 'bg-slate-900/50 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
            <BookOpen className={`w-10 h-10 mx-auto mb-3 ${isDark ? 'text-slate-700' : 'text-slate-300'}`} />
            <p className={`text-sm ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>No projects yet. Create your first project above!</p>
          </div>
        )}
      </div>

      <StoryImportModal isOpen={showImportModal} onClose={() => setShowImportModal(false)} />

      {deletingProject && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={handleDeleteCancel}
        >
          <div
            className={`mx-4 w-full max-w-md rounded-xl border p-6 shadow-lg ${
              isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-200'
            }`}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className={`text-base font-semibold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                Delete Project
              </h3>
              <button
                onClick={handleDeleteCancel}
                className={`p-1 rounded transition-colors ${
                  isDark ? 'text-slate-500 hover:text-slate-300 hover:bg-slate-800' : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100'
                }`}
                aria-label="Cancel"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className={`text-sm mb-6 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
              Delete &apos;{deletingProject.project_name}&apos; and all associated data? This cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={handleDeleteCancel}
                className={`px-4 py-2 text-sm font-medium rounded-lg border transition-colors ${
                  isDark
                    ? 'border-slate-700 text-slate-300 hover:bg-slate-800'
                    : 'border-slate-300 text-slate-700 hover:bg-slate-50'
                }`}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 text-sm font-medium rounded-lg bg-red-600 text-white hover:bg-red-700 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}
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

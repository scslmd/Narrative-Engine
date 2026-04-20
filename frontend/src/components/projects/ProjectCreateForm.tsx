import { useState } from 'react';
import type { StoryStructureType, ProjectCreateRequest } from '../../types/project';
import { createProject } from '../../services/projects';
import { toast } from '../../lib/toast';

interface ProjectCreateFormProps {
  onSuccess: (projectId: string) => void;
  onCancel: () => void;
}

type ProjectType = 'standard' | 'brain_dump';

const GENRES = [
  'Fantasy',
  'Science Fiction',
  'Mystery',
  'Romance',
  'Thriller',
  'Horror',
  'Historical Fiction',
  'Literary Fiction',
];

const STRUCTURE_TYPES: StoryStructureType[] = [
  'THREE_ACT',
  'SAVE_THE_CAT',
  'HERO_JOURNEY',
  'FREYTAGS_PYRAMID',
  'KISHOTENKETSU',
  'FICHTEAN_CURVE',
  'SEVEN_POINT_STRUCTURE',
  'SEVEN_KEY_STEPS',
  'SNOWFLAKE_METHOD',
  'OTHER',
];

const STRUCTURE_LABELS: Record<StoryStructureType, string> = {
  THREE_ACT: 'Three Act Structure',
  SAVE_THE_CAT: 'Save the Cat',
  HERO_JOURNEY: "Hero's Journey",
  FREYTAGS_PYRAMID: "Freytag's Pyramid",
  KISHOTENKETSU: 'Kishōtenketsu',
  FICHTEAN_CURVE: 'Fichtean Curve',
  SEVEN_POINT_STRUCTURE: 'Seven-Point Structure',
  SEVEN_KEY_STEPS: 'Seven Key Steps',
  SNOWFLAKE_METHOD: 'Snowflake Method',
  BRAINDUMP: 'Brain Dump',
  OTHER: 'Other',
};

export default function ProjectCreateForm({ onSuccess, onCancel }: ProjectCreateFormProps) {
  const [projectType, setProjectType] = useState<ProjectType>('standard');
  const [projectName, setProjectName] = useState('');
  const [genre, setGenre] = useState(GENRES[0]);
  const [primaryTone, setPrimaryTone] = useState('');
  const [secondaryTones, setSecondaryTones] = useState<string[]>([]);
  const [structureType, setStructureType] = useState<StoryStructureType>('THREE_ACT');
  const [loading, setLoading] = useState(false);

  const TONES = [
    'Serious',
    'Humorous',
    'Dark',
    'Hopeful',
    'Melancholic',
    'Adventurous',
    'Mysterious',
    'Romantic',
  ];

  const toggleSecondaryTone = (tone: string) => {
    if (secondaryTones.includes(tone)) {
      setSecondaryTones(secondaryTones.filter((t) => t !== tone));
    } else {
      if (secondaryTones.length < 3) {
        setSecondaryTones([...secondaryTones, tone]);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!projectName.trim()) {
      toast.error('Project name is required');
      return;
    }

    if (projectName.length > 100) {
      toast.error('Project name must be 100 characters or less');
      return;
    }

    if (projectType === 'standard' && !primaryTone) {
      toast.error('Primary tone is required');
      return;
    }

    setLoading(true);

    try {
      const data: ProjectCreateRequest = {
         project_name: projectName.trim(),
         project_kind: projectType === 'brain_dump' ? 'brain_dump' : 'standard',
       };

       if (projectType === 'standard') {
         data.genre = genre;
         data.tone_profile = `${primaryTone}${secondaryTones.length > 0 ? ', ' + secondaryTones.join(', ') : ''}`;
         data.story_structure = structureType;
       }

      const result = await createProject(data);
      toast.success('Project created successfully');
      onSuccess(result.project_id);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Project Type
        </label>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => setProjectType('standard')}
            className={`flex-1 px-4 py-3 rounded-lg border-2 text-sm font-medium transition-all ${
              projectType === 'standard'
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-200 text-gray-600 hover:border-gray-300'
            }`}
          >
            <div className="font-semibold">Standard Project</div>
            <div className="text-xs mt-1 opacity-70">Full project setup with genre, tone & structure</div>
          </button>
          <button
            type="button"
            onClick={() => setProjectType('brain_dump')}
            className={`flex-1 px-4 py-3 rounded-lg border-2 text-sm font-medium transition-all ${
              projectType === 'brain_dump'
                ? 'border-amber-500 bg-amber-50 text-amber-700'
                : 'border-gray-200 text-gray-600 hover:border-gray-300'
            }`}
          >
            <div className="font-semibold">Brain Dump</div>
            <div className="text-xs mt-1 opacity-70">Skip setup — start typing ideas immediately</div>
          </button>
        </div>
      </div>

      <div>
        <label htmlFor="projectName" className="block text-sm font-medium text-gray-700 mb-1">
          Project Name *
        </label>
        <input
          id="projectName"
          type="text"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          maxLength={100}
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Enter project name"
        />
        <p className="mt-1 text-xs text-gray-500">{projectName.length}/100 characters</p>
      </div>

      {projectType === 'standard' && (
        <>
          <div>
            <label htmlFor="genre" className="block text-sm font-medium text-gray-700 mb-1">
              Genre *
            </label>
            <select
              id="genre"
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {GENRES.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="primaryTone" className="block text-sm font-medium text-gray-700 mb-1">
              Primary Tone *
            </label>
            <select
              id="primaryTone"
              value={primaryTone}
              onChange={(e) => setPrimaryTone(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select a tone</option>
              {TONES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Secondary Tones (optional, max 3)
            </label>
            <div className="flex flex-wrap gap-2">
              {TONES.filter((t) => t !== primaryTone).map((tone) => (
                <button
                  key={tone}
                  type="button"
                  onClick={() => toggleSecondaryTone(tone)}
                  className={`px-3 py-1 text-sm rounded-full transition-colors ${
                    secondaryTones.includes(tone)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {tone}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label htmlFor="structureType" className="block text-sm font-medium text-gray-700 mb-1">
              Story Structure *
            </label>
            <select
              id="structureType"
              value={structureType}
              onChange={(e) => setStructureType(e.target.value as StoryStructureType)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {STRUCTURE_TYPES.map((s) => (
                <option key={s} value={s}>
                  {STRUCTURE_LABELS[s]}
                </option>
              ))}
            </select>
          </div>
        </>
      )}

      <div className="flex gap-3 pt-4">
        <button
          type="submit"
          disabled={loading}
          className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg transition-colors font-medium"
        >
          {loading ? 'Creating...' : 'Create Project'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={loading}
          className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition-colors font-medium"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

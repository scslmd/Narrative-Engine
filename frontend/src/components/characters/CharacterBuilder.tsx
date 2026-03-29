import { useState } from 'react';
import type { CharacterRecord } from '../../types/characters';

interface CharacterBuilderProps {
  projectId: string;
  character?: CharacterRecord;
  onSave?: (character: Partial<CharacterRecord>) => void;
  onDelete?: (characterId: string) => void;
  onCancel?: () => void;
}

export function CharacterBuilder({ character, onSave, onDelete, onCancel }: CharacterBuilderProps) {
  const [name, setName] = useState(character?.name || '');
  const [description, setDescription] = useState(character?.description || '');
  const [personality, setPersonality] = useState(character?.personality || '');
  const [motivation, setMotivation] = useState(character?.motivation || '');
  const [conflict, setConflict] = useState(character?.conflict || '');
  const [arc, setArc] = useState(character?.arc || '');
  const [role, setRole] = useState<CharacterRecord['role']>(character?.role || 'SUPPORTING');
  const [isAntagonist, setIsAntagonist] = useState(character?.is_antagonist || false);

  const handleSave = () => {
    onSave?.({
      name,
      description,
      personality,
      motivation,
      conflict,
      arc,
      role,
      is_antagonist: isAntagonist,
    });
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="p-4 bg-white border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {character ? 'Edit Character' : 'New Character'}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Build and refine your characters
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Save
            </button>
            {character && onDelete && (
              <button
                onClick={() => onDelete(character.character_id)}
                className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
              >
                Delete
              </button>
            )}
            {onCancel && (
              <button
                onClick={onCancel}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Editor content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Name */}
          <Section title="Name" description="The character's name">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter character name"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
            />
          </Section>

          {/* Role and Type */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Section title="Role" description="Character's role in the story">
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as CharacterRecord['role'])}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="PROTAGONIST">Protagonist</option>
                <option value="ANTAGONIST">Antagonist</option>
                <option value="DEUTERAGONIST">Deuteragonist</option>
                <option value="SUPPORTING">Supporting</option>
                <option value="TERTIARY">Tertiary</option>
              </select>
            </Section>

            <Section title="Type" description="Character classification">
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isAntagonist}
                    onChange={(e) => setIsAntagonist(e.target.checked)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">Antagonist</span>
                </label>
              </div>
            </Section>
          </div>

          {/* Description */}
          <Section title="Description" description="Physical appearance and key traits">
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the character's appearance, age, and distinctive features..."
              className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </Section>

          {/* Personality */}
          <Section title="Personality" description="Character's personality and temperament">
            <textarea
              value={personality}
              onChange={(e) => setPersonality(e.target.value)}
              placeholder="What are their key personality traits? How do they typically behave?"
              className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </Section>

          {/* Motivation and Conflict */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Section title="Motivation" description="What drives this character?">
              <textarea
                value={motivation}
                onChange={(e) => setMotivation(e.target.value)}
                placeholder="What does this character want? What drives them?"
                className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>

            <Section title="Conflict" description="Internal struggles and challenges">
              <textarea
                value={conflict}
                onChange={(e) => setConflict(e.target.value)}
                placeholder="What internal conflicts or challenges does this character face?"
                className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              />
            </Section>
          </div>

          {/* Character Arc */}
          <Section title="Character Arc" description="How the character changes throughout the story">
            <textarea
              value={arc}
              onChange={(e) => setArc(e.target.value)}
              placeholder="Describe how this character changes or grows throughout the story..."
              className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </Section>
        </div>
      </div>
    </div>
  );
}

interface SectionProps {
  title: string;
  description: string;
  children: React.ReactNode;
}

function Section({ title, description, children }: SectionProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
        <p className="text-xs text-gray-500">{description}</p>
      </div>
      {children}
    </div>
  );
}

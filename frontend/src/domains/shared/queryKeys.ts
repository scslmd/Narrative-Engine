export const queryKeys = {
  planning: {
    sequencePlans: (projectId: string) => ['planning-sequence-plans', projectId] as const,
    chapterPlans: (projectId: string) => ['planning-chapter-plans', projectId] as const,
    scenePlans: (projectId: string) => ['planning-scene-plans', projectId] as const,
    beatPlans: (projectId: string) => ['planning-beat-plans', projectId] as const,
    dependencies: (projectId: string) => ['planning-dependencies', projectId] as const,
    chapterPackets: (projectId: string) => ['planning-chapter-packets', projectId] as const,
  },
  canon: {
    annotations: (projectId: string) => ['canon', 'annotations', projectId] as const,
    profiles: (projectId: string) => ['canon', 'profiles', projectId] as const,
    mythos: (projectId: string) => ['mythos', projectId] as const,
    patterns: (projectId: string) => ['patterns', projectId] as const,
    planningCharacters: (projectId: string) => ['planning', 'characters', projectId] as const,
    planningWorldBible: (projectId: string) => ['planning', 'world-bible', projectId] as const,
  },
  generation: {
    characters: (projectId: string) => ['generation', 'characters', projectId] as const,
    world: (projectId: string) => ['generation', 'world', projectId] as const,
    runs: (projectId: string) => ['generation', 'runs', projectId] as const,
    gates: (runId: string) => ['generation', 'gates', runId] as const,
    run: (generationId: string) => ['generation', 'run', generationId] as const,
    packet: (generationId: string) => ['generation', 'packet', generationId] as const,
  },
};


import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '../../__tests__/test-utils';
import { CanonWorkshop } from './CanonWorkshop';

describe('CanonWorkshop', () => {
  it('renders overview and supports save/preview/generate actions', async () => {
    const onSaveProfile = vi.fn().mockResolvedValue(undefined);
    const onPreviewPacket = vi.fn().mockResolvedValue(undefined);
    const onSubmitGeneration = vi.fn().mockResolvedValue({
      generation_id: 'gen-1',
      source_project_id: 'project-1',
      target_project_id: 'project-1',
      job_ids: [],
      status: 'queued',
      warnings: [],
      created_artifacts: [],
    });

    render(
      <CanonWorkshop
        projectId="project-1"
        characters={[]}
        worldEntries={[]}
        mythosEntries={[]}
        patternEntries={[]}
        annotations={[]}
        profiles={[]}
        onSaveProfile={onSaveProfile}
        onPreviewPacket={onPreviewPacket}
        onSubmitGeneration={onSubmitGeneration}
        packetPreview={null}
      />,
    );

    expect(screen.getByText('Canon Workshop')).toBeInTheDocument();
    expect(screen.getAllByText('Save Profile').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Generate with Selected').length).toBeGreaterThan(0);
  });
});

import { BrainstormWorkspace } from '../brainstorm/BrainstormWorkspace';
import { useBrainstorm } from '../../hooks/useBrainstorm';
import { WorkspaceStatus } from '../planning/ui';

interface StudioIdeasPanelProps {
  projectId: string;
}

export function StudioIdeasPanel({ projectId }: StudioIdeasPanelProps) {
  const { items, isLoading, addItem, clusterItems, promoteItem } = useBrainstorm(projectId);

  if (isLoading) {
    return <WorkspaceStatus title="Loading ideas" detail="Fetching brainstorm items." />;
  }

  return (
    <BrainstormWorkspace
      projectId={projectId}
      items={items}
      onItemAdd={(req) => {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars -- strip project_id, addItem auto-injects it
        const { project_id, ...rest } = req;
        void addItem(rest);
      }}
      onClusterCreate={(itemIds) => void clusterItems(itemIds)}
      onPromote={async ({ item_id, target_object_kind, target_object_id }) => {
        await promoteItem(item_id, target_object_kind, target_object_id);
      }}
    />
  );
}

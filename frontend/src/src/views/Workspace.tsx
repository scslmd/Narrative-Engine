import { useUIStore } from '../stores/uiStore'
import { WorkspaceShell } from '../components/WorkspaceShell'
import { PlanningView } from './PlanningView'
import { WritingView } from './WritingView'
import { ReviewView } from './ReviewView'
import { InspectView } from './InspectView'

export function Workspace() {
  const { mode } = useUIStore()

  const renderView = () => {
    switch (mode) {
      case 'plan':
        return <PlanningView />
      case 'write':
        return <WritingView />
      case 'review':
        return <ReviewView />
      case 'inspect':
        return <InspectView />
      default:
        return <PlanningView />
    }
  }

  return (
    <WorkspaceShell>
      {renderView()}
    </WorkspaceShell>
  )
}
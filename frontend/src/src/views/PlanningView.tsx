import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'

export function PlanningView() {
  return (
    <div className="space-y-4">
      <Card title="New Project">
        <div className="space-y-3">
          <Input label="Project Title" placeholder="Enter project title..." />
          <Input label="Genre" placeholder="e.g., Sci-Fi, Fantasy..." />
          <Input label="Target Length" placeholder="e.g., 80,000 words" />
          <div className="flex justify-end gap-2">
            <Button variant="secondary">Cancel</Button>
            <Button>Create Project</Button>
          </div>
        </div>
      </Card>

      <Card title="Existing Projects">
        <div className="text-gray-500">No projects yet</div>
      </Card>
    </div>
  )
}
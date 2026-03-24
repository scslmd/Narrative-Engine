import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'

export function InspectView() {
  return (
    <div className="space-y-4">
      <Card title="Job History">
        <div className="space-y-2">
          <div className="p-3 border rounded flex justify-between items-center">
            <div>
              <div className="font-medium">Architect Job #123</div>
              <div className="text-sm text-gray-500">Completed 2 hours ago</div>
            </div>
            <Button size="sm" variant="ghost">View Details</Button>
          </div>
          <div className="p-3 border rounded flex justify-between items-center">
            <div>
              <div className="font-medium">Sequencer Job #124</div>
              <div className="text-sm text-gray-500">Completed 1 hour ago</div>
            </div>
            <Button size="sm" variant="ghost">View Details</Button>
          </div>
        </div>
      </Card>

      <Card title="Artifact Lineage">
        <div className="text-gray-500">Select a job to view artifact lineage</div>
      </Card>
    </div>
  )
}
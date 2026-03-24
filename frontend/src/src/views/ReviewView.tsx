import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'

export function ReviewView() {
  return (
    <div className="space-y-4">
      <Card title="Review Queue">
        <div className="space-y-3">
          <div className="p-4 border rounded-lg">
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-medium">Chapter 1: The Beginning</h4>
              <span className="text-sm text-gray-500">Draft v2</span>
            </div>
            <p className="text-gray-600 mb-3">
              The protagonist wakes up in a strange world, unsure of how they got there...
            </p>
            <div className="flex gap-2">
              <Button size="sm" variant="primary">Approve</Button>
              <Button size="sm" variant="secondary">Request Changes</Button>
            </div>
          </div>
        </div>
      </Card>

      <Card title="Feedback">
        <textarea
          className="w-full h-32 p-3 border rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Add feedback..."
        />
        <Button className="mt-2">Submit Feedback</Button>
      </Card>
    </div>
  )
}
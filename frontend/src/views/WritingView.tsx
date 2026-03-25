import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'

export function WritingView() {
  return (
    <div className="space-y-4">
      <Card title="Chapter Outline">
        <div className="space-y-2">
          <div className="p-3 bg-gray-100 rounded border-l-4 border-blue-500">
            <h4 className="font-medium">Chapter 1: The Beginning</h4>
            <p className="text-sm text-gray-600">Introduction to the main character</p>
          </div>
          <div className="p-3 bg-gray-50 rounded">
            <h4 className="font-medium">Chapter 2: The Journey</h4>
            <p className="text-sm text-gray-600">The hero sets out on their quest</p>
          </div>
        </div>
      </Card>

      <Card title="Draft" actions={<Button size="sm">Generate</Button>}>
        <textarea
          className="w-full h-64 p-3 border rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Start writing or generate content..."
        />
        <div className="flex justify-end gap-2 mt-3">
          <Button variant="secondary">Save Draft</Button>
          <Button>Submit for Review</Button>
        </div>
      </Card>
    </div>
  )
}
interface JobProgressProps {
  progress: number | null;
  currentPhase?: string | null;
  currentStep?: string | null;
}

export default function JobProgress({ progress, currentPhase, currentStep }: JobProgressProps) {
  const percentage = progress ?? 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600">Progress</span>
        <span className="font-medium text-gray-900">{percentage}%</span>
      </div>

      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>

      {(currentPhase || currentStep) && (
        <div className="pt-1 space-y-1">
          {currentPhase && (
            <div className="text-xs text-gray-500">
              <span className="font-medium">Phase:</span> {currentPhase}
            </div>
          )}
          
          {currentStep && (
            <div className="text-xs text-gray-500">
              <span className="font-medium">Step:</span> {currentStep}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

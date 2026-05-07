import { useState, useCallback } from 'react';
import type { JobPhase, JobCreateRequest, JobStatusResponse } from '../../types/job';
import { createJob } from '../../services/jobs';
import { useToastStore } from '../../stores/toastStore';
import PhaseSelector from './PhaseSelector';
import PayloadBuilder from './PayloadBuilder';

interface JobLaunchFormProps {
  onJobCreated?: (job: JobStatusResponse) => void;
}

export default function JobLaunchForm({ onJobCreated }: JobLaunchFormProps) {
  const addToast = useToastStore((state) => state.addToast);
  const [selectedPhase, setSelectedPhase] = useState<JobPhase | null>(null);
  const [payload, setPayload] = useState<Record<string, unknown>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedPhase) {
      setError('Please select a job phase');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const request: JobCreateRequest = {
        phase: selectedPhase,
        payload,
      };

      const job = await createJob(request);
      
      addToast(`Job ${job.id} created successfully`, 'success');
      
      if (onJobCreated) {
        onJobCreated(job);
      }

      setSelectedPhase(null);
      setPayload({});
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create job';
      setError(message);
      addToast(`Error: ${message}`, 'error');
    } finally {
      setIsSubmitting(false);
    }
  }, [selectedPhase, payload, onJobCreated, addToast]);

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-slate-100">Launch Job</h2>
        <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">Configure and submit a backend job for execution</p>
      </div>

      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-4 space-y-6">
        <PhaseSelector selectedPhase={selectedPhase} onSelectPhase={setSelectedPhase} />

        {selectedPhase && (
          <PayloadBuilder initialPayload={{}} onPayloadChange={setPayload} />
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
      </form>

      <div className="p-4 border-t bg-gray-50 dark:bg-slate-900">
        <button
          type="submit"
          onClick={handleSubmit}
          disabled={!selectedPhase || isSubmitting}
          className={`w-full py-2.5 rounded-lg font-medium transition-all ${
            !selectedPhase || isSubmitting
              ? 'bg-gray-300 dark:bg-slate-600 text-gray-500 dark:text-slate-400 cursor-not-allowed'
              : 'bg-primary-600 text-white hover:bg-primary-700'
          }`}
        >
          {isSubmitting ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
              Launching...
            </span>
          ) : (
            'Launch Job'
          )}
        </button>

        {!selectedPhase && (
          <p className="text-xs text-gray-500 dark:text-slate-400 text-center mt-2">
            Select a phase and configure payload to enable launch
          </p>
        )}
      </div>
    </div>
  );
}

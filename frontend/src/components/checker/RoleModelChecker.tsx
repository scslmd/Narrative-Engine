import { useState, useEffect } from 'react';
import type { ModelCatalog, RoleModelCheckStatus } from '../../types/checker';
import { getModelCatalog, runChecker, getCheckerStatus, retryChecker } from '../../services/checker';

interface RoleModelCheckerProps {
  projectId: string;
}

export function RoleModelChecker({ projectId }: RoleModelCheckerProps) {
  const [catalog, setCatalog] = useState<ModelCatalog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedModels, setSelectedModels] = useState<Record<string, string>>({});
  const [checkStatus, setCheckStatus] = useState<RoleModelCheckStatus | null>(null);
  const [polling, setPolling] = useState(false);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    loadCatalog();
  }, []);

  useEffect(() => {
    if (checkStatus && checkStatus.status === 'RUNNING') {
      startPolling(checkStatus.run_id);
    } else if (checkStatus && checkStatus.status === 'COMPLETED') {
      setPolling(false);
    }
  }, [checkStatus]);

  const loadCatalog = async () => {
    try {
      const data = await getModelCatalog();
      setCatalog(data);
      
      const defaults: Record<string, string> = {};
      data.workflow_order.forEach((role) => {
        const model = data.discovered_models.find(m => m.role === role);
        if (model) {
          defaults[role] = model.model_id;
        }
      });
      setSelectedModels(defaults);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load models');
    } finally {
      setLoading(false);
    }
  };

  const startPolling = async (runId: string) => {
    setPolling(true);
    
    try {
      while (true) {
        const status = await getCheckerStatus(runId);
        setCheckStatus(status);
        
        if (status.status === 'COMPLETED' || status.status === 'FAILED') {
          break;
        }
        
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    } catch (err) {
      console.error('Polling error:', err);
    } finally {
      setPolling(false);
    }
  };

  const handleRunCheck = async () => {
    if (isRunning) return;
    setIsRunning(true);
    try {
      const status = await runChecker({ project_id: projectId, models: selectedModels });
      setCheckStatus(status);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run checker');
    } finally {
      setIsRunning(false);
    }
  };

  const handleRetry = async () => {
    if (!checkStatus?.run_id) return;
    
    try {
      const status = await retryChecker(checkStatus.run_id);
      setCheckStatus(status);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retry checker');
    }
  };

  if (loading) {
    return <div className="text-gray-500">Loading models...</div>;
  }

  if (!catalog) {
    return <div className="text-red-600">{error || 'Failed to load models'}</div>;
  }

  const getStatusColor = (status: RoleModelCheckStatus['status']) => {
    switch (status) {
      case 'QUEUED':
        return 'bg-yellow-100 text-yellow-800';
      case 'RUNNING':
        return 'bg-blue-100 text-blue-800';
      case 'COMPLETED':
        return 'bg-green-100 text-green-800';
      case 'FAILED':
        return 'bg-red-100 text-red-800';
    }
  };

  return (
    <div className="border rounded-lg p-4">
      <h3 className="font-semibold text-gray-900 mb-4">Role Model Checker</h3>

      <div className="space-y-3 mb-4">
        {catalog.workflow_order.map((role) => (
          <div key={role}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {role.charAt(0).toUpperCase() + role.slice(1)} Model
            </label>
            <select
              value={selectedModels[role] || ''}
              onChange={(e) => setSelectedModels({ ...selectedModels, [role]: e.target.value })}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {catalog.discovered_models
                .filter(m => m.role === role)
                .map(model => (
                  <option key={model.model_id} value={model.model_id}>
                    {model.name} ({model.model_id})
                  </option>
                ))}
            </select>
          </div>
        ))}
      </div>

      {!checkStatus && (
        <button
          onClick={handleRunCheck}
          disabled={isRunning}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isRunning ? 'Running...' : 'Run Checker'}
        </button>
      )}

      {checkStatus && (
        <div className="border-t pt-3">
          <div className="flex items-center justify-between mb-2">
            <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(checkStatus.status)}`}>
              {checkStatus.status}
            </span>
            <span className="text-sm text-gray-500">Attempt #{checkStatus.attempt_number}</span>
          </div>

          {checkStatus.progress_current !== undefined && checkStatus.progress_total !== undefined && (
            <div className="mb-2">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${(checkStatus.progress_current / checkStatus.progress_total) * 100}%` }}
                ></div>
              </div>
              <span className="text-xs text-gray-500">
                {checkStatus.progress_current} / {checkStatus.progress_total}
              </span>
            </div>
          )}

          {polling && (
            <p className="text-sm text-blue-600 mb-2">Checking status...</p>
          )}

          {checkStatus.error && (
            <p className="text-sm text-red-600 mb-2">{checkStatus.error}</p>
          )}

          {checkStatus.status === 'FAILED' && (
            <button
              onClick={handleRetry}
              className="w-full px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
            >
              Retry Checker
            </button>
          )}

          {checkStatus.status === 'COMPLETED' && (
            <p className="text-sm text-green-600">Checker completed successfully</p>
          )}
        </div>
      )}
    </div>
  );
}

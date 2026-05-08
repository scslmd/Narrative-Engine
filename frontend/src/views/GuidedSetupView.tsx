import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, Rocket, AlertTriangle } from 'lucide-react';
import { ChatPanel } from '../components/guided-setup/ChatPanel';
import { FieldPreview } from '../components/guided-setup/FieldPreview';
import { useGuidedSetup } from '../hooks/useGuidedSetup';
import { useGuidedSetupStore } from '../stores/guidedSetupStore';
import { checkLlmHealth, type LlmHealthStatus } from '../services/guidedSetup';

export function GuidedSetupView(): React.ReactElement {
  const navigate = useNavigate();
  const [llmHealth, setLlmHealth] = useState<LlmHealthStatus | null>(null);
  const {
    isAnalyzing,
    createMutation,
    handleAnalyze,
    handleSubmitCreate,
  } = useGuidedSetup();
  const { accumulatedFields, conversationHistory } = useGuidedSetupStore();

  useEffect(() => {
    const check = async () => setLlmHealth(await checkLlmHealth());
    check();
    // Re-check every 30 seconds
    const interval = setInterval(check, 30_000);
    return () => clearInterval(interval);
  }, []);

  const isCreating = createMutation.isPending;
  // Allow creating when user has answered at least one question (beyond the initial seed)
  const hasContent = accumulatedFields.config.project_name || accumulatedFields.foundation.premise_text || conversationHistory.length > 2;

  const handleSend = async (message: string) => {
    try {
      await handleAnalyze(message);
    } catch {
      // Error already handled in store
    }
  };

  const handleCreate = () => {
    try {
      handleSubmitCreate();
    } catch {
      // Error already handled
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-950">
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        {llmHealth && !llmHealth.ok && (
          <div className="max-w-7xl mx-auto mb-3 flex items-center gap-2 px-4 py-2.5 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-amber-800 dark:text-amber-300 text-sm">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>LLM unavailable ({llmHealth.backend}). Conversational features won't work — you can still fill in fields manually and create a project.</span>
          </div>
        )}
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              Story Architect
            </h1>
            {llmHealth && (
              <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                llmHealth.ok
                  ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800'
                  : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800'
              }`}>
                <span className={`w-2 h-2 rounded-full ${llmHealth.ok ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
                {llmHealth.ok ? llmHealth.model || llmHealth.backend : `${llmHealth.backend} offline`}
              </div>
            )}
          </div>

          {hasContent && !isCreating && (
            <button
              onClick={handleCreate}
              className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-violet-500 to-purple-500 text-white rounded-lg hover:from-violet-600 hover:to-purple-600 transition-all font-medium shadow-md"
            >
              <Rocket className="w-4 h-4" />
              Create Project
            </button>
          )}

          {isCreating && (
            <div className="flex items-center gap-2 px-6 py-2.5 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 rounded-lg">
              <Loader2 className="w-4 h-4 animate-spin" />
              Creating project...
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-12rem)]">
          <div className="lg:col-span-2 h-full">
            <ChatPanel onSend={handleSend} isLoading={isAnalyzing} />
          </div>
          <div className="hidden lg:block">
            <FieldPreview />
          </div>
        </div>
      </main>
    </div>
  );
}

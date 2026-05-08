import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { useToastStore } from '../stores/toastStore';
import { useGuidedSetupStore } from '../stores/guidedSetupStore';
import { createFromFields, type GuidedSetupCreateRequest } from '../services/guidedSetup';

export function useGuidedSetup() {
  const navigate = useNavigate();
  const addToast = useToastStore((state) => state.addToast);
  const store = useGuidedSetupStore();

  const createMutation = useMutation({
    mutationFn: (request: GuidedSetupCreateRequest) => createFromFields(request),
    onSuccess: (result) => {
      addToast(`Project '${result.project_name}' created successfully!`, 'success');
      store.reset();
      navigate(`/workspace/${result.project_id}`);
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Failed to create project';
      addToast(message, 'error');
    },
  });

  return {
    ...store,
    createMutation,
    handleSubmitCreate: () => {
      const { accumulatedFields } = store;
      createMutation.mutate({ accumulated_fields: accumulatedFields });
    },
  };
}

import { create } from 'zustand';
import {
  analyzeTurn,
  createFromFields,
  emptyExtractedFields,
  type ChatMessage,
  type ExtractedFields,
  type CategoryProgress,
} from '../services/guidedSetup';

const READINESS_NOTIFICATION = "I think we have enough to create your project. You can review the fields on the right and save whenever you're ready.";

interface GuidedSetupState {
  conversationHistory: ChatMessage[];
  accumulatedFields: ExtractedFields;
  nextQuestion: string;
  progress: number;
  confidence: number;
  readyToCreate: boolean;
  categoryProgress: CategoryProgress[];
  hasBeenReady: boolean;
  isAnalyzing: boolean;
  isCreating: boolean;
  error: string | null;
  turnCount: number;

  setNextQuestion: (question: string) => void;
  addUserMessage: (content: string) => void;
  addSystemMessage: (content: string) => void;
  setFields: (fields: ExtractedFields) => void;
  updateFields: (patch: Record<string, unknown>) => void;
  setProgress: (progress: number, confidence: number, ready: boolean, categoryProgress: CategoryProgress[]) => void;
  setIsAnalyzing: (loading: boolean) => void;
  setIsCreating: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;

  handleAnalyze: (answer: string) => Promise<void>;
  handleCreate: () => Promise<{ project_id: string; project_name: string }>;
}

export const useGuidedSetupStore = create<GuidedSetupState>((set, get) => ({
  conversationHistory: [
    { role: 'system', content: "I'd love to help you build your story project. What kind of story are you looking to write? Tell me about the genre, setting, or any ideas you have in mind.", turn: 1 },
  ],
  accumulatedFields: emptyExtractedFields(),
  nextQuestion: "I'd love to help you build your story project. What kind of story are you looking to write? Tell me about the genre, setting, or any ideas you have in mind.",
  progress: 0,
  confidence: 0,
  readyToCreate: false,
  categoryProgress: [],
  hasBeenReady: false,
  isAnalyzing: false,
  isCreating: false,
  error: null,
  turnCount: 1,

  setNextQuestion: (question) => set({ nextQuestion: question }),

  addUserMessage: (content) => {
    const { conversationHistory, turnCount } = get();
    set({
      conversationHistory: [
        ...conversationHistory,
        { role: 'user', content, turn: turnCount + 1 },
      ],
      turnCount: turnCount + 1,
    });
  },

  addSystemMessage: (content) => {
    const { conversationHistory, turnCount } = get();
    set({
      conversationHistory: [
        ...conversationHistory,
        { role: 'system', content, turn: turnCount + 1 },
      ],
      turnCount: turnCount + 1,
    });
  },

  setFields: (fields) => set({ accumulatedFields: fields }),

  updateFields: (patch) => {
    const { accumulatedFields } = get();
    set({
      accumulatedFields: {
        ...accumulatedFields,
        ...patch,
        config: patch.config ? { ...accumulatedFields.config, ...patch.config } : accumulatedFields.config,
        foundation: patch.foundation ? { ...accumulatedFields.foundation, ...patch.foundation } : accumulatedFields.foundation,
      },
    });
  },

  setProgress: (progress, confidence, ready, categoryProgress) =>
    set({ progress, confidence, readyToCreate: ready, categoryProgress }),

  setIsAnalyzing: (loading) => set({ isAnalyzing: loading }),
  setIsCreating: (loading) => set({ isCreating: loading }),
  setError: (error) => set({ error }),

  reset: () => set({
    conversationHistory: [
      { role: 'system', content: "I'd love to help you build your story project. What kind of story are you looking to write? Tell me about the genre, setting, or any ideas you have in mind.", turn: 1 },
    ],
    accumulatedFields: emptyExtractedFields(),
    nextQuestion: "I'd love to help you build your story project. What kind of story are you looking to write? Tell me about the genre, setting, or any ideas you have in mind.",
    progress: 0,
    confidence: 0,
    readyToCreate: false,
    categoryProgress: [],
    hasBeenReady: false,
    isAnalyzing: false,
    isCreating: false,
    error: null,
    turnCount: 1,
  }),

  handleAnalyze: async (answer: string) => {
    const { conversationHistory, accumulatedFields, turnCount } = get();

    // Show user message immediately
    const userMessage = { role: 'user' as const, content: answer, turn: turnCount + 1 };
    set({
      isAnalyzing: true,
      error: null,
      conversationHistory: [...conversationHistory, userMessage],
      turnCount: turnCount + 1,
    });

    try {
      const request = {
        conversation_history: [...conversationHistory, userMessage],
        current_answer: answer,
        accumulated_fields: accumulatedFields,
      };

      const response = await analyzeTurn(request);

      const wasReady = get().hasBeenReady;
      const newlyReady = response.ready_to_create && !wasReady;

      const currentTurn = get().turnCount;
      const extraMessages: ChatMessage[] = [];
      if (newlyReady) {
        extraMessages.push({
          role: 'system' as const,
          content: READINESS_NOTIFICATION,
          turn: currentTurn + 2,
        });
      }

      set({
        accumulatedFields: response.extracted_fields,
        nextQuestion: response.next_question,
        progress: response.progress,
        confidence: response.confidence,
        readyToCreate: response.ready_to_create,
        categoryProgress: response.category_progress,
        hasBeenReady: response.ready_to_create || wasReady,
        conversationHistory: [
          ...get().conversationHistory,
          { role: 'system' as const, content: response.next_question, turn: currentTurn + 1 },
          ...extraMessages,
        ],
        turnCount: currentTurn + 1 + extraMessages.length,
      });
    } catch (error) {
      const errorMessage = "Sorry, I'm having trouble connecting. Make sure the backend server and LLM are running.";
      const currentTurn = get().turnCount;
      set({
        error: error instanceof Error ? error.message : 'Failed to analyze answer',
        conversationHistory: [
          ...get().conversationHistory,
          { role: 'system' as const, content: errorMessage, turn: currentTurn + 1 },
        ],
        turnCount: currentTurn + 1,
      });
      throw error;
    } finally {
      set({ isAnalyzing: false });
    }
  },

  handleCreate: async () => {
    const { accumulatedFields } = get();

    set({ isCreating: true, error: null });

    try {
      const response = await createFromFields({ accumulated_fields: accumulatedFields });
      return { project_id: response.project_id, project_name: response.project_name };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create project';
      set({ error: message });
      throw error;
    } finally {
      set({ isCreating: false });
    }
  },
}));

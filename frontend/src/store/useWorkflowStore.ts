import { create } from 'zustand';
import { WorkflowState, AgentFinding, AgentTask } from '@/types/workflow';

interface WorkflowStore {
  activeWorkflow: WorkflowState | null;
  history: WorkflowState[];
  isStreaming: boolean;
  setActiveWorkflow: (workflow: WorkflowState | null) => void;
  updateWorkflow: (updates: Partial<WorkflowState>) => void;
  addFinding: (finding: AgentFinding) => void;
  addTask: (task: AgentTask) => void;
  setStreaming: (isStreaming: boolean) => void;
  reset: () => void;
}

export const useWorkflowStore = create<WorkflowStore>((set) => ({
  activeWorkflow: null,
  history: [],
  isStreaming: false,
  setActiveWorkflow: (workflow) => set({ activeWorkflow: workflow }),
  updateWorkflow: (updates) => set((state) => ({
    activeWorkflow: state.activeWorkflow ? { ...state.activeWorkflow, ...updates } : null
  })),
  addFinding: (finding) => set((state) => ({
    activeWorkflow: state.activeWorkflow ? {
      ...state.activeWorkflow,
      findings: [...state.activeWorkflow.findings, finding]
    } : null
  })),
  addTask: (task) => set((state) => ({
    activeWorkflow: state.activeWorkflow ? {
      ...state.activeWorkflow,
      tasks: [...state.activeWorkflow.tasks, task]
    } : null
  })),
  setStreaming: (isStreaming) => set({ isStreaming }),
  reset: () => set({ activeWorkflow: null, isStreaming: false }),
}));

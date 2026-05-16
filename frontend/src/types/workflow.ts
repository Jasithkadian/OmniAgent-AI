export type AgentName = "planning" | "supervisor" | "research" | "coding" | "report" | "presentation" | "browser";
export type WorkflowStatus = "queued" | "running" | "completed" | "failed";

export interface AgentFinding {
  agent: AgentName;
  title: string;
  content: string;
  confidence: number;
  citations: string[];
  metadata: Record<string, any>;
}

export interface AgentTask {
  id: string;
  agent: AgentName;
  title: string;
  objective: string;
  depends_on: string[];
  status: WorkflowStatus;
}

export interface AgentMessage {
  agent: AgentName;
  content: string;
  metadata: Record<string, any>;
}

export interface WorkflowState {
  workflow_id: string;
  user_id: string;
  conversation_id: string | null;
  objective: string;
  status: WorkflowStatus;
  tasks: AgentTask[];
  findings: AgentFinding[];
  messages: AgentMessage[];
  errors: string[];
  active_agent: AgentName | null;
  artifacts: Record<string, any>;
  document_ids: string[];
  iteration_count: number;
}

export interface WebSocketEvent {
  event: string;
  name: string;
  data?: any;
}

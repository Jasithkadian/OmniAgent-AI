import React, { useState, useRef, useEffect } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Send, Loader2 } from 'lucide-react';
import { useWorkflowStore } from '@/store/useWorkflowStore';
import { WorkflowSocket } from '@/websocket/socket';
import { v4 as uuidv4 } from 'uuid';
import AgentActivityTimeline from '@/features/agents/AgentActivityTimeline';

const ChatWorkspace: React.FC = () => {
  const [input, setInput] = useState('');
  const { activeWorkflow, setActiveWorkflow, updateWorkflow, setStreaming, isStreaming } = useWorkflowStore();
  const socketRef = useRef<WorkflowSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initializing socket for the workspace
    socketRef.current = new WorkflowSocket((event) => {
      console.log('WS Event:', event);
      if (event.event === 'node_start') {
        updateWorkflow({ active_agent: event.name as any });
      } else if (event.event === 'node_end') {
        // Optional end logic
      }
    });

    return () => {
      socketRef.current?.disconnect();
    };
  }, []);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const workflowId = uuidv4();
    const objective = input;
    setInput('');
    setStreaming(true);

    // Initialize state
    setActiveWorkflow({
      workflow_id: workflowId,
      user_id: '00000000-0000-0000-0000-000000000000', // Dev placeholder
      conversation_id: null,
      objective,
      status: 'running',
      tasks: [],
      findings: [],
      messages: [],
      errors: [],
      active_agent: 'planning',
      artifacts: {},
      document_ids: [],
      iteration_count: 0
    });

    // Connect and run via WS
    socketRef.current?.connect();
    // In a real implementation, we'd wait for 'onopen' before sending
    setTimeout(() => {
      socketRef.current?.send({ objective, document_ids: [] });
    }, 500);
  };

  return (
    <div className="flex flex-col h-full bg-background">
      <ScrollArea className="flex-1 p-6" ref={scrollRef}>
        <div className="max-w-3xl mx-auto space-y-6">
          {!activeWorkflow && (
            <div className="h-[50vh] flex flex-col items-center justify-center text-center space-y-4">
              <h2 className="text-3xl font-bold tracking-tight">How can I help you today?</h2>
              <p className="text-muted-foreground max-w-md">
                Upload your research papers, technical docs, or project specs and let the agent swarm analyze them for you.
              </p>
            </div>
          )}

          {activeWorkflow && (
            <div className="space-y-4 animate-in fade-in duration-500">
              <div className="flex justify-start">
                <div className="bg-muted px-4 py-3 rounded-2xl rounded-tl-none max-w-[85%]">
                  <p className="text-sm font-medium mb-1">Objective</p>
                  <p className="text-sm">{activeWorkflow.objective}</p>
                </div>
              </div>

              <AgentActivityTimeline />
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="p-6 border-t border-border bg-card/50 backdrop-blur-sm">
        <div className="max-w-3xl mx-auto relative">
          <Input
            placeholder="Describe your research objective..."
            className="pr-12 h-12 rounded-xl border-2 focus-visible:ring-primary shadow-sm"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={isStreaming}
          />
          <Button
            size="icon"
            className="absolute right-1.5 top-1.5 h-9 w-9 rounded-lg transition-transform active:scale-95"
            onClick={handleSend}
            disabled={isStreaming || !input.trim()}
          >
            {isStreaming ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
          </Button>
        </div>
        <p className="text-[10px] text-center mt-2 text-muted-foreground uppercase tracking-widest font-semibold">
          Veyra | Powered by Gemini 2.0 & LangGraph
        </p>
      </div>
    </div>
  );
};

export default ChatWorkspace;

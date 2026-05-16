import React from 'react';
import { useWorkflowStore } from '@/store/useWorkflowStore';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, CheckCircle2, Search, FileText, Layout, Play, Terminal } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const AgentIcon = ({ name }: { name: string }) => {
  switch (name) {
    case 'planning': return <Layout size={16} />;
    case 'research': return <Search size={16} />;
    case 'report': return <FileText size={16} />;
    case 'supervisor': return <Play size={16} />;
    default: return <Terminal size={16} />;
  }
};

const AgentActivityTimeline: React.FC = () => {
  const { activeWorkflow } = useWorkflowStore();

  if (!activeWorkflow) return null;

  return (
    <div className="space-y-4">
      <AnimatePresence mode="popLayout">
        {activeWorkflow.findings.map((finding, idx) => (
          <motion.div
            key={`finding-${idx}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-end"
          >
            <Card className="max-w-[90%] border-primary/20 bg-primary/5">
              <CardContent className="p-4 space-y-2">
                <div className="flex items-center gap-2 text-xs font-semibold text-primary uppercase tracking-tight">
                  <AgentIcon name={finding.agent} />
                  {finding.agent} Agent
                </div>
                <h3 className="text-sm font-bold">{finding.title}</h3>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
                  {finding.content}
                </p>
              </CardContent>
            </Card>
          </motion.div>
        ))}

        {activeWorkflow.active_agent && (
          <motion.div
            key="active-agent"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex justify-center py-4"
          >
            <div className="flex items-center gap-3 px-4 py-2 bg-muted rounded-full border border-border animate-pulse shadow-sm">
              <Loader2 className="animate-spin text-primary" size={16} />
              <span className="text-xs font-medium uppercase tracking-wider">
                {activeWorkflow.active_agent} Agent is reasoning...
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AgentActivityTimeline;

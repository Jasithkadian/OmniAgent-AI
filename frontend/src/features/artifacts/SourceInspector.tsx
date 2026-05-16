import React from 'react';
import { useWorkflowStore } from '@/store/useWorkflowStore';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FileText, ExternalLink, Quote } from 'lucide-react';

const SourceInspector: React.FC = () => {
  const { activeWorkflow } = useWorkflowStore();

  if (!activeWorkflow || activeWorkflow.findings.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-muted-foreground">
        <Database size={48} className="mb-4 opacity-20" />
        <p className="text-sm font-medium">No sources retrieved yet.</p>
        <p className="text-xs">Once the Research Agent starts, retrieved context will appear here.</p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-4">
        {activeWorkflow.findings.map((finding, idx) => (
          <Card key={`source-${idx}`} className="border-border/40 overflow-hidden shadow-sm">
            <CardHeader className="p-3 bg-muted/30">
              <div className="flex items-center justify-between">
                <Badge variant="outline" className="text-[10px] uppercase font-bold tracking-tight">
                  {finding.agent}
                </Badge>
                <span className="text-[10px] text-muted-foreground font-medium">
                  {Math.round(finding.confidence * 100)}% Confidence
                </span>
              </div>
              <CardTitle className="text-sm mt-1 leading-tight">{finding.title}</CardTitle>
            </CardHeader>
            <CardContent className="p-3 space-y-2">
              <div className="relative">
                <Quote size={12} className="absolute -left-1 -top-1 text-primary opacity-20" />
                <p className="text-xs text-muted-foreground line-clamp-4 pl-3">
                  {finding.content}
                </p>
              </div>
              {finding.citations && finding.citations.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-2">
                  {finding.citations.map((cite, cIdx) => (
                    <Badge key={cIdx} variant="secondary" className="text-[9px] h-4">
                      {cite}
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
};

import { Database } from 'lucide-react';

export default SourceInspector;

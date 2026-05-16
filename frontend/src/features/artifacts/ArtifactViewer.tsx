import React from 'react';
import { useWorkflowStore } from '@/store/useWorkflowStore';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileText, Download, Copy, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Button } from '@/components/ui/button';

const ArtifactViewer: React.FC = () => {
  const { activeWorkflow } = useWorkflowStore();
  const [copied, setCopied] = React.useState(false);

  const finalReport = activeWorkflow?.artifacts?.final_report;

  if (!finalReport) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-muted-foreground">
        <FileText size={48} className="mb-4 opacity-20" />
        <p className="text-sm font-medium">No artifacts generated yet.</p>
        <p className="text-xs">The Final Report will appear here once the Report Agent completes its task.</p>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(finalReport);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-border flex items-center justify-between bg-muted/10">
        <h3 className="text-xs font-bold uppercase tracking-widest flex items-center gap-2">
          <FileText size={14} />
          Technical Report
        </h3>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleCopy}>
            {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <Download size={14} />
          </Button>
        </div>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-6 prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown>{finalReport}</ReactMarkdown>
        </div>
      </ScrollArea>
    </div>
  );
};

export default ArtifactViewer;

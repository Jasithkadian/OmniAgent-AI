import React from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Plus, MessageSquare, Files, Settings } from 'lucide-react';
import DocumentUpload from '@/features/uploads/DocumentUpload';

const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 h-full bg-muted/30 flex flex-col shrink-0">
      <div className="p-4 border-b border-border">
        <Button className="w-full justify-start gap-2" variant="outline">
          <Plus size={16} />
          New Workflow
        </Button>
      </div>
      
      <ScrollArea className="flex-1">
        <div className="p-2 flex flex-col gap-1">
          <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Conversations
          </div>
          <Button variant="ghost" className="w-full justify-start gap-2 text-sm">
            <MessageSquare size={16} />
            AI Research Task
          </Button>
        </div>
      </ScrollArea>

      <div className="mt-auto px-4 py-4 flex flex-col gap-2 border-t border-border">
        <DocumentUpload />
        <Button variant="ghost" className="w-full justify-start gap-2 text-sm">
          <Settings size={16} />
          Settings
        </Button>
      </div>
    </aside>
  );
};

export default Sidebar;

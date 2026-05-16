import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Info, Database, FileText } from 'lucide-react';
import SourceInspector from '@/features/artifacts/SourceInspector';
import ArtifactViewer from '@/features/artifacts/ArtifactViewer';

const RightPanel: React.FC = () => {
  return (
    <aside className="w-80 h-full bg-card border-l border-border flex flex-col shrink-0">
      <Tabs defaultValue="sources" className="flex flex-col h-full">
        <div className="px-4 pt-4 border-b border-border bg-muted/20">
          <TabsList className="w-full grid grid-cols-2 mb-2">
            <TabsTrigger value="sources" className="gap-2">
              <Database size={14} />
              Sources
            </TabsTrigger>
            <TabsTrigger value="artifacts" className="gap-2">
              <FileText size={14} />
              Artifacts
            </TabsTrigger>
          </TabsList>
        </div>
        
        <div className="flex-1 overflow-hidden">
          <TabsContent value="sources" className="h-full m-0">
            <SourceInspector />
          </TabsContent>
          <TabsContent value="artifacts" className="h-full m-0">
            <ArtifactViewer />
          </TabsContent>
        </div>
      </Tabs>
    </aside>
  );
};

export default RightPanel;

import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/toaster';
import MainLayout from '@/layouts/MainLayout';
import ChatWorkspace from '@/features/chat/ChatWorkspace';
import Sidebar from '@/components/layout/Sidebar';
import RightPanel from '@/components/layout/RightPanel';
import { useWorkflowStore } from '@/store/useWorkflowStore';

const queryClient = new QueryClient();

function App() {
  const { activeWorkflow } = useWorkflowStore();

  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex h-screen w-full bg-background text-foreground overflow-hidden">
        <Sidebar />
        <main className="flex-1 flex flex-col relative overflow-hidden">
          <MainLayout>
            <ChatWorkspace />
          </MainLayout>
        </main>
        <RightPanel />
      </div>
      <Toaster />
    </QueryClientProvider>
  );
}

export default App;

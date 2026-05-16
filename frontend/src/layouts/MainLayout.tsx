import React from 'react';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden border-x border-border">
      <header className="h-14 border-b border-border flex items-center px-6 bg-card shrink-0">
        <h1 className="text-lg font-semibold tracking-tight">Veyra Workspace</h1>
      </header>
      <div className="flex-1 overflow-hidden relative">
        {children}
      </div>
    </div>
  );
};

export default MainLayout;

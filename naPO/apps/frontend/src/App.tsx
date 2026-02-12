import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import AppLayout from '@/components/layout/AppLayout';
import Dashboard from '@/pages/Dashboard';
import Settings from '@/pages/Settings';
import { ChatPanel } from '@/components/chat/ChatPanel';
import { useAppStore } from '@/stores/appStore';
import '@/styles/globals.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
});

export default function App() {
  const { currentView } = useAppStore();

  return (
    <QueryClientProvider client={queryClient}>
      <AppLayout>
        {currentView === 'chat' && <ChatPanel />}
        {currentView === 'data' && <Dashboard />}
        {currentView === 'settings' && <Settings />}
        {!['chat', 'data', 'settings'].includes(currentView) && <ChatPanel />}
      </AppLayout>

      <Toaster
        position="top-center"
        toastOptions={{
          duration: 3000,
          style: {
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            border: '2px solid var(--border-color)',
            fontFamily: 'var(--font-family-base)',
            fontSize: '0.875rem',
          },
        }}
      />
    </QueryClientProvider>
  );
}

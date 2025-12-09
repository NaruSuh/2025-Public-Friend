import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import AppLayout from '@/components/layout/AppLayout';
import Dashboard from '@/pages/Dashboard';
import History from '@/pages/History';
import Settings from '@/pages/Settings';
import ApiSources from '@/pages/ApiSources';
import { useAppStore } from '@/stores/appStore';
import '@/styles/globals.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

export default function App() {
  const { currentView } = useAppStore();

  return (
    <QueryClientProvider client={queryClient}>
      <AppLayout>
        {currentView === 'dashboard' && <Dashboard />}
        {currentView === 'history' && <History />}
        {currentView === 'settings' && <Settings />}
        {currentView === '/sources/api' && <ApiSources />}
        {!['dashboard', 'history', 'settings', '/sources/api'].includes(currentView) && (
          <Dashboard />
        )}
      </AppLayout>

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-color)',
          },
          success: {
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
    </QueryClientProvider>
  );
}

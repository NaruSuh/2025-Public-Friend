import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AppState {
  // Theme
  theme: 'light' | 'dark';
  toggleTheme: () => void;

  // Left Navigation
  leftNavOpen: boolean;
  leftNavCollapsed: boolean;
  toggleLeftNav: () => void;
  collapseLeftNav: () => void;

  // Right Navigation
  rightNavOpen: boolean;
  toggleRightNav: () => void;

  // Current View
  currentView: string;
  setCurrentView: (view: string) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // Theme
      theme: 'light',
      toggleTheme: () =>
        set((state) => ({
          theme: state.theme === 'light' ? 'dark' : 'light',
        })),

      // Left Navigation
      leftNavOpen: true,
      leftNavCollapsed: false,
      toggleLeftNav: () => set((state) => ({ leftNavOpen: !state.leftNavOpen })),
      collapseLeftNav: () => set((state) => ({ leftNavCollapsed: !state.leftNavCollapsed })),

      // Right Navigation
      rightNavOpen: true,
      toggleRightNav: () => set((state) => ({ rightNavOpen: !state.rightNavOpen })),

      // Current View
      currentView: 'dashboard',
      setCurrentView: (view) => set({ currentView: view }),
    }),
    {
      name: 'napo-app-store',
    }
  )
);

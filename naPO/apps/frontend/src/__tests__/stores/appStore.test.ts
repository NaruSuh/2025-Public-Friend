import { describe, it, expect, beforeEach } from 'vitest';
import { act } from '@testing-library/react';
import { useAppStore } from '@/stores/appStore';

describe('AppStore', () => {
  beforeEach(() => {
    // Clear localStorage to reset persist state
    localStorage.clear();

    // Reset store to initial state by calling setState directly
    useAppStore.setState({
      theme: 'light',
      leftNavOpen: true,
      leftNavCollapsed: false,
      rightNavOpen: true,
      currentView: 'dashboard',
    });
  });

  describe('Theme', () => {
    it('should have default theme as light', () => {
      const { theme } = useAppStore.getState();
      expect(theme).toBe('light');
    });

    it('should toggle theme from light to dark', () => {
      const { toggleTheme } = useAppStore.getState();

      act(() => {
        toggleTheme();
      });

      expect(useAppStore.getState().theme).toBe('dark');
    });

    it('should toggle theme from dark to light', () => {
      const { toggleTheme } = useAppStore.getState();

      // First toggle to dark
      act(() => {
        toggleTheme();
      });

      // Then toggle back to light
      act(() => {
        toggleTheme();
      });

      expect(useAppStore.getState().theme).toBe('light');
    });
  });

  describe('Navigation', () => {
    it('should have left nav open by default', () => {
      const { leftNavOpen } = useAppStore.getState();
      expect(leftNavOpen).toBe(true);
    });

    it('should toggle left navigation', () => {
      const { toggleLeftNav } = useAppStore.getState();

      act(() => {
        toggleLeftNav();
      });

      expect(useAppStore.getState().leftNavOpen).toBe(false);
    });

    it('should have right nav open by default', () => {
      const { rightNavOpen } = useAppStore.getState();
      expect(rightNavOpen).toBe(true);
    });

    it('should toggle right navigation', () => {
      const { toggleRightNav } = useAppStore.getState();

      act(() => {
        toggleRightNav();
      });

      expect(useAppStore.getState().rightNavOpen).toBe(false);
    });

    it('should collapse left navigation', () => {
      const { collapseLeftNav, leftNavCollapsed } = useAppStore.getState();
      expect(leftNavCollapsed).toBe(false);

      act(() => {
        collapseLeftNav();
      });

      expect(useAppStore.getState().leftNavCollapsed).toBe(true);
    });
  });

  describe('Current View', () => {
    it('should have dashboard as default view', () => {
      const { currentView } = useAppStore.getState();
      expect(currentView).toBe('dashboard');
    });

    it('should set current view', () => {
      const { setCurrentView } = useAppStore.getState();

      act(() => {
        setCurrentView('history');
      });

      expect(useAppStore.getState().currentView).toBe('history');
    });

    it('should allow setting any view name', () => {
      const { setCurrentView } = useAppStore.getState();

      act(() => {
        setCurrentView('settings');
      });

      expect(useAppStore.getState().currentView).toBe('settings');
    });
  });
});

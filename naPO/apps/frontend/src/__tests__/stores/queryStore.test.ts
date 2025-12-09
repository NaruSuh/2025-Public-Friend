import { describe, it, expect, beforeEach } from 'vitest';
import { act } from '@testing-library/react';
import { useQueryStore } from '@/stores/queryStore';

describe('QueryStore', () => {
  beforeEach(() => {
    // Reset store to initial state
    act(() => {
      useQueryStore.getState().setCurrentQuery('');
      useQueryStore.getState().setParsedQuery(null);
      useQueryStore.getState().clearHistory();
      useQueryStore.getState().setQueryError(null);
      useQueryStore.getState().setQueryResult(null);
      useQueryStore.getState().clearDebugInfo();
    });
  });

  describe('Current Query', () => {
    it('should have empty string as default query', () => {
      const { currentQuery } = useQueryStore.getState();
      expect(currentQuery).toBe('');
    });

    it('should set current query', () => {
      const { setCurrentQuery } = useQueryStore.getState();

      act(() => {
        setCurrentQuery('2022년 지방선거 공약 조회');
      });

      expect(useQueryStore.getState().currentQuery).toBe('2022년 지방선거 공약 조회');
    });
  });

  describe('Parsed Query', () => {
    it('should have null as default parsed query', () => {
      const { parsedQuery } = useQueryStore.getState();
      expect(parsedQuery).toBeNull();
    });

    it('should set parsed query', () => {
      const { setParsedQuery } = useQueryStore.getState();
      const testParsed = {
        intent: 'search_pledges',
        entities: { year: '2022', election: 'local' },
      };

      act(() => {
        setParsedQuery(testParsed as any);
      });

      expect(useQueryStore.getState().parsedQuery).toEqual(testParsed);
    });
  });

  describe('Query History', () => {
    it('should have empty history by default', () => {
      const { queryHistory } = useQueryStore.getState();
      expect(queryHistory).toEqual([]);
    });

    it('should add query to history', () => {
      const { addToHistory } = useQueryStore.getState();

      act(() => {
        addToHistory('test query');
      });

      const { queryHistory } = useQueryStore.getState();
      expect(queryHistory.length).toBe(1);
      expect(queryHistory[0].query).toBe('test query');
      expect(queryHistory[0].timestamp).toBeDefined();
    });

    it('should add multiple queries to history in reverse order', () => {
      const { addToHistory } = useQueryStore.getState();

      act(() => {
        addToHistory('first query');
        addToHistory('second query');
        addToHistory('third query');
      });

      const { queryHistory } = useQueryStore.getState();
      expect(queryHistory.length).toBe(3);
      expect(queryHistory[0].query).toBe('third query');
      expect(queryHistory[2].query).toBe('first query');
    });

    it('should limit history to 50 items', () => {
      const { addToHistory } = useQueryStore.getState();

      act(() => {
        for (let i = 0; i < 60; i++) {
          addToHistory(`query ${i}`);
        }
      });

      const { queryHistory } = useQueryStore.getState();
      expect(queryHistory.length).toBe(50);
      expect(queryHistory[0].query).toBe('query 59');
    });

    it('should clear history', () => {
      const { addToHistory, clearHistory } = useQueryStore.getState();

      act(() => {
        addToHistory('test query');
        clearHistory();
      });

      expect(useQueryStore.getState().queryHistory).toEqual([]);
    });
  });

  describe('Loading State', () => {
    it('should have false as default parsing state', () => {
      const { isParsingQuery } = useQueryStore.getState();
      expect(isParsingQuery).toBe(false);
    });

    it('should set parsing state', () => {
      const { setIsParsingQuery } = useQueryStore.getState();

      act(() => {
        setIsParsingQuery(true);
      });

      expect(useQueryStore.getState().isParsingQuery).toBe(true);
    });
  });

  describe('Query Error', () => {
    it('should have null as default error', () => {
      const { queryError } = useQueryStore.getState();
      expect(queryError).toBeNull();
    });

    it('should set query error', () => {
      const { setQueryError } = useQueryStore.getState();

      act(() => {
        setQueryError('API call failed');
      });

      expect(useQueryStore.getState().queryError).toBe('API call failed');
    });

    it('should clear error by setting to null', () => {
      const { setQueryError } = useQueryStore.getState();

      act(() => {
        setQueryError('Error');
        setQueryError(null);
      });

      expect(useQueryStore.getState().queryError).toBeNull();
    });
  });

  describe('Debug Info', () => {
    it('should have null as default debug info', () => {
      const { debugInfo } = useQueryStore.getState();
      expect(debugInfo).toBeNull();
    });

    it('should set debug info', () => {
      const { setDebugInfo } = useQueryStore.getState();
      const testDebug = {
        parseDuration: 100,
        apiCallDuration: 200,
      };

      act(() => {
        setDebugInfo(testDebug as any);
      });

      expect(useQueryStore.getState().debugInfo).toEqual(testDebug);
    });

    it('should update debug info partially', () => {
      const { setDebugInfo, updateDebugInfo } = useQueryStore.getState();
      const initialDebug = { parseDuration: 100 };

      act(() => {
        setDebugInfo(initialDebug as any);
        updateDebugInfo({ apiCallDuration: 200 } as any);
      });

      expect(useQueryStore.getState().debugInfo).toEqual({
        parseDuration: 100,
        apiCallDuration: 200,
      });
    });

    it('should clear debug info', () => {
      const { setDebugInfo, clearDebugInfo } = useQueryStore.getState();

      act(() => {
        setDebugInfo({ parseDuration: 100 } as any);
        clearDebugInfo();
      });

      expect(useQueryStore.getState().debugInfo).toBeNull();
    });
  });
});

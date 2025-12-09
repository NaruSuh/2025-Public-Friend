import { create } from 'zustand';
import { ParsedQuery, DebugInfo } from '@/types';

interface QueryState {
  // Current Query
  currentQuery: string;
  setCurrentQuery: (query: string) => void;

  // Parsed Query
  parsedQuery: ParsedQuery | null;
  setParsedQuery: (parsed: ParsedQuery | null) => void;

  // Query History
  queryHistory: Array<{
    query: string;
    timestamp: string;
    parsedQuery?: ParsedQuery;
    debugInfo?: DebugInfo;
  }>;
  addToHistory: (query: string, parsed?: ParsedQuery, debug?: DebugInfo) => void;
  clearHistory: () => void;

  // Loading State
  isParsingQuery: boolean;
  setIsParsingQuery: (loading: boolean) => void;

  // Results
  queryResult: any;
  setQueryResult: (result: any) => void;

  // Error
  queryError: string | null;
  setQueryError: (error: string | null) => void;

  // Debug / Observability
  debugInfo: DebugInfo | null;
  setDebugInfo: (info: DebugInfo | null) => void;
  updateDebugInfo: (partial: Partial<DebugInfo>) => void;
  clearDebugInfo: () => void;
}

export const useQueryStore = create<QueryState>((set) => ({
  // Current Query
  currentQuery: '',
  setCurrentQuery: (query) => set({ currentQuery: query }),

  // Parsed Query
  parsedQuery: null,
  setParsedQuery: (parsed) => set({ parsedQuery: parsed }),

  // Query History
  queryHistory: [],
  addToHistory: (query, parsed, debug) =>
    set((state) => ({
      queryHistory: [
        { query, timestamp: new Date().toISOString(), parsedQuery: parsed, debugInfo: debug },
        ...state.queryHistory.slice(0, 49), // Keep last 50
      ],
    })),
  clearHistory: () => set({ queryHistory: [] }),

  // Loading State
  isParsingQuery: false,
  setIsParsingQuery: (loading) => set({ isParsingQuery: loading }),

  // Results
  queryResult: null,
  setQueryResult: (result) => set({ queryResult: result }),

  // Error
  queryError: null,
  setQueryError: (error) => set({ queryError: error }),

  // Debug / Observability
  debugInfo: null,
  setDebugInfo: (info) => set({ debugInfo: info }),
  updateDebugInfo: (partial) =>
    set((state) => ({
      debugInfo: state.debugInfo ? { ...state.debugInfo, ...partial } : partial,
    })),
  clearDebugInfo: () => set({ debugInfo: null }),
}));

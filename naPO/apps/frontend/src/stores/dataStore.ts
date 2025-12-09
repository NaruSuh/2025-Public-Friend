import { create } from 'zustand';
import { ApiSource, CrawlerSite, DataJob, ParserInfo } from '@/types';

interface DataState {
  // API Sources
  apiSources: ApiSource[];
  setApiSources: (sources: ApiSource[]) => void;

  // Crawler Sites
  crawlerSites: CrawlerSite[];
  setCrawlerSites: (sites: CrawlerSite[]) => void;

  // Available Parsers
  parsers: ParserInfo[];
  setParsers: (parsers: ParserInfo[]) => void;
  selectedParser: string | null;
  setSelectedParser: (parserId: string | null) => void;

  // Current Data
  currentData: any[];
  setCurrentData: (data: any[]) => void;

  // Jobs
  jobs: DataJob[];
  setJobs: (jobs: DataJob[]) => void;
  addJob: (job: DataJob) => void;
  updateJob: (id: string, updates: Partial<DataJob>) => void;

  // Selected Items
  selectedRows: string[];
  setSelectedRows: (rows: string[]) => void;
  toggleRowSelection: (rowId: string) => void;
  clearSelection: () => void;
}

export const useDataStore = create<DataState>((set) => ({
  // API Sources
  apiSources: [],
  setApiSources: (sources) => set({ apiSources: sources }),

  // Crawler Sites
  crawlerSites: [],
  setCrawlerSites: (sites) => set({ crawlerSites: sites }),

  // Available Parsers
  parsers: [],
  setParsers: (parsers) => set({ parsers: parsers }),
  selectedParser: null,
  setSelectedParser: (parserId) => set({ selectedParser: parserId }),

  // Current Data
  currentData: [],
  setCurrentData: (data) => set({ currentData: data }),

  // Jobs
  jobs: [],
  setJobs: (jobs) => set({ jobs: jobs }),
  addJob: (job) => set((state) => ({ jobs: [job, ...state.jobs] })),
  updateJob: (id, updates) =>
    set((state) => ({
      jobs: state.jobs.map((j) => (j.id === id ? { ...j, ...updates } : j)),
    })),

  // Selected Items
  selectedRows: [],
  setSelectedRows: (rows) => set({ selectedRows: rows }),
  toggleRowSelection: (rowId) =>
    set((state) => ({
      selectedRows: state.selectedRows.includes(rowId)
        ? state.selectedRows.filter((id) => id !== rowId)
        : [...state.selectedRows, rowId],
    })),
  clearSelection: () => set({ selectedRows: [] }),
}));

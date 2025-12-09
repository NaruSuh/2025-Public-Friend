import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useExport } from '@/hooks/useExport';
import * as XLSX from 'xlsx';
import * as FileSaver from 'file-saver';

// Mock xlsx and file-saver
vi.mock('xlsx');
vi.mock('file-saver', () => ({
  saveAs: vi.fn(),
}));

const saveAs = FileSaver.saveAs;

describe('useExport', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('exportToExcel', () => {
    it('should export data to Excel file', () => {
      const { result } = renderHook(() => useExport());
      const mockData = [
        { id: 1, name: 'Test 1', value: 100 },
        { id: 2, name: 'Test 2', value: 200 },
      ];

      const mockWorkbook = { SheetNames: [], Sheets: {} };
      const mockWorksheet = {};

      vi.mocked(XLSX.utils.book_new).mockReturnValue(mockWorkbook as any);
      vi.mocked(XLSX.utils.json_to_sheet).mockReturnValue(mockWorksheet as any);
      vi.mocked(XLSX.write).mockReturnValue(new ArrayBuffer(0) as any);

      act(() => {
        result.current.exportToExcel(mockData);
      });

      expect(XLSX.utils.book_new).toHaveBeenCalled();
      expect(XLSX.utils.json_to_sheet).toHaveBeenCalledWith(mockData);
      expect(XLSX.utils.book_append_sheet).toHaveBeenCalled();
      expect(saveAs).toHaveBeenCalled();
    });

    it('should not export when data is empty', () => {
      const { result } = renderHook(() => useExport());
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      act(() => {
        result.current.exportToExcel([]);
      });

      expect(consoleErrorSpy).toHaveBeenCalledWith('No data to export');
      expect(XLSX.utils.book_new).not.toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });

    it('should use custom filename when provided', () => {
      const { result } = renderHook(() => useExport());
      const mockData = [{ id: 1, name: 'Test' }];
      const customFilename = 'custom-export.xlsx';

      const mockWorkbook = { SheetNames: [], Sheets: {} };
      const mockWorksheet = {};

      vi.mocked(XLSX.utils.book_new).mockReturnValue(mockWorkbook as any);
      vi.mocked(XLSX.utils.json_to_sheet).mockReturnValue(mockWorksheet as any);
      vi.mocked(XLSX.write).mockReturnValue(new ArrayBuffer(0) as any);

      act(() => {
        result.current.exportToExcel(mockData, customFilename);
      });

      expect(saveAs).toHaveBeenCalledWith(expect.any(Blob), customFilename);
    });
  });

  describe('exportToCSV', () => {
    it('should export data to CSV file', () => {
      const { result } = renderHook(() => useExport());
      const mockData = [
        { id: 1, name: 'Test 1', value: 100 },
        { id: 2, name: 'Test 2', value: 200 },
      ];

      act(() => {
        result.current.exportToCSV(mockData);
      });

      expect(saveAs).toHaveBeenCalled();
      const blob = vi.mocked(saveAs).mock.calls[0][0] as Blob;
      expect(blob.type).toBe('text/csv;charset=utf-8;');
    });
  });

  describe('exportToJSON', () => {
    it('should export data to JSON file', () => {
      const { result } = renderHook(() => useExport());
      const mockData = [
        { id: 1, name: 'Test 1', value: 100 },
        { id: 2, name: 'Test 2', value: 200 },
      ];

      act(() => {
        result.current.exportToJSON(mockData);
      });

      expect(saveAs).toHaveBeenCalled();
      const blob = vi.mocked(saveAs).mock.calls[0][0] as Blob;
      expect(blob.type).toMatch(/application\/json/);
    });
  });

  describe('isExporting state', () => {
    it('should track exporting state correctly', async () => {
      const { result } = renderHook(() => useExport());
      const mockData = [{ id: 1, name: 'Test' }];

      expect(result.current.isExporting).toBe(false);

      const mockWorkbook = { SheetNames: [], Sheets: {} };
      const mockWorksheet = {};

      vi.mocked(XLSX.utils.book_new).mockReturnValue(mockWorkbook as any);
      vi.mocked(XLSX.utils.json_to_sheet).mockReturnValue(mockWorksheet as any);
      vi.mocked(XLSX.write).mockReturnValue(new ArrayBuffer(0) as any);

      act(() => {
        result.current.exportToExcel(mockData);
      });

      // After export completes, should be false again
      expect(result.current.isExporting).toBe(false);
    });
  });
});

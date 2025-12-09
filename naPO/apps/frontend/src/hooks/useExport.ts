/**
 * 데이터 내보내기 Hook
 *
 * CSV, JSON, Excel 형식으로 데이터를 내보내는 기능을 제공합니다.
 * 중첩된 객체와 배열을 자동으로 평면화하여 내보냅니다.
 *
 * @module hooks/useExport
 *
 * @example
 * ```tsx
 * function DataTable({ data }) {
 *   const { exportToCSV, exportToExcel, isExporting } = useExport();
 *
 *   return (
 *     <div>
 *       <button onClick={() => exportToCSV(data)} disabled={isExporting}>
 *         Export CSV
 *       </button>
 *       <button onClick={() => exportToExcel(data, 'my-data.xlsx')}>
 *         Export Excel
 *       </button>
 *     </div>
 *   );
 * }
 * ```
 */
import { useCallback, useState } from 'react';
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import { format } from 'date-fns';

/**
 * 중첩된 데이터를 CSV/Excel 내보내기에 적합하게 평면화합니다.
 * 특히 정당 공약 데이터의 중첩된 policies 배열을 행으로 변환합니다.
 *
 * @param data - 평면화할 데이터 배열
 * @returns 평면화된 데이터 배열
 */
function flattenPartyPolicyData(data: any[]): any[] {
  const flattened: any[] = [];

  for (const item of data) {
    // Check if this is party policy data with nested policies array
    if (item.partyName && item.policies && Array.isArray(item.policies)) {
      for (const policy of item.policies) {
        flattened.push({
          electionId: item.electionId || '',
          partyName: item.partyName,
          policyOrder: policy.order || '',
          policyRealm: policy.realm || '',
          policyTitle: policy.title || '',
          policyContent: policy.content || item._raw?.[`prmmCont${policy.order}`] || '',
        });
      }
    } else {
      // For other data, flatten any nested objects
      const flatItem: any = {};
      for (const [key, value] of Object.entries(item)) {
        if (value && typeof value === 'object' && !Array.isArray(value)) {
          // Flatten nested object
          for (const [nestedKey, nestedValue] of Object.entries(value as object)) {
            flatItem[`${key}_${nestedKey}`] = nestedValue;
          }
        } else if (Array.isArray(value)) {
          // Convert array to JSON string
          flatItem[key] = JSON.stringify(value);
        } else {
          flatItem[key] = value;
        }
      }
      flattened.push(flatItem);
    }
  }

  return flattened.length > 0 ? flattened : data;
}

/**
 * 데이터 내보내기 기능을 제공하는 React Hook
 *
 * @returns 내보내기 함수들과 상태
 * @property exportToCSV - CSV 형식으로 내보내기
 * @property exportToJSON - JSON 형식으로 내보내기
 * @property exportToExcel - Excel(xlsx) 형식으로 내보내기
 * @property isExporting - 현재 내보내기 진행 중 여부
 */
export function useExport() {
  const [isExporting, setIsExporting] = useState(false);

  /**
   * 데이터를 CSV 파일로 내보냅니다.
   * @param data - 내보낼 데이터 배열
   * @param fileName - 파일명 (선택, 기본: napo-export-YYYYMMDD-HHmmss.csv)
   */
  const exportToCSV = useCallback((data: any[], fileName?: string) => {
    if (!data || data.length === 0) {
      console.error('No data to export');
      return;
    }

    setIsExporting(true);

    try {
      // Flatten nested data for CSV export
      const flatData = flattenPartyPolicyData(data);
      const headers = Object.keys(flatData[0]);
      const csvContent = [
        headers.join(','), // Header row
        ...flatData.map((row) =>
          headers
            .map((header) => {
              const value = row[header];
              // Escape commas, quotes, and newlines
              if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
                return `"${value.replace(/"/g, '""').replace(/\n/g, ' ')}"`;
              }
              return value ?? '';
            })
            .join(',')
        ),
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const filename = fileName || `napo-export-${format(new Date(), 'yyyyMMdd-HHmmss')}.csv`;
      saveAs(blob, filename);

      console.log(`✅ Exported ${flatData.length} rows to CSV`);
    } catch (error) {
      console.error('❌ CSV export failed:', error);
    } finally {
      setIsExporting(false);
    }
  }, []);

  const exportToJSON = useCallback((data: any[], fileName?: string) => {
    if (!data || data.length === 0) {
      console.error('No data to export');
      return;
    }

    setIsExporting(true);

    try {
      const jsonString = JSON.stringify(data, null, 2);
      const blob = new Blob([jsonString], { type: 'application/json' });
      const filename = fileName || `napo-export-${format(new Date(), 'yyyyMMdd-HHmmss')}.json`;
      saveAs(blob, filename);

      console.log(`✅ Exported ${data.length} rows to JSON`);
    } catch (error) {
      console.error('❌ JSON export failed:', error);
    } finally {
      setIsExporting(false);
    }
  }, []);

  const exportToExcel = useCallback((data: any[], fileName?: string) => {
    if (!data || data.length === 0) {
      console.error('No data to export');
      return;
    }

    setIsExporting(true);

    try {
      // Flatten nested data for Excel export
      const flatData = flattenPartyPolicyData(data);

      // Create workbook
      const wb = XLSX.utils.book_new();

      // Convert JSON to worksheet
      const ws = XLSX.utils.json_to_sheet(flatData);

      // Auto-size columns (cap at 50 chars to avoid extremely wide columns)
      const colWidths = Object.keys(flatData[0]).map((key) => ({
        wch: Math.min(50, Math.max(key.length, ...flatData.map((row) => String(row[key] || '').substring(0, 50).length)) + 2),
      }));
      ws['!cols'] = colWidths;

      // Add worksheet to workbook
      XLSX.utils.book_append_sheet(wb, ws, 'Data');

      // Generate Excel file
      const excelBuffer = XLSX.write(wb, {
        bookType: 'xlsx',
        type: 'array',
      });

      // Create blob and download
      const blob = new Blob([excelBuffer], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      const filename = fileName || `napo-export-${format(new Date(), 'yyyyMMdd-HHmmss')}.xlsx`;
      saveAs(blob, filename);

      console.log(`✅ Exported ${flatData.length} rows to Excel`);
    } catch (error) {
      console.error('❌ Excel export failed:', error);
    } finally {
      setIsExporting(false);
    }
  }, []);

  return {
    exportToCSV,
    exportToJSON,
    exportToExcel,
    isExporting,
  };
}

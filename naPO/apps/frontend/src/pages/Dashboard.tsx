import React from 'react';
import { useQueryStore } from '@/stores/queryStore';
import { useDataStore } from '@/stores/dataStore';
import { DataTable } from '@/components/data/DataTable';
import { QueryDebugPanel } from '@/components/debug/QueryDebugPanel';
import { useExport } from '@/hooks/useExport';
import { Download, FileJson, FileSpreadsheet } from 'lucide-react';
import styles from './Dashboard.module.css';

export default function Dashboard() {
  const { queryResult, parsedQuery } = useQueryStore();
  const { currentData, setCurrentData } = useDataStore();
  const { exportToCSV, exportToJSON, exportToExcel, isExporting } = useExport();

  // Update currentData when queryResult changes
  React.useEffect(() => {
    if (queryResult?.data) {
      try {
        // Handle nested response structure: queryResult.data.data or queryResult.data
        let extractedData = queryResult.data;

        // If data has a nested 'data' property (API response wrapper), extract it
        if (extractedData && typeof extractedData === 'object' && !Array.isArray(extractedData)) {
          if ('data' in extractedData && Array.isArray(extractedData.data)) {
            extractedData = extractedData.data;
          } else if ('success' in extractedData && 'data' in extractedData) {
            // Handle {success: true, totalCount: N, data: [...]} format
            extractedData = extractedData.data;
          }
        }

        const data = Array.isArray(extractedData) ? extractedData : [extractedData];
        // Filter out null/undefined values
        const validData = data.filter((item) => item != null && typeof item === 'object');
        setCurrentData(validData);
      } catch (error) {
        console.error('Error processing query result:', error);
        setCurrentData([]);
      }
    } else if (queryResult && !queryResult.data) {
      // Clear data if result exists but has no data
      setCurrentData([]);
    }
  }, [queryResult, setCurrentData]);

  // Auto-generate columns from data
  const columns = React.useMemo(() => {
    if (!currentData || !currentData.length) return [];

    try {
      const firstItem = currentData[0];
      if (!firstItem || typeof firstItem !== 'object') return [];

      // Skip internal/raw fields that are too verbose for display
      const skipFields = ['_raw', '_RAW'];

      return Object.keys(firstItem)
        .filter((key) => !skipFields.includes(key.toLowerCase()) && !skipFields.includes(key))
        .map((key) => ({
          accessorKey: key,
          header: key.toUpperCase(),
          cell: (info: any) => {
            const value = info.getValue();
            if (value === null || value === undefined) {
              return '';
            }
            if (Array.isArray(value)) {
              // For arrays, show count and brief summary
              if (value.length === 0) return '[]';
              const preview = value.length <= 2
                ? value.map((v) => (typeof v === 'object' ? (v.title || v.name || '...') : v)).join(', ')
                : `${value.length} items`;
              return `[${preview}]`;
            }
            if (typeof value === 'object') {
              // For objects, show brief representation
              const keys = Object.keys(value);
              if (keys.length === 0) return '{}';
              const preview = keys.slice(0, 2).join(', ');
              return `{${preview}${keys.length > 2 ? ', ...' : ''}}`;
            }
            // Truncate long strings
            const str = String(value);
            return str.length > 100 ? str.substring(0, 100) + '...' : str;
          },
        }));
    } catch (error) {
      console.error('Error generating columns:', error);
      return [];
    }
  }, [currentData]);

  return (
    <div className={styles.dashboard}>
      {/* Header */}
      <div className={styles.header}>
        <h2 className={styles.title}>DATA RESULTS</h2>

        {currentData.length > 0 && (
          <div className={styles.actions}>
            <button
              className={styles.exportBtn}
              onClick={() => exportToCSV(currentData)}
              disabled={isExporting}
            >
              <Download size={16} />
              CSV
            </button>
            <button
              className={styles.exportBtn}
              onClick={() => exportToJSON(currentData)}
              disabled={isExporting}
            >
              <FileJson size={16} />
              JSON
            </button>
            <button
              className={styles.exportBtn}
              onClick={() => exportToExcel(currentData)}
              disabled={isExporting}
            >
              <FileSpreadsheet size={16} />
              EXCEL
            </button>
          </div>
        )}
      </div>

      {/* Query Info */}
      {parsedQuery && (
        <div className={styles.queryInfo}>
          <div className={styles.queryInfoItem}>
            <span className={styles.label}>QUERY:</span>
            <span className={styles.value}>{parsedQuery.rawQuery}</span>
          </div>
          <div className={styles.queryInfoItem}>
            <span className={styles.label}>SOURCE:</span>
            <span className={styles.value}>
              {parsedQuery.source.id || parsedQuery.source.url || 'N/A'}
            </span>
          </div>
          <div className={styles.queryInfoItem}>
            <span className={styles.label}>RESULTS:</span>
            <span className={styles.value}>{currentData.length} rows</span>
          </div>
        </div>
      )}

      {/* Data Table */}
      {currentData.length > 0 ? (
        <DataTable data={currentData} columns={columns} />
      ) : (
        <div className={styles.emptyState}>
          <p>NO DATA</p>
          <span>자연어 쿼리를 입력하여 데이터를 가져오세요</span>
        </div>
      )}

      {/* Debug Panel */}
      <QueryDebugPanel />
    </div>
  );
}

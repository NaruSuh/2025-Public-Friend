import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DataTable } from '@/components/data/DataTable';
import { apiService } from '@/services/api';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import styles from './History.module.css';

export default function History() {
  const { setCurrentView } = useAppStore();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['queryHistory'],
    queryFn: async () => {
      const response = await apiService.getQueryHistory(100, 0);
      return response.data;
    },
  });

  const columns = useMemo(
    () => [
      {
        accessorKey: 'naturalQuery',
        header: 'QUERY',
        cell: (info: any) => <span className={styles.queryText}>{info.getValue()}</span>,
      },
      {
        accessorKey: 'parsedIntent',
        header: 'INTENT',
        cell: (info: any) => <span className={styles.intent}>{info.getValue()}</span>,
      },
      {
        accessorKey: 'resultCount',
        header: 'RESULTS',
        cell: (info: any) => {
          const value = info.getValue();
          return value !== null ? value : '-';
        },
      },
      {
        accessorKey: 'executionTimeMs',
        header: 'TIME (MS)',
        cell: (info: any) => {
          const value = info.getValue();
          return value !== null ? value : '-';
        },
      },
      {
        accessorKey: 'createdAt',
        header: 'CREATED AT',
        cell: (info: any) => {
          const date = new Date(info.getValue());
          return date.toLocaleString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
          });
        },
      },
    ],
    []
  );

  const historyItems = data?.items || [];

  return (
    <div className={styles.history}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.titleRow}>
          <button className={styles.backBtn} onClick={() => setCurrentView('dashboard')}>
            <ArrowLeft size={20} />
            <span>Back to Dashboard</span>
          </button>
          <h2 className={styles.title}>QUERY HISTORY</h2>
        </div>

        <div className={styles.actions}>
          <button className={styles.refreshBtn} onClick={() => refetch()} disabled={isLoading}>
            <RefreshCw size={16} className={isLoading ? styles.spinning : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className={styles.stats}>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>TOTAL QUERIES</span>
          <span className={styles.statValue}>{data?.total || 0}</span>
        </div>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>SHOWING</span>
          <span className={styles.statValue}>{historyItems.length}</span>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className={styles.emptyState}>
          <p>Loading history...</p>
        </div>
      ) : error ? (
        <div className={styles.emptyState}>
          <p>Error loading history</p>
          <span>{(error as Error).message}</span>
        </div>
      ) : historyItems.length > 0 ? (
        <DataTable data={historyItems} columns={columns} pageSize={20} />
      ) : (
        <div className={styles.emptyState}>
          <p>NO HISTORY</p>
          <span>쿼리를 실행하면 여기에 히스토리가 표시됩니다</span>
        </div>
      )}
    </div>
  );
}

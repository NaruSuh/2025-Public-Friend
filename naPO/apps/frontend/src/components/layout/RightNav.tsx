import {
  Settings,
  Download,
  Clock,
  Database,
  FileText,
  Trash2,
  CheckCircle,
  XCircle,
  Loader2,
} from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import { useDataStore } from '@/stores/dataStore';
import { useQueryStore } from '@/stores/queryStore';
import { useExport } from '@/hooks/useExport';
import styles from './RightNav.module.css';

export default function RightNav() {
  const { theme, toggleTheme } = useAppStore();
  const { currentData, jobs, selectedParser, setSelectedParser } = useDataStore();
  const { queryHistory, clearHistory } = useQueryStore();
  const { exportToCSV, exportToJSON, isExporting } = useExport();

  return (
    <nav className={styles.nav}>
      {/* Export Section */}
      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>
          <Download size={16} />
          EXPORT
        </h3>
        <div className={styles.sectionContent}>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Rows</span>
            <span className={styles.statValue}>{currentData.length}</span>
          </div>

          <div className={styles.exportButtons}>
            <button
              className={styles.btn}
              onClick={() => exportToCSV(currentData)}
              disabled={!currentData.length || isExporting}
            >
              Export CSV
            </button>
            <button
              className={styles.btn}
              onClick={() => exportToJSON(currentData)}
              disabled={!currentData.length || isExporting}
            >
              Export JSON
            </button>
          </div>
        </div>
      </section>

      {/* Parser Selection */}
      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>
          <FileText size={16} />
          PDF PARSER
        </h3>
        <div className={styles.sectionContent}>
          <select
            className={styles.select}
            value={selectedParser || ''}
            onChange={(e) => setSelectedParser(e.target.value || null)}
          >
            <option value="">Auto Select</option>
            <option value="pymupdf">PyMuPDF (Local)</option>
            <option value="clova_ocr">Clova OCR</option>
            <option value="google_vision">Google Vision</option>
            <option value="dolphin">Dolphin</option>
          </select>
        </div>
      </section>

      {/* Jobs Status */}
      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>
          <Database size={16} />
          RECENT JOBS
        </h3>
        <div className={styles.sectionContent}>
          {jobs.length === 0 ? (
            <p className={styles.emptyText}>No jobs yet</p>
          ) : (
            <ul className={styles.jobList}>
              {jobs.slice(0, 5).map((job) => (
                <li key={job.id} className={styles.jobItem}>
                  <span className={styles.jobStatus}>
                    {job.status === 'completed' && (
                      <CheckCircle size={14} className={styles.success} />
                    )}
                    {job.status === 'failed' && <XCircle size={14} className={styles.error} />}
                    {job.status === 'running' && <Loader2 size={14} className={styles.spinner} />}
                    {job.status === 'pending' && <Clock size={14} />}
                  </span>
                  <span className={styles.jobType}>{job.jobType}</span>
                  <span className={styles.jobCount}>{job.resultCount ?? '-'}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      {/* Query History */}
      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>
          <Clock size={16} />
          HISTORY
          {queryHistory.length > 0 && (
            <button className={styles.clearBtn} onClick={clearHistory} title="Clear history">
              <Trash2 size={12} />
            </button>
          )}
        </h3>
        <div className={styles.sectionContent}>
          {queryHistory.length === 0 ? (
            <p className={styles.emptyText}>No history</p>
          ) : (
            <ul className={styles.historyList}>
              {queryHistory.slice(0, 10).map((item, index) => (
                <li key={index} className={styles.historyItem}>
                  <span className={styles.historyQuery}>{item.query}</span>
                  <span className={styles.historyTime}>
                    {new Date(item.timestamp).toLocaleTimeString()}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      {/* Settings */}
      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>
          <Settings size={16} />
          SETTINGS
        </h3>
        <div className={styles.sectionContent}>
          <div className={styles.settingItem}>
            <span>Theme</span>
            <button className={styles.toggleBtn} onClick={toggleTheme}>
              {theme === 'light' ? 'Light' : 'Dark'}
            </button>
          </div>
        </div>
      </section>
    </nav>
  );
}

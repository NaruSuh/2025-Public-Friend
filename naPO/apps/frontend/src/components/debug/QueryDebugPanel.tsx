import React, { useState, useCallback } from 'react';
import { ChevronDown, ChevronRight, Copy, Download, Bug } from 'lucide-react';
import { useQueryStore } from '@/stores/queryStore';
import styles from './QueryDebugPanel.module.css';
import toast from 'react-hot-toast';

interface SectionProps {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

function Section({ title, defaultOpen = true, children }: SectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className={styles.section}>
      <div className={styles.sectionTitle} onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        {title}
      </div>
      {isOpen && <div className={styles.sectionContent}>{children}</div>}
    </div>
  );
}

function formatDuration(start?: number, end?: number): string {
  if (!start || !end) return '-';
  const duration = end - start;
  if (duration < 1000) {
    return `${duration.toFixed(0)}ms`;
  }
  return `${(duration / 1000).toFixed(2)}s`;
}

export function QueryDebugPanel() {
  const { debugInfo, parsedQuery, currentQuery } = useQueryStore();
  const [isExpanded, setIsExpanded] = useState(true);

  const copyDebugInfo = useCallback(() => {
    if (!debugInfo) return;

    const debugData = {
      timestamp: new Date().toISOString(),
      query: currentQuery,
      parsedQuery,
      debugInfo,
    };

    navigator.clipboard.writeText(JSON.stringify(debugData, null, 2));
    toast.success('Debug info copied to clipboard');
  }, [debugInfo, parsedQuery, currentQuery]);

  const exportDebugLog = useCallback(() => {
    if (!debugInfo) return;

    const debugData = {
      timestamp: new Date().toISOString(),
      query: currentQuery,
      parsedQuery,
      debugInfo,
    };

    const blob = new Blob([JSON.stringify(debugData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `napo-debug-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Debug log exported');
  }, [debugInfo, parsedQuery, currentQuery]);

  const hasData = debugInfo || parsedQuery;

  return (
    <div className={styles.panel}>
      <div className={styles.header} onClick={() => setIsExpanded(!isExpanded)}>
        <div className={styles.headerTitle}>
          <Bug size={16} />
          QUERY DEBUG
        </div>
        <ChevronDown
          size={16}
          className={`${styles.collapseIcon} ${isExpanded ? styles.expanded : ''}`}
        />
      </div>

      {isExpanded && (
        <div className={styles.content}>
          {!hasData ? (
            <div className={styles.emptyState}>
              Execute a query to see debug information
            </div>
          ) : (
            <>
              {/* Raw Query */}
              <Section title="RAW QUERY">
                <div className={styles.row}>
                  <span className={styles.value}>{currentQuery || '-'}</span>
                </div>
              </Section>

              {/* Timing */}
              <Section title="TIMING">
                <div className={styles.timing}>
                  <div className={styles.timingItem}>
                    <span className={styles.timingLabel}>Parse</span>
                    <span className={styles.timingValue}>
                      {formatDuration(debugInfo?.parseStartTime, debugInfo?.parseEndTime)}
                    </span>
                  </div>
                  <div className={styles.timingItem}>
                    <span className={styles.timingLabel}>Execute</span>
                    <span className={styles.timingValue}>
                      {formatDuration(debugInfo?.executeStartTime, debugInfo?.executeEndTime)}
                    </span>
                  </div>
                  <div className={styles.timingItem}>
                    <span className={styles.timingLabel}>Total</span>
                    <span className={styles.timingValue}>
                      {formatDuration(debugInfo?.parseStartTime, debugInfo?.executeEndTime)}
                    </span>
                  </div>
                </div>
              </Section>

              {/* Parsed Result */}
              {parsedQuery && (
                <Section title="PARSED RESULT">
                  <div className={styles.row}>
                    <span className={styles.label}>Intent:</span>
                    <span className={styles.value}>{parsedQuery.intent}</span>
                  </div>
                  <div className={styles.row}>
                    <span className={styles.label}>Confidence:</span>
                    <span className={styles.value}>
                      {(parsedQuery.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className={styles.row}>
                    <span className={styles.label}>Source:</span>
                    <span className={styles.value}>
                      {parsedQuery.source?.id || parsedQuery.source?.url || 'N/A'}
                    </span>
                  </div>
                  <div className={styles.row}>
                    <span className={styles.label}>Source Type:</span>
                    <span className={styles.value}>{parsedQuery.source?.type}</span>
                  </div>
                </Section>
              )}

              {/* Filters */}
              {parsedQuery?.filters && Object.keys(parsedQuery.filters).length > 0 && (
                <Section title="FILTERS" defaultOpen={false}>
                  <div className={styles.filters}>
                    {JSON.stringify(parsedQuery.filters, null, 2)}
                  </div>
                </Section>
              )}

              {/* Execution Details */}
              <Section title="EXECUTION">
                <div className={styles.row}>
                  <span className={styles.label}>Total Rows:</span>
                  <span className={`${styles.value} ${styles.success}`}>
                    {debugInfo?.totalRows ?? '-'}
                  </span>
                </div>
                <div className={styles.row}>
                  <span className={styles.label}>API Chain:</span>
                  <span className={styles.value}>
                    {debugInfo?.backendDebug?.apiChainUsed ? 'Yes' : 'No'}
                  </span>
                </div>
                {debugInfo?.backendDebug?.stages && (
                  <div className={styles.row}>
                    <span className={styles.label}>Stages:</span>
                    <span className={styles.value}>
                      {debugInfo.backendDebug.stages.join(' -> ')}
                    </span>
                  </div>
                )}
              </Section>

              {/* Queried Parties */}
              {debugInfo?.queriedParties && debugInfo.queriedParties.length > 0 && (
                <Section title="QUERIED PARTIES">
                  <div className={styles.partyList}>
                    {debugInfo.queriedParties.map((party, idx) => (
                      <span
                        key={idx}
                        className={`${styles.partyTag} ${
                          debugInfo.failedParties?.includes(party) ? styles.failed : ''
                        }`}
                      >
                        {party}
                      </span>
                    ))}
                  </div>
                  {debugInfo.failedParties && debugInfo.failedParties.length > 0 && (
                    <div className={styles.row} style={{ marginTop: 'var(--spacing-2)' }}>
                      <span className={styles.label}>Failed:</span>
                      <span className={`${styles.value} ${styles.error}`}>
                        {debugInfo.failedParties.join(', ')}
                      </span>
                    </div>
                  )}
                </Section>
              )}

              {/* Backend Debug Info */}
              {debugInfo?.backendDebug?.adaptedParams && (
                <Section title="ADAPTED PARAMS" defaultOpen={false}>
                  <div className={styles.filters}>
                    {JSON.stringify(debugInfo.backendDebug.adaptedParams, null, 2)}
                  </div>
                </Section>
              )}

              {/* Actions */}
              <div className={styles.actions}>
                <button className={styles.actionBtn} onClick={copyDebugInfo}>
                  <Copy size={14} />
                  Copy Debug Info
                </button>
                <button className={styles.actionBtn} onClick={exportDebugLog}>
                  <Download size={14} />
                  Export Log
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

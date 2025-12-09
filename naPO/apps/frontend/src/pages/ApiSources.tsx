import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { apiService } from '@/services/api';
import { useAppStore } from '@/stores/appStore';
import { ArrowLeft, Plus, Key, Check, X, ExternalLink } from 'lucide-react';
import { ApiKeyForm } from '@/components/forms/ApiKeyForm';
import styles from './ApiSources.module.css';

interface ApiSource {
  id: string;
  name: string;
  displayName: string;
  baseUrl: string;
  isActive: boolean;
  apiKeys: Array<{
    id: string;
    label: string | null;
    isActive: boolean;
    createdAt: string;
  }>;
}

export default function ApiSources() {
  const { setCurrentView } = useAppStore();
  const queryClient = useQueryClient();
  const [expandedSource, setExpandedSource] = React.useState<string | null>(null);
  const [addingKeyFor, setAddingKeyFor] = React.useState<string | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['apiSources'],
    queryFn: async () => {
      const response = await apiService.get('/sources/apis');
      return response.data.data as ApiSource[];
    },
  });

  const toggleKeyMutation = useMutation({
    mutationFn: async ({
      sourceId,
      keyId,
      isActive,
    }: {
      sourceId: string;
      keyId: string;
      isActive: boolean;
    }) => {
      return apiService.patch(`/sources/apis/${sourceId}/keys/${keyId}`, { isActive });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['apiSources'] });
    },
  });

  const addKeyMutation = useMutation({
    mutationFn: async ({
      sourceId,
      keyValue,
      label,
    }: {
      sourceId: string;
      keyValue: string;
      label?: string;
    }) => {
      return apiService.post(`/sources/apis/${sourceId}/keys`, { keyValue, label });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['apiSources'] });
      setAddingKeyFor(null);
      toast.success('API key added successfully');
    },
    onError: (error: any) => {
      toast.error(`Failed to add API key: ${error.message || 'Unknown error'}`);
    },
  });

  const sources = data || [];

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <button className={styles.backBtn} onClick={() => setCurrentView('dashboard')}>
          <ArrowLeft size={20} />
          <span>Back to Dashboard</span>
        </button>
        <h2 className={styles.title}>API SOURCES</h2>
        <p className={styles.subtitle}>등록된 API 데이터 소스 및 인증 키 관리</p>
      </div>

      {isLoading ? (
        <div className={styles.loading}>Loading API sources...</div>
      ) : error ? (
        <div className={styles.error}>
          <p>Failed to load API sources</p>
          <span>{(error as Error).message}</span>
        </div>
      ) : sources.length === 0 ? (
        <div className={styles.empty}>
          <p>NO API SOURCES</p>
          <span>API 소스가 등록되지 않았습니다</span>
        </div>
      ) : (
        <div className={styles.sourcesList}>
          {sources.map((source) => {
            const activeClass = source.isActive ? styles.active : styles.inactive;
            const isExpanded = expandedSource === source.id;
            const isAddingKey = addingKeyFor === source.id;

            return (
              <div key={source.id} className={styles.sourceCard}>
                <div
                  className={styles.sourceHeader}
                  onClick={() => setExpandedSource(isExpanded ? null : source.id)}
                >
                  <div className={styles.sourceInfo}>
                    <h3 className={styles.sourceName}>{source.displayName}</h3>
                    <div className={styles.sourceMeta}>
                      <span className={styles.sourceId}>{source.name}</span>
                      <a
                        href={source.baseUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.sourceUrl}
                      >
                        <ExternalLink size={14} />
                        {source.baseUrl}
                      </a>
                    </div>
                  </div>
                  <div className={styles.sourceStatus}>
                    <span className={styles.keyCount}>
                      <Key size={16} />
                      {source.apiKeys.length} {source.apiKeys.length === 1 ? 'key' : 'keys'}
                    </span>
                    <span className={`${styles.badge} ${activeClass}`}>
                      {source.isActive ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                  </div>
                </div>

                {isExpanded && (
                  <div className={styles.sourceDetails}>
                    <div className={styles.keysHeader}>
                      <h4>API KEYS</h4>
                      <button
                        className={styles.addKeyBtn}
                        onClick={() => setAddingKeyFor(isAddingKey ? null : source.id)}
                      >
                        <Plus size={16} />
                        Add Key
                      </button>
                    </div>

                    {isAddingKey && (
                      <ApiKeyForm
                        sourceId={source.id}
                        onSubmit={(data) => addKeyMutation.mutate(data)}
                        onCancel={() => setAddingKeyFor(null)}
                        isPending={addKeyMutation.isPending}
                      />
                    )}

                    {source.apiKeys.length === 0 ? (
                      <div className={styles.noKeys}>
                        <Key size={32} />
                        <p>No API keys configured</p>
                      </div>
                    ) : (
                      <div className={styles.keysList}>
                        {source.apiKeys.map((key) => {
                          const keyActiveClass = key.isActive
                            ? styles.activeBtn
                            : styles.inactiveBtn;

                          return (
                            <div key={key.id} className={styles.keyItem}>
                              <div className={styles.keyInfo}>
                                <span className={styles.keyLabel}>
                                  {key.label || 'Unnamed Key'}
                                </span>
                                <span className={styles.keyDate}>
                                  Added: {new Date(key.createdAt).toLocaleDateString('ko-KR')}
                                </span>
                              </div>
                              <button
                                className={`${styles.toggleBtn} ${keyActiveClass}`}
                                onClick={() =>
                                  toggleKeyMutation.mutate({
                                    sourceId: source.id,
                                    keyId: key.id,
                                    isActive: !key.isActive,
                                  })
                                }
                                disabled={toggleKeyMutation.isPending}
                              >
                                {key.isActive ? (
                                  <>
                                    <Check size={14} /> Active
                                  </>
                                ) : (
                                  <>
                                    <X size={14} /> Inactive
                                  </>
                                )}
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

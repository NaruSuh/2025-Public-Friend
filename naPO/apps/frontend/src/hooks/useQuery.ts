import { useCallback, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { useQueryStore } from '@/stores/queryStore';
import apiService from '@/services/api';
import { NLQueryResponse, DebugInfo } from '@/types';

export function useNLQuery() {
  const {
    currentQuery,
    setCurrentQuery,
    setParsedQuery,
    setIsParsingQuery,
    setQueryResult,
    setQueryError,
    addToHistory,
    updateDebugInfo,
    clearDebugInfo,
  } = useQueryStore();

  // Ref to track debug info during mutation lifecycle
  const debugRef = useRef<DebugInfo>({});

  // Parse natural language query
  const parseMutation = useMutation({
    mutationFn: (query: string) => apiService.parseQuery(query),
    onMutate: () => {
      setIsParsingQuery(true);
      setQueryError(null);
      // Start timing parse
      debugRef.current.parseStartTime = performance.now();
      updateDebugInfo({ parseStartTime: performance.now() });
    },
    onSuccess: (response: { data: NLQueryResponse }) => {
      // End timing parse
      const parseEndTime = performance.now();
      debugRef.current.parseEndTime = parseEndTime;
      debugRef.current.parsedQuery = response.data.parsedQuery;
      debugRef.current.source = response.data.parsedQuery?.source?.id;

      updateDebugInfo({
        parseEndTime,
        parsedQuery: response.data.parsedQuery,
        source: response.data.parsedQuery?.source?.id,
      });

      setParsedQuery(response.data.parsedQuery);
      toast.success('Query parsed successfully');
    },
    onError: (error: any) => {
      const parseEndTime = performance.now();
      debugRef.current.parseEndTime = parseEndTime;
      updateDebugInfo({ parseEndTime });

      const message = error.message || 'Failed to parse query';
      setQueryError(message);
      toast.error(`Parse failed: ${message}`);
    },
    onSettled: () => {
      setIsParsingQuery(false);
    },
  });

  // Execute parsed query
  const executeMutation = useMutation({
    mutationFn: (parsedQuery: any) => {
      // Start timing execution
      debugRef.current.executeStartTime = performance.now();
      updateDebugInfo({ executeStartTime: performance.now() });
      return apiService.executeQuery(parsedQuery);
    },
    onSuccess: (response) => {
      // End timing execution
      const executeEndTime = performance.now();
      debugRef.current.executeEndTime = executeEndTime;

      // Extract debug metadata from backend response
      const backendMetadata = response.data?.metadata;
      const nestedData = response.data?.data;
      const rowCount = nestedData?.totalCount ?? nestedData?.data?.length ?? nestedData?.length ?? 0;

      // Update debug info with execution details
      const debugUpdate: Partial<DebugInfo> = {
        executeEndTime,
        totalRows: rowCount,
        backendDebug: {
          apiChainUsed: backendMetadata?.apiChainUsed,
          stages: backendMetadata?.stages,
          originalFilters: backendMetadata?.debug?.originalFilters,
          adaptedParams: backendMetadata?.debug?.adaptedParams,
          successCount: backendMetadata?.debug?.successCount,
          failedCount: backendMetadata?.debug?.failedCount,
          successParties: backendMetadata?.debug?.successParties,
          failedParties: backendMetadata?.debug?.failedParties,
          candidateName: backendMetadata?.debug?.candidateName,
        },
        queriedParties: backendMetadata?.queriedParties || backendMetadata?.debug?.successParties,
        failedParties: backendMetadata?.debug?.failedParties,
      };

      debugRef.current = { ...debugRef.current, ...debugUpdate };
      updateDebugInfo(debugUpdate);

      setQueryResult(response.data);
      toast.success(`Retrieved ${rowCount} rows`);
    },
    onError: (error: any) => {
      const executeEndTime = performance.now();
      debugRef.current.executeEndTime = executeEndTime;
      updateDebugInfo({ executeEndTime });

      const message = error.message || 'Failed to execute query';
      setQueryError(message);
      toast.error(`Execution failed: ${message}`);
    },
  });

  const submitQuery = useCallback(
    async (query: string) => {
      try {
        // Validate query before submission
        const trimmedQuery = query.trim();
        if (!trimmedQuery) {
          setQueryError('Query cannot be empty');
          return;
        }

        if (trimmedQuery.length > 1000) {
          setQueryError('Query is too long (max 1000 characters)');
          return;
        }

        // Clear previous debug info and initialize new one
        clearDebugInfo();
        debugRef.current = {};

        setCurrentQuery(trimmedQuery);
        const parseResult = await parseMutation.mutateAsync(trimmedQuery);

        if (parseResult?.data?.parsedQuery) {
          await executeMutation.mutateAsync(parseResult.data.parsedQuery);

          // Add to history with debug info after successful execution
          addToHistory(trimmedQuery, parseResult.data.parsedQuery, debugRef.current);
        } else {
          setQueryError('Failed to parse query: Invalid response format');
        }
      } catch (error: any) {
        console.error('Query submission error:', error);
        setQueryError(error?.message || 'An unexpected error occurred');
      }
    },
    [parseMutation, executeMutation, setCurrentQuery, setQueryError, clearDebugInfo, addToHistory]
  );

  return {
    currentQuery,
    setCurrentQuery,
    submitQuery,
    isLoading: parseMutation.isPending || executeMutation.isPending,
  };
}

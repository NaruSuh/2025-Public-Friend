/**
 * ECOS (한국은행) API Connector
 */

import { BaseConnector, type ConnectorOptions } from '../base';
import { EcosAdapter, type EcosStatItem, type EcosKeyStatItem, type EcosEndpoint } from './EcosAdapter';
import type { ConnectorConfig, ConnectorStatus, NormalizedResponse, QueryFilters } from '@labgod/core-types';

export const ECOS_CONFIG: ConnectorConfig = {
  id: 'ecos',
  name: 'ECOS (한국은행 경제통계)',
  baseUrl: 'https://ecos.bok.or.kr/api',
  timeout: 30000,
  rateLimit: { requestsPerDay: 10000 },
};

export interface EcosConnectorOptions extends ConnectorOptions {
  apiKey: string;
}

export class EcosConnector extends BaseConnector {
  private readonly ecosApiKey: string;

  constructor(options: EcosConnectorOptions) {
    super(ECOS_CONFIG, options);
    this.ecosApiKey = options.apiKey;
    if (!this.ecosApiKey) throw new Error('ECOS API key is required');
  }

  async checkStatus(): Promise<ConnectorStatus> {
    try {
      const url = EcosAdapter.buildApiUrl(this.ecosApiKey, 'KeyStatisticList', { startCount: 1, endCount: 1 });
      const response = await this.get(url.replace(ECOS_CONFIG.baseUrl, ''));
      const result = response as Record<string, { CODE?: string }> | undefined;
      const isHealthy = Boolean(response && !result?.RESULT?.CODE?.startsWith('ERROR'));
      return { isConnected: isHealthy, id: this.getId(), name: this.getName(), enabled: true, healthy: isHealthy, lastCheck: new Date().toISOString() };
    } catch (error) {
      return { isConnected: false, id: this.getId(), name: this.getName(), enabled: true, healthy: false, lastCheck: new Date().toISOString(), error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async fetchByFilters<T = EcosStatItem>(filters: QueryFilters): Promise<NormalizedResponse<T>> {
    const params = EcosAdapter.adaptFilters(filters);
    const url = EcosAdapter.buildApiUrl(this.ecosApiKey, 'StatisticSearch', params);
    const response = await this.get(url.replace(ECOS_CONFIG.baseUrl, ''));
    return EcosAdapter.normalizeDataResponse(response) as unknown as NormalizedResponse<T>;
  }

  async getStatData(params: { statCode: string; itemCode1?: string; itemCode2?: string; startTime: string; endTime: string; cycle?: string }): Promise<NormalizedResponse<EcosStatItem>> {
    const url = EcosAdapter.buildApiUrl(this.ecosApiKey, 'StatisticSearch', params);
    const response = await this.get(url.replace(ECOS_CONFIG.baseUrl, ''));
    return EcosAdapter.normalizeDataResponse(response);
  }

  async getInterestRates(params?: { startDate?: string; endDate?: string }): Promise<NormalizedResponse<EcosStatItem>> {
    const apiParams = EcosAdapter.buildInterestRateParams(params?.startDate, params?.endDate);
    const url = EcosAdapter.buildApiUrl(this.ecosApiKey, 'StatisticSearch', apiParams);
    const response = await this.get(url.replace(ECOS_CONFIG.baseUrl, ''));
    return EcosAdapter.normalizeDataResponse(response);
  }

  async getExchangeRates(params?: { currency?: '달러' | '엔' | '유로'; startDate?: string; endDate?: string }): Promise<NormalizedResponse<EcosStatItem>> {
    const apiParams = EcosAdapter.buildExchangeRateParams(params?.currency, params?.startDate, params?.endDate);
    const url = EcosAdapter.buildApiUrl(this.ecosApiKey, 'StatisticSearch', apiParams);
    const response = await this.get(url.replace(ECOS_CONFIG.baseUrl, ''));
    return EcosAdapter.normalizeDataResponse(response);
  }

  async getKeyStatistics(): Promise<NormalizedResponse<EcosKeyStatItem>> {
    const url = EcosAdapter.buildApiUrl(this.ecosApiKey, 'KeyStatisticList', {});
    const response = await this.get(url.replace(ECOS_CONFIG.baseUrl, ''));
    return EcosAdapter.normalizeKeyStatResponse(response);
  }
}

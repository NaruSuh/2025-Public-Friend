import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { XMLParser } from 'fast-xml-parser';
import { ApiEndpointConfig, ApiResponse, ApiRequestParams } from '@/types/api.types';
import { env } from '@/config/env';
import { logger } from '@/config/logger';

export abstract class BaseApiConnector {
  protected config: ApiEndpointConfig;
  protected client: AxiosInstance;
  protected xmlParser: XMLParser;

  constructor(config: ApiEndpointConfig) {
    this.config = config;
    this.client = axios.create({
      baseURL: config.baseUrl,
      timeout: 30000,
    });
    this.xmlParser = new XMLParser({
      ignoreAttributes: false,
      attributeNamePrefix: '@_',
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor for logging
    this.client.interceptors.request.use((config) => {
      logger.debug(`[API] ${config.method?.toUpperCase()} ${config.url}`);
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        logger.error(`[API Error]`, { error: error.message });
        throw error;
      }
    );
  }

  protected getApiKey(): string | undefined {
    // Override in subclass to provide specific API key
    return undefined;
  }

  protected buildAuthParams(): Record<string, string> {
    const { authType, authConfig } = this.config;
    const apiKey = this.getApiKey();

    if (authType === 'api_key' && apiKey && authConfig.keyParamName) {
      if (authConfig.keyLocation === 'query') {
        return { [authConfig.keyParamName]: apiKey };
      }
    }
    return {};
  }

  protected buildAuthHeaders(): Record<string, string> {
    const { authType, authConfig } = this.config;
    const apiKey = this.getApiKey();

    if (authType === 'bearer' && apiKey) {
      return { Authorization: `Bearer ${apiKey}` };
    }
    if (authType === 'api_key' && authConfig.keyLocation === 'header' && apiKey) {
      const headerName = authConfig.headerName || 'X-API-Key';
      return { [headerName]: apiKey };
    }
    return {};
  }

  async fetch<T = any>(request: ApiRequestParams): Promise<ApiResponse<T>> {
    const startTime = Date.now();
    const requestId = `${this.config.id}-${Date.now()}`;

    try {
      const endpoint = request.endpoint || '';
      const authParams = this.buildAuthParams();
      const authHeaders = this.buildAuthHeaders();

      const axiosConfig: AxiosRequestConfig = {
        method: 'GET',
        url: endpoint,
        params: {
          ...this.config.defaultParams,
          ...authParams,
          ...request.params,
          resultType: 'json', // Force JSON response
        },
        headers: {
          ...authHeaders,
          ...request.headers,
        },
      };

      const response = await this.client.request(axiosConfig);
      let data = response.data;

      // XML 응답 처리
      if (typeof data === 'string' && data.trim().startsWith('<?xml')) {
        data = this.xmlParser.parse(data);
      }

      // 공공데이터포털 응답 구조 처리
      const normalizedData = this.normalizeResponse(data);

      return {
        success: true,
        data: normalizedData as T,
        metadata: {
          requestId,
          timestamp: new Date().toISOString(),
          source: this.config.id,
          totalCount: this.extractTotalCount(data),
          pageNo: typeof request.params?.pageNo === 'number' ? request.params.pageNo : undefined,
          numOfRows: typeof request.params?.numOfRows === 'number' ? request.params.numOfRows : undefined,
        },
      };
    } catch (error: any) {
      return {
        success: false,
        error: {
          code: error.response?.status?.toString() || 'UNKNOWN',
          message: error.message,
        },
        metadata: {
          requestId,
          timestamp: new Date().toISOString(),
          source: this.config.id,
        },
      };
    }
  }

  // Override in subclass for custom normalization
  protected normalizeResponse(data: any): any {
    // 공공데이터포털 기본 구조: response.body.items.item
    if (data?.response?.body?.items?.item) {
      return data.response.body.items.item;
    }
    return data;
  }

  protected extractTotalCount(data: any): number | undefined {
    return data?.response?.body?.totalCount;
  }

  getConfig(): ApiEndpointConfig {
    return this.config;
  }
}

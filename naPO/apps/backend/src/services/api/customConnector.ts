import { BaseApiConnector } from './baseConnector';
import { ApiEndpointConfig, ApiResponse, ApiRequestParams } from '@/types/api.types';

// 사용자 정의 API 커넥터 (동적 생성용)
export class CustomApiConnector extends BaseApiConnector {
  private apiKey?: string;

  constructor(config: ApiEndpointConfig, apiKey?: string) {
    super(config);
    this.apiKey = apiKey;
  }

  protected getApiKey(): string | undefined {
    return this.apiKey;
  }

  setApiKey(key: string): void {
    this.apiKey = key;
  }

  // 범용 요청 메서드
  async request(params: ApiRequestParams): Promise<ApiResponse> {
    return this.fetch(params);
  }
}

// API 커넥터 팩토리
export class ApiConnectorFactory {
  // 캐시 제거: API 키 변경 시 오래된 커넥터를 반환하는 문제 방지
  static create(config: ApiEndpointConfig, apiKey?: string): BaseApiConnector {
    // 매번 새로운 커넥터 인스턴스 생성 (API 키 변경 반영)
    return new CustomApiConnector(config, apiKey);
  }
}

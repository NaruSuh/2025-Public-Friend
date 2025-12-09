import { ApiRegistry } from '@/config/apis';
import { ApiConnectorFactory } from './customConnector';
import { PartyPolicyAdapter } from './adapters/partyPolicyAdapter';
import { logger } from '@/config/logger';

/**
 * 중앙선거관리위원회 정당정책 정보 조회 서비스
 *
 * 정당의 공약 정보를 조회하는 서비스
 *
 * 사용 예:
 * ```
 * const policies = await PartyPolicyService.getPartyPolicy(apiKey, '20220309', '국민의힘');
 * const comparison = await PartyPolicyService.comparePartyPolicies(apiKey, '20220309', ['국민의힘', '더불어민주당']);
 * ```
 */
export class PartyPolicyService {
  /**
   * 정당정책 정보 조회
   *
   * @param apiKey 공공데이터포털 API 키
   * @param electionId 선거ID (예: "20220309")
   * @param partyName 정당명 (예: "국민의힘")
   * @returns 정당정책 정보
   */
  static async getPartyPolicy(
    apiKey: string,
    electionId: string,
    partyName: string
  ): Promise<any> {
    logger.debug(`[PARTY-POLICY] Fetching party policy for ${partyName} in election ${electionId}...`);

    const params = {
      sgId: electionId,
      partyName,
      pageNo: 1,
      numOfRows: 10,
      resultType: 'json',
    };

    // 파라미터 검증
    const validation = PartyPolicyAdapter.validateParams(params);
    if (!validation.valid) {
      logger.error('[PARTY-POLICY] Parameter validation failed:', { errors: validation.errors });
      return {
        success: false,
        error: {
          message: 'Invalid parameters',
          details: validation.errors,
        },
      };
    }

    try {
      const config = ApiRegistry.getInstance().get('public_data_party_policy');
      if (!config) {
        throw new Error('Party Policy API configuration not found in registry');
      }

      const connector = ApiConnectorFactory.create(config, apiKey);
      const response = await connector.fetch({
        endpoint: '/getPartyPlcInfoInqire',
        params,
      });

      logger.debug('[PARTY-POLICY] Party policy response received');

      const normalized = PartyPolicyAdapter.normalizeResponse(response.data);

      if (!normalized.success) {
        logger.error('[PARTY-POLICY] Failed to fetch party policy:', { error: normalized.error });
      } else {
        logger.debug(`[PARTY-POLICY] Found ${normalized.totalCount} party policy records`);
      }

      return normalized;
    } catch (error: any) {
      logger.error('[PARTY-POLICY] Error fetching party policy:', { error: error.message });
      return {
        success: false,
        error: {
          message: error.message || 'Unknown error occurred',
        },
      };
    }
  }

  /**
   * 여러 정당의 정책 조회
   *
   * @param apiKey 공공데이터포털 API 키
   * @param electionId 선거ID
   * @param partyNames 정당명 배열
   * @returns 각 정당별 정책 정보 배열
   */
  static async getMultiplePartyPolicies(
    apiKey: string,
    electionId: string,
    partyNames: string[]
  ): Promise<any[]> {
    logger.debug(`[PARTY-POLICY] Fetching policies for ${partyNames.length} parties...`);

    const results = await Promise.allSettled(
      partyNames.map((partyName) => this.getPartyPolicy(apiKey, electionId, partyName))
    );

    return results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return {
          partyName: partyNames[index],
          ...result.value,
        };
      } else {
        return {
          partyName: partyNames[index],
          success: false,
          error: {
            message: result.reason?.message || 'Promise rejected',
          },
        };
      }
    });
  }

  /**
   * 정당 간 정책 비교
   *
   * @param apiKey 공공데이터포털 API 키
   * @param electionId 선거ID
   * @param partyNames 비교할 정당명 배열
   * @returns 정당별 정책 비교 데이터
   */
  static async comparePartyPolicies(
    apiKey: string,
    electionId: string,
    partyNames: string[]
  ): Promise<any> {
    logger.debug(`[PARTY-POLICY] Comparing policies for ${partyNames.length} parties...`);

    const policies = await this.getMultiplePartyPolicies(apiKey, electionId, partyNames);

    // 성공한 정당만 필터링
    const successPolicies = policies
      .filter((p) => p.success && p.data && p.data.length > 0)
      .map((p) => p.data[0]);

    if (successPolicies.length === 0) {
      return {
        success: false,
        error: {
          message: 'No party policies found',
        },
      };
    }

    const comparison = PartyPolicyAdapter.createComparisonData(successPolicies);

    logger.debug('[PARTY-POLICY] Policy comparison completed');
    logger.debug(`[PARTY-POLICY] Parties: ${comparison.parties.length}`);
    logger.debug(`[PARTY-POLICY] Realms: ${comparison.realms.length}`);

    return {
      success: true,
      electionId,
      comparison,
    };
  }

  /**
   * 특정 분야의 정당 정책 비교
   *
   * @param apiKey 공공데이터포털 API 키
   * @param electionId 선거ID
   * @param partyNames 정당명 배열
   * @param realmKeyword 분야 키워드 (예: "노동", "환경")
   * @returns 특정 분야의 정당별 정책
   */
  static async compareByRealm(
    apiKey: string,
    electionId: string,
    partyNames: string[],
    realmKeyword: string
  ): Promise<any> {
    logger.debug(`[PARTY-POLICY] Comparing policies in realm: ${realmKeyword}`);

    const policies = await this.getMultiplePartyPolicies(apiKey, electionId, partyNames);

    const realmComparison: Record<string, any> = {};

    policies.forEach((partyData) => {
      if (partyData.success && partyData.data && partyData.data.length > 0) {
        const partyPolicy = partyData.data[0];
        const filteredPolicies = PartyPolicyAdapter.filterPoliciesByRealm(
          partyPolicy.policies,
          realmKeyword
        );

        realmComparison[partyPolicy.partyName] = filteredPolicies;
      }
    });

    return {
      success: true,
      electionId,
      realm: realmKeyword,
      policies: realmComparison,
    };
  }

  /**
   * 키워드로 정당 정책 검색
   *
   * @param apiKey 공공데이터포털 API 키
   * @param electionId 선거ID
   * @param partyName 정당명
   * @param keyword 검색 키워드
   * @returns 키워드가 포함된 공약 목록
   */
  static async searchPartyPolicies(
    apiKey: string,
    electionId: string,
    partyName: string,
    keyword: string
  ): Promise<any> {
    logger.debug(`[PARTY-POLICY] Searching for "${keyword}" in ${partyName} policies`);

    const result = await this.getPartyPolicy(apiKey, electionId, partyName);

    if (!result.success || !result.data || result.data.length === 0) {
      return result;
    }

    const partyPolicy = result.data[0];
    const matchedPolicies = PartyPolicyAdapter.searchPoliciesByTitle(
      partyPolicy.policies,
      keyword
    );

    return {
      success: true,
      electionId,
      partyName: partyPolicy.partyName,
      keyword,
      totalPolicies: partyPolicy.policyCount,
      matchedCount: matchedPolicies.length,
      policies: matchedPolicies,
    };
  }

  /**
   * 정당 정책 통계 생성
   *
   * @param apiKey 공공데이터포털 API 키
   * @param electionId 선거ID
   * @param partyName 정당명
   * @returns 정당 정책 통계
   */
  static async getPartyPolicyStats(
    apiKey: string,
    electionId: string,
    partyName: string
  ): Promise<any> {
    logger.debug(`[PARTY-POLICY] Generating policy stats for ${partyName}`);

    const result = await this.getPartyPolicy(apiKey, electionId, partyName);

    if (!result.success || !result.data || result.data.length === 0) {
      return result;
    }

    const partyPolicy = result.data[0];
    const stats = PartyPolicyAdapter.generatePolicyStats(partyPolicy);

    return {
      success: true,
      electionId,
      stats,
    };
  }

  /**
   * 여러 정당의 정책 통계 비교
   *
   * @param apiKey 공공데이터포털 API 키
   * @param electionId 선거ID
   * @param partyNames 정당명 배열
   * @returns 정당별 정책 통계 배열
   */
  static async comparePartyPolicyStats(
    apiKey: string,
    electionId: string,
    partyNames: string[]
  ): Promise<any> {
    logger.debug(`[PARTY-POLICY] Comparing policy stats for ${partyNames.length} parties`);

    const statsPromises = partyNames.map((partyName) =>
      this.getPartyPolicyStats(apiKey, electionId, partyName)
    );

    const results = await Promise.allSettled(statsPromises);

    const stats = results
      .map((result, index) => {
        if (result.status === 'fulfilled' && result.value.success) {
          return result.value.stats;
        }
        return null;
      })
      .filter((stat) => stat !== null);

    return {
      success: true,
      electionId,
      partiesCount: stats.length,
      stats,
    };
  }
}

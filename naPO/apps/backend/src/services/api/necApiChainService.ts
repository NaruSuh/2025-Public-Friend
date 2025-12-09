import { ApiRegistry } from '@/config/apis';
import { ApiConnectorFactory } from './customConnector';
import { NecCandidateAdapter } from './adapters/necCandidateAdapter';
import { NecManifestoAdapter } from './adapters/necManifestoAdapter';
import { logger } from '@/config/logger';

/**
 * NEC (중앙선거관리위원회) API 체인 서비스
 *
 * 문제: 선거공약 API는 cnddtId (후보자ID) 필수이지만 사용자는 이름만 알고 있음
 * 해결: 2단계 API 체인으로 자동 조회
 *
 * 1단계: 후보자 정보 API 호출 → huboid 획득
 * 2단계: 선거공약 API 호출 → 공약 정보 반환
 *
 * 사용 예:
 * ```
 * const pledges = await NecApiChainService.getCandidatePledgesByName(
 *   '20220309',
 *   '1',
 *   '윤석열',
 *   apiKey
 * );
 * ```
 */
export class NecApiChainService {
  /**
   * 후보자 이름으로 공약 정보 조회 (2단계 체인)
   *
   * @param electionId 선거ID (예: "20220309")
   * @param electionType 선거종류코드 (예: "1" = 대통령)
   * @param candidateName 후보자 이름 (예: "윤석열")
   * @param apiKey 공공데이터포털 API 키
   * @param partyName 정당명 (옵션, 동명이인 구분용)
   * @returns 공약 정보 또는 에러
   */
  static async getCandidatePledgesByName(
    electionId: string,
    electionType: string,
    candidateName: string,
    apiKey: string,
    partyName?: string
  ): Promise<any> {
    logger.debug('[NEC-API-CHAIN] Starting 2-stage API chain...');
    logger.debug(`[NEC-API-CHAIN] Election: ${electionId}, Type: ${electionType}`);
    logger.debug(`[NEC-API-CHAIN] Searching for candidate: ${candidateName}${partyName ? ` (${partyName})` : ''}`);

    // ============================================
    // STAGE 1: 후보자 정보 조회 (Candidate Info API)
    // ============================================
    logger.debug('[NEC-API-CHAIN] Stage 1: Fetching candidate information...');

    const candidateParams: Record<string, any> = {
      sgId: electionId,
      sgTypecode: electionType,
      pageNo: 1,
      numOfRows: 100, // 많은 후보자를 처리하기 위해 넉넉하게
      resultType: 'json',
    };

    // 대통령 선거의 경우 선거구 정보 추가
    if (electionType === '1') {
      candidateParams['sggName'] = '대한민국';
      candidateParams['sdName'] = '전국';
    }

    logger.debug('[NEC-API-CHAIN] Candidate API params:', candidateParams);

    try {
      // 후보자 API 설정 가져오기
      const candidateConfig = ApiRegistry.getInstance().get('public_data_candidate');
      if (!candidateConfig) {
        throw new Error('Candidate API configuration not found in registry');
      }

      // 후보자 API 커넥터 생성
      const candidateConnector = ApiConnectorFactory.create(candidateConfig, apiKey);

      // 후보자 API 호출
      const candidateResponse = await candidateConnector.fetch({
        endpoint: '/getPofelcddRegistSttusInfoInqire',
        params: candidateParams,
      });

      logger.debug('[NEC-API-CHAIN] Candidate API response received');
      logger.debug('[NEC-API-CHAIN] Response status:', candidateResponse.success ? 'success' : 'failed');

      // 응답 정규화
      const normalizedCandidates = NecCandidateAdapter.normalizeResponse(candidateResponse.data);

      if (!normalizedCandidates.success) {
        logger.error('[NEC-API-CHAIN] Stage 1 failed:', { error: normalizedCandidates.error });
        return {
          success: false,
          error: {
            stage: 'candidate_lookup',
            message: `Candidate API error: ${normalizedCandidates.error?.message}`,
            code: normalizedCandidates.error?.code,
          },
        };
      }

      logger.debug(`[NEC-API-CHAIN] Found ${normalizedCandidates.totalCount} total candidates`);

      // 후보자 이름으로 필터링
      const candidate = NecCandidateAdapter.filterByName(
        normalizedCandidates.data || [],
        candidateName,
        partyName
      );

      if (!candidate) {
        logger.error(`[NEC-API-CHAIN] Candidate not found: ${candidateName}`);
        return {
          success: false,
          error: {
            stage: 'candidate_lookup',
            message: `Candidate not found: ${candidateName}`,
            availableCandidates: normalizedCandidates.data?.map((c: any) => ({
              name: c.nameKr,
              party: c.party,
              ballotNumber: c.ballotNumber,
            })),
          },
        };
      }

      logger.debug('[NEC-API-CHAIN] Candidate found:', {
        name: candidate.nameKr,
        nameHanja: candidate.nameHanja,
        party: candidate.party,
        ballot: candidate.ballotNumber,
        huboid: candidate.huboid,
      });

      const huboid = candidate.huboid;

      if (!huboid) {
        logger.error('[NEC-API-CHAIN] huboid missing in candidate data');
        return {
          success: false,
          error: {
            stage: 'candidate_lookup',
            message: 'huboid not found in candidate data',
            candidateData: candidate,
          },
        };
      }

      // ============================================
      // STAGE 2: 선거공약 조회 (Manifesto API)
      // ============================================
      logger.debug('[NEC-API-CHAIN] Stage 2: Fetching manifesto with huboid...');

      const pledgeParams = {
        sgId: electionId,
        sgTypecode: electionType,
        cnddtId: huboid, // ⚠️ huboid를 cnddtId로 사용
        pageNo: 1,
        numOfRows: 10, // 공약 최대 10개
        resultType: 'json',
      };

      logger.debug('[NEC-API-CHAIN] Manifesto API params:', pledgeParams);

      // 공약 API 설정 가져오기
      const pledgeConfig = ApiRegistry.getInstance().get('public_data_election');
      if (!pledgeConfig) {
        throw new Error('Manifesto API configuration not found in registry');
      }

      // 공약 API 커넥터 생성
      const pledgeConnector = ApiConnectorFactory.create(pledgeConfig, apiKey);

      // 공약 API 호출
      const pledgeResponse = await pledgeConnector.fetch({
        endpoint: '/getCnddtElecPrmsInfoInqire',
        params: pledgeParams,
      });

      logger.debug('[NEC-API-CHAIN] Manifesto API response received');

      // 응답 정규화
      const normalizedPledges = NecManifestoAdapter.normalizeResponse(pledgeResponse.data);

      if (!normalizedPledges.success) {
        logger.error('[NEC-API-CHAIN] Stage 2 failed:', { error: normalizedPledges.error });
        return {
          success: false,
          error: {
            stage: 'manifesto_lookup',
            message: `Manifesto API error: ${normalizedPledges.error?.message}`,
            code: normalizedPledges.error?.code,
          },
        };
      }

      logger.debug(`[NEC-API-CHAIN] Found ${normalizedPledges.totalCount} pledge records`);
      logger.debug('[NEC-API-CHAIN] API chain completed successfully!');

      // 후보자 정보와 공약 정보 결합
      return {
        success: true,
        candidate: {
          id: candidate.huboid,
          name: candidate.nameKr,
          nameHanja: candidate.nameHanja,
          party: candidate.party,
          ballotNumber: candidate.ballotNumber,
          district: candidate.district,
          sido: candidate.sido,
        },
        pledges: normalizedPledges,
        metadata: {
          electionId,
          electionType,
          chainStages: ['candidate_lookup', 'manifesto_lookup'],
          timestamp: new Date().toISOString(),
        },
      };
    } catch (error: any) {
      logger.error('[NEC-API-CHAIN] API chain failed with exception:', { error: error.message, stack: error.stack });
      return {
        success: false,
        error: {
          stage: 'unknown',
          message: error.message || 'Unknown error occurred',
          stack: error.stack,
        },
      };
    }
  }

  /**
   * 여러 후보자의 공약을 한 번에 조회
   *
   * @param electionId 선거ID
   * @param electionType 선거종류코드
   * @param candidateNames 후보자 이름 배열
   * @param apiKey API 키
   * @returns 각 후보자별 공약 정보 배열
   */
  static async getMultipleCandidatesPledges(
    electionId: string,
    electionType: string,
    candidateNames: string[],
    apiKey: string
  ): Promise<any[]> {
    logger.debug(`[NEC-API-CHAIN] Fetching pledges for ${candidateNames.length} candidates...`);

    const results = await Promise.allSettled(
      candidateNames.map((name) =>
        this.getCandidatePledgesByName(electionId, electionType, name, apiKey)
      )
    );

    return results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return {
          candidateName: candidateNames[index],
          ...result.value,
        };
      } else {
        return {
          candidateName: candidateNames[index],
          success: false,
          error: {
            message: result.reason?.message || 'Promise rejected',
          },
        };
      }
    });
  }

  /**
   * 선거의 모든 후보자 목록 조회 (공약 없이 후보자 정보만)
   *
   * @param electionId 선거ID
   * @param electionType 선거종류코드
   * @param apiKey API 키
   * @returns 후보자 목록
   */
  static async getAllCandidates(
    electionId: string,
    electionType: string,
    apiKey: string
  ): Promise<any> {
    logger.debug(`[NEC-API-CHAIN] Fetching all candidates for election ${electionId}...`);

    const candidateParams: Record<string, any> = {
      sgId: electionId,
      sgTypecode: electionType,
      pageNo: 1,
      numOfRows: 100,
      resultType: 'json',
    };

    // 대통령 선거의 경우 선거구 정보 추가
    if (electionType === '1') {
      candidateParams['sggName'] = '대한민국';
      candidateParams['sdName'] = '전국';
    }

    try {
      const candidateConfig = ApiRegistry.getInstance().get('public_data_candidate');
      if (!candidateConfig) {
        throw new Error('Candidate API configuration not found');
      }

      const candidateConnector = ApiConnectorFactory.create(candidateConfig, apiKey);
      const candidateResponse = await candidateConnector.fetch({
        endpoint: '/getPofelcddRegistSttusInfoInqire',
        params: candidateParams,
      });

      const normalized = NecCandidateAdapter.normalizeResponse(candidateResponse.data);

      logger.debug(`[NEC-API-CHAIN] Found ${normalized.totalCount} candidates`);

      return normalized;
    } catch (error: any) {
      logger.error('[NEC-API-CHAIN] Failed to fetch all candidates:', { error: error.message });
      return {
        success: false,
        error: {
          message: error.message || 'Unknown error',
        },
      };
    }
  }
}

import { ApiRegistry } from '@/config/apis';
import { ApiConnectorFactory } from './customConnector';
import { CommonCodeAdapter } from './adapters/commonCodeAdapter';
import { logger } from '@/config/logger';
import type {
  NormalizedCodeResponse,
  ElectionCode,
  DistrictCode,
  PartyCode,
  JobCode,
  EducationCode,
} from '@/types/api.types';

/**
 * 중앙선거관리위원회 코드관리 서비스
 *
 * 코드 조회 API를 통해 선거, 지역, 정당, 직업, 학력 등의
 * 참조 데이터를 조회하는 서비스
 *
 * 사용 예:
 * ```
 * const elections = await CommonCodeService.getElectionCodes(apiKey);
 * const parties = await CommonCodeService.getPartyCodes('20220309', '1', apiKey);
 * ```
 */
export class CommonCodeService {
  /**
   * 선거코드 조회
   *
   * @param apiKey 공공데이터포털 API 키
   * @param sgTypecode 선거종류코드 (옵션, 지정하면 특정 선거 종류만 조회)
   * @returns 선거코드 목록
   */
  static async getElectionCodes(apiKey: string, sgTypecode?: string): Promise<NormalizedCodeResponse<ElectionCode>> {
    logger.debug('[COMMON-CODE] Fetching election codes...');

    const params: Record<string, string | number> = {
      pageNo: 1,
      numOfRows: 100,
      resultType: 'json',
    };

    if (sgTypecode) {
      params.sgTypecode = sgTypecode;
    }

    try {
      const config = ApiRegistry.getInstance().get('public_data_common_code');
      if (!config) {
        throw new Error('CommonCode API configuration not found in registry');
      }

      const connector = ApiConnectorFactory.create(config, apiKey);
      const response = await connector.fetch({
        endpoint: '/getCommonSgCodeList',
        params,
      });

      logger.debug('[COMMON-CODE] Election codes response received');

      const normalized = CommonCodeAdapter.normalizeElectionCodeResponse(response.data);

      if (!normalized.success) {
        logger.error('[COMMON-CODE] Failed to fetch election codes:', { error: normalized.error });
      } else {
        logger.debug(`[COMMON-CODE] Found ${normalized.totalCount} election codes`);
      }

      return normalized;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      logger.error('[COMMON-CODE] Error fetching election codes:', { error: errorMessage });
      return {
        success: false,
        totalCount: 0,
        pageNo: 1,
        numOfRows: 0,
        data: [],
        error: {
          code: 'FETCH_ERROR',
          message: errorMessage,
        },
      };
    }
  }

  /**
   * 시군구코드 조회
   *
   * @param apiKey 공공데이터포털 API 키
   * @param sgId 선거ID (옵션)
   * @param sgTypecode 선거종류코드 (옵션)
   * @returns 시군구코드 목록
   */
  static async getDistrictCodes(
    apiKey: string,
    sgId?: string,
    sgTypecode?: string
  ): Promise<NormalizedCodeResponse<DistrictCode>> {
    logger.debug('[COMMON-CODE] Fetching district codes...');

    const params: Record<string, string | number> = {
      pageNo: 1,
      numOfRows: 100,
      resultType: 'json',
    };

    if (sgId) params.sgId = sgId;
    if (sgTypecode) params.sgTypecode = sgTypecode;

    try {
      const config = ApiRegistry.getInstance().get('public_data_common_code');
      if (!config) {
        throw new Error('CommonCode API configuration not found in registry');
      }

      const connector = ApiConnectorFactory.create(config, apiKey);
      const response = await connector.fetch({
        endpoint: '/getCommonGusigunCodeList',
        params,
      });

      logger.debug('[COMMON-CODE] District codes response received');

      const normalized = CommonCodeAdapter.normalizeDistrictCodeResponse(response.data);

      if (!normalized.success) {
        logger.error('[COMMON-CODE] Failed to fetch district codes:', { error: normalized.error });
      } else {
        logger.debug(`[COMMON-CODE] Found ${normalized.totalCount} district codes`);
      }

      return normalized;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      logger.error('[COMMON-CODE] Error fetching district codes:', { error: errorMessage });
      return {
        success: false,
        totalCount: 0,
        pageNo: 1,
        numOfRows: 0,
        data: [],
        error: {
          code: 'FETCH_ERROR',
          message: errorMessage,
        },
      };
    }
  }

  /**
   * 선거구코드 조회
   *
   * @param apiKey 공공데이터포털 API 키
   * @param sgId 선거ID (필수)
   * @param sgTypecode 선거종류코드 (필수)
   * @returns 선거구코드 목록
   */
  static async getConstituencyCodes(
    apiKey: string,
    sgId: string,
    sgTypecode: string
  ): Promise<NormalizedCodeResponse<DistrictCode>> {
    logger.debug(`[COMMON-CODE] Fetching constituency codes for ${sgId}/${sgTypecode}...`);

    const params = {
      sgId,
      sgTypecode,
      pageNo: 1,
      numOfRows: 100,
      resultType: 'json',
    };

    try {
      const config = ApiRegistry.getInstance().get('public_data_common_code');
      if (!config) {
        throw new Error('CommonCode API configuration not found in registry');
      }

      const connector = ApiConnectorFactory.create(config, apiKey);
      const response = await connector.fetch({
        endpoint: '/getCommonSggCodeList',
        params,
      });

      logger.debug('[COMMON-CODE] Constituency codes response received');

      const normalized = CommonCodeAdapter.normalizeConstituencyCodeResponse(response.data);

      if (!normalized.success) {
        logger.error('[COMMON-CODE] Failed to fetch constituency codes:', { error: normalized.error });
      } else {
        logger.debug(`[COMMON-CODE] Found ${normalized.totalCount} constituency codes`);
      }

      return normalized;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      logger.error('[COMMON-CODE] Error fetching constituency codes:', { error: errorMessage });
      return {
        success: false,
        totalCount: 0,
        pageNo: 1,
        numOfRows: 0,
        data: [],
        error: {
          code: 'FETCH_ERROR',
          message: errorMessage,
        },
      };
    }
  }

  /**
   * 정당코드 조회
   *
   * @param apiKey 공공데이터포털 API 키
   * @param sgId 선거ID (필수)
   * @param sgTypecode 선거종류코드 (필수)
   * @returns 정당코드 목록
   */
  static async getPartyCodes(apiKey: string, sgId: string, sgTypecode: string): Promise<NormalizedCodeResponse<PartyCode>> {
    logger.debug(`[COMMON-CODE] Fetching party codes for ${sgId}/${sgTypecode}...`);

    const params = {
      sgId,
      sgTypecode,
      pageNo: 1,
      numOfRows: 100,
      resultType: 'json',
    };

    try {
      const config = ApiRegistry.getInstance().get('public_data_common_code');
      if (!config) {
        throw new Error('CommonCode API configuration not found in registry');
      }

      const connector = ApiConnectorFactory.create(config, apiKey);
      const response = await connector.fetch({
        endpoint: '/getCommonPartyCodeList',
        params,
      });

      logger.debug('[COMMON-CODE] Party codes response received');

      const normalized = CommonCodeAdapter.normalizePartyCodeResponse(response.data);

      if (!normalized.success) {
        logger.error('[COMMON-CODE] Failed to fetch party codes:', { error: normalized.error });
      } else {
        logger.debug(`[COMMON-CODE] Found ${normalized.totalCount} party codes`);
      }

      return normalized;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      logger.error('[COMMON-CODE] Error fetching party codes:', { error: errorMessage });
      return {
        success: false,
        totalCount: 0,
        pageNo: 1,
        numOfRows: 0,
        data: [],
        error: {
          code: 'FETCH_ERROR',
          message: errorMessage,
        },
      };
    }
  }

  /**
   * 직업코드 조회
   *
   * @param apiKey 공공데이터포털 API 키
   * @returns 직업코드 목록
   */
  static async getJobCodes(apiKey: string): Promise<NormalizedCodeResponse<JobCode>> {
    logger.debug('[COMMON-CODE] Fetching job codes...');

    const params = {
      pageNo: 1,
      numOfRows: 100,
      resultType: 'json',
    };

    try {
      const config = ApiRegistry.getInstance().get('public_data_common_code');
      if (!config) {
        throw new Error('CommonCode API configuration not found in registry');
      }

      const connector = ApiConnectorFactory.create(config, apiKey);
      const response = await connector.fetch({
        endpoint: '/getCommonJobCodeList',
        params,
      });

      logger.debug('[COMMON-CODE] Job codes response received');

      const normalized = CommonCodeAdapter.normalizeJobCodeResponse(response.data);

      if (!normalized.success) {
        logger.error('[COMMON-CODE] Failed to fetch job codes:', { error: normalized.error });
      } else {
        logger.debug(`[COMMON-CODE] Found ${normalized.totalCount} job codes`);
      }

      return normalized;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      logger.error('[COMMON-CODE] Error fetching job codes:', { error: errorMessage });
      return {
        success: false,
        totalCount: 0,
        pageNo: 1,
        numOfRows: 0,
        data: [],
        error: {
          code: 'FETCH_ERROR',
          message: errorMessage,
        },
      };
    }
  }

  /**
   * 학력코드 조회
   *
   * @param apiKey 공공데이터포털 API 키
   * @returns 학력코드 목록
   */
  static async getEducationCodes(apiKey: string): Promise<NormalizedCodeResponse<EducationCode>> {
    logger.debug('[COMMON-CODE] Fetching education codes...');

    const params = {
      pageNo: 1,
      numOfRows: 100,
      resultType: 'json',
    };

    try {
      const config = ApiRegistry.getInstance().get('public_data_common_code');
      if (!config) {
        throw new Error('CommonCode API configuration not found in registry');
      }

      const connector = ApiConnectorFactory.create(config, apiKey);
      const response = await connector.fetch({
        endpoint: '/getCommonEduBckgrdCodeList',
        params,
      });

      logger.debug('[COMMON-CODE] Education codes response received');

      const normalized = CommonCodeAdapter.normalizeEducationCodeResponse(response.data);

      if (!normalized.success) {
        logger.error('[COMMON-CODE] Failed to fetch education codes:', { error: normalized.error });
      } else {
        logger.debug(`[COMMON-CODE] Found ${normalized.totalCount} education codes`);
      }

      return normalized;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      logger.error('[COMMON-CODE] Error fetching education codes:', { error: errorMessage });
      return {
        success: false,
        totalCount: 0,
        pageNo: 1,
        numOfRows: 0,
        data: [],
        error: {
          code: 'FETCH_ERROR',
          message: errorMessage,
        },
      };
    }
  }

  /**
   * 선거ID로 선거 정보 조회 (헬퍼 메서드)
   *
   * @param apiKey 공공데이터포털 API 키
   * @param electionId 선거ID (예: "20220309")
   * @returns 선거 정보 또는 null
   */
  static async getElectionInfo(apiKey: string, electionId: string): Promise<ElectionCode | null> {
    const result = await this.getElectionCodes(apiKey);

    if (!result.success || !result.data) {
      return null;
    }

    return CommonCodeAdapter.filterElectionById(result.data, electionId);
  }

  /**
   * 선거명으로 선거 정보 검색 (헬퍼 메서드)
   *
   * @param apiKey 공공데이터포털 API 키
   * @param keyword 검색 키워드 (예: "대통령", "2022")
   * @returns 선거 정보 배열
   */
  static async searchElections(apiKey: string, keyword: string): Promise<ElectionCode[]> {
    const result = await this.getElectionCodes(apiKey);

    if (!result.success || !result.data) {
      return [];
    }

    return CommonCodeAdapter.filterElectionByName(result.data, keyword);
  }

  /**
   * 시도명으로 시군구 검색 (헬퍼 메서드)
   *
   * @param apiKey 공공데이터포털 API 키
   * @param provinceName 시도명 (예: "서울특별시")
   * @returns 시군구 배열
   */
  static async getDistrictsByProvince(apiKey: string, provinceName: string): Promise<DistrictCode[]> {
    const result = await this.getDistrictCodes(apiKey);

    if (!result.success || !result.data) {
      return [];
    }

    return CommonCodeAdapter.filterDistrictByProvince(result.data, provinceName);
  }

  /**
   * 정당명으로 정당 검색 (헬퍼 메서드)
   *
   * @param apiKey 공공데이터포털 API 키
   * @param sgId 선거ID
   * @param sgTypecode 선거종류코드
   * @param keyword 검색 키워드 (예: "민주", "국민의힘")
   * @returns 정당 배열
   */
  static async searchParties(
    apiKey: string,
    sgId: string,
    sgTypecode: string,
    keyword: string
  ): Promise<PartyCode[]> {
    const result = await this.getPartyCodes(apiKey, sgId, sgTypecode);

    if (!result.success || !result.data) {
      return [];
    }

    return CommonCodeAdapter.filterPartyByName(result.data, keyword);
  }
}

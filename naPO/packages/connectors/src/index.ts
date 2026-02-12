/**
 * @labgod/connectors
 *
 * API Connectors for Korean public data sources
 * Used by: naPO, naON, and other Labgod apps
 *
 * Supported APIs:
 * - KOSIS (통계청 - 국가통계포털)
 * - ECOS (한국은행 경제통계시스템)
 * - R-ONE (한국부동산원)
 * - HUG (주택도시보증공사)
 * - Local Finance (지방재정365)
 * - NABO Stats (국회예산정책처)
 *
 * @packageDocumentation
 */

// Internal imports for createConnector factory
import { BaseConnector } from './base';
import { KosisConnector } from './kosis';
import { EcosConnector } from './ecos';
import { RoneConnector } from './rone';
import { HugConnector } from './hug';
import { LocalFinanceConnector } from './local-finance';
import { NaboStatsConnector } from './nabo-stats';

// Base connector
export { BaseConnector, type ConnectorOptions } from './base';

// KOSIS (통계청)
export {
  KosisConnector,
  KosisAdapter,
  KOSIS_CONFIG,
  type KosisConnectorOptions,
  type KosisStatListItem,
  type KosisStatDataItem,
  type KosisParamItem,
} from './kosis';

// ECOS (한국은행)
export {
  EcosConnector,
  EcosAdapter,
  ECOS_CONFIG,
  type EcosConnectorOptions,
  type EcosStatItem,
  type EcosStatTableItem,
  type EcosKeyStatItem,
  type EcosEndpoint,
} from './ecos';

// R-ONE (한국부동산원)
export {
  RoneConnector,
  RoneAdapter,
  RONE_CONFIG,
  type RoneConnectorOptions,
  type RoneTableListItem,
  type RoneTableItemsItem,
  type RoneTableDataItem,
  type RoneNormalizedResponse,
} from './rone';

// HUG (주택도시보증공사)
export {
  HugConnector,
  HugAdapter,
  HUG_CONFIG,
  type HugConnectorOptions,
  type HugEndpointType,
  type HugDistributionGuaranteeItem,
  type HugGuaranteeAmountItem,
  type HugConstructionRateItem,
  type HugPfLoanItem,
  type HugDistributionPerformanceItem,
  type HugNewDistributionItem,
  type HugPriceIndexItem,
  type HugPricePerSqmItem,
  type HugNormalizedResponse,
} from './hug';

// Local Finance (지방재정365)
export {
  LocalFinanceConnector,
  LocalFinanceAdapter,
  LOCAL_FINANCE_CONFIG,
  type LocalFinanceConnectorOptions,
  type LocalFinanceEndpointType,
  type LocalFinanceExpItem,
  type LocalFinanceRatioItem,
  type LocalFinanceDebtItem,
  type LocalFinanceBudgetItem,
  type LocalFinanceNormalizedResponse,
} from './local-finance';

// NABOSTATS (국회예산정책처)
export {
  NaboStatsConnector,
  NaboStatsAdapter,
  NABOSTATS_CONFIG,
  type NaboStatsConnectorOptions,
  type NaboEndpointType,
  type NaboTableItem,
  type NaboTableItemDetail,
  type NaboDataItem,
  type NaboDictionaryItem,
  type NaboNormalizedResponse,
} from './nabo-stats';

// Re-export core types for convenience
export type {
  ConnectorConfig,
  ConnectorStatus,
  NormalizedResponse,
  QueryFilters,
  ApiError,
} from '@labgod/core-types';

/**
 * Connector type union - All supported connectors
 */
export type ConnectorType = 'kosis' | 'ecos' | 'rone' | 'hug' | 'local_finance' | 'nabostats';

/**
 * Create a connector by type
 */
export function createConnector(
  type: 'kosis' | 'ecos' | 'rone' | 'hug' | 'local_finance' | 'nabostats',
  options: { apiKey: string; debug?: boolean }
): BaseConnector;
export function createConnector(
  type: ConnectorType,
  options: { apiKey?: string; debug?: boolean }
): BaseConnector {
  switch (type) {
    case 'kosis':
      if (!options.apiKey) throw new Error('KOSIS connector requires apiKey');
      return new KosisConnector({ apiKey: options.apiKey, debug: options.debug });
    case 'ecos':
      if (!options.apiKey) throw new Error('ECOS connector requires apiKey');
      return new EcosConnector({ apiKey: options.apiKey, debug: options.debug });
    case 'rone':
      if (!options.apiKey) throw new Error('R-ONE connector requires apiKey');
      return new RoneConnector({ apiKey: options.apiKey, debug: options.debug });
    case 'hug':
      if (!options.apiKey) throw new Error('HUG connector requires apiKey');
      return new HugConnector({ apiKey: options.apiKey, debug: options.debug });
    case 'local_finance':
      if (!options.apiKey) throw new Error('LocalFinance connector requires apiKey');
      return new LocalFinanceConnector({ apiKey: options.apiKey, debug: options.debug });
    case 'nabostats':
      if (!options.apiKey) throw new Error('NaboStats connector requires apiKey');
      return new NaboStatsConnector({ apiKey: options.apiKey, debug: options.debug });
    default:
      throw new Error(`Unknown connector type: ${type}`);
  }
}

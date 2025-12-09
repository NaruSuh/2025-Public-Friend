import { Router, Request, Response } from 'express';
import { NLQueryEngine } from '@/services/nlp/queryEngine';
import { ApiConnectorFactory } from '@/services/api/customConnector';
import { CrawlerFactory } from '@/services/crawler/crawlerFactory';
import { ApiRegistry } from '@/config/apis';
import { prisma } from '@/lib/prisma';
import { getApiKey } from '@/lib/apiKeyHelper';
import { StubDataGenerator } from '@/services/api/stubDataGenerator';
import { parseQueryValidation, executeQueryValidation } from '@/api/validators/query.validators';
import { validationResult } from 'express-validator';
import { requireNLQuery } from '@/middleware/featureFlag.middleware';
import { RoneAdapter } from '@/services/api/adapters/roneAdapter';
import { NecManifestoAdapter } from '@/services/api/adapters/necManifestoAdapter';
import { PartyPolicyAdapter } from '@/services/api/adapters/partyPolicyAdapter';
import { WinnerInfoAdapter } from '@/services/api/adapters/winnerInfoAdapter';
import { NecApiChainService } from '@/services/api/necApiChainService';
import { logger } from '@/config/logger';

const router = Router();
const nlEngine = new NLQueryEngine();

// 자연어 쿼리 처리
router.post('/', requireNLQuery, parseQueryValidation, async (req: Request, res: Response) => {
  try {
    // Check validation errors
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid request data',
          details: errors.array(),
        },
      });
    }

    const { query } = req.body;

    // Sanitize query string
    const sanitizedQuery = query.trim();

    // Additional safety check
    if (sanitizedQuery.length === 0) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'EMPTY_QUERY',
          message: 'Query cannot be empty',
        },
      });
    }

    // 자연어 쿼리 파싱
    const parsed = await nlEngine.parseQuery(sanitizedQuery);

    return res.json({
      success: true,
      data: parsed,
    });
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

// 파싱된 쿼리 실행
router.post('/execute', requireNLQuery, executeQueryValidation, async (req: Request, res: Response) => {
  try {
    // Check validation errors
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid request data',
          details: errors.array(),
        },
      });
    }

    const { parsedQuery } = req.body;

    let result;
    let executionError = null;

    try {
      switch (parsedQuery.intent) {
        case 'fetch_api': {
          // Use stub data in test environment
          if (process.env.NODE_ENV === 'test') {
            logger.debug(`[TEST MODE] Generating stub data for source: ${parsedQuery.source.id}`);
            const stubData = StubDataGenerator.generate({
              source: parsedQuery.source.id || 'generic',
              filters: parsedQuery.filters,
              count: parsedQuery.output.limit || 50,
            });
            result = { data: stubData, source: parsedQuery.source.id, isStubData: true };
            break;
          }

          // Real API connector logic
          const sourceId = parsedQuery.source.id;
          if (!sourceId) {
            throw new Error('API source ID is required for fetch_api intent');
          }

          // Get API configuration from registry
          const apiRegistry = ApiRegistry.getInstance();
          const apiConfig = apiRegistry.get(sourceId);
          if (!apiConfig) {
            throw new Error(`Unknown API source: ${sourceId}`);
          }

          // Find API source in database by name
          const apiSource = await prisma.apiSource.findFirst({
            where: { name: sourceId },
          });

          if (!apiSource) {
            throw new Error(`API source not found in database: ${sourceId}`);
          }

          // Fetch and decrypt API key from database using the source's name
          const apiKeyValue = await getApiKey(sourceId);

          if (!apiKeyValue) {
            throw new Error(`No active API key found for source: ${sourceId}`);
          }

          // Create connector with timeout and retry logic
          const connector = ApiConnectorFactory.create(apiConfig, apiKeyValue);

          try {
            // Prepare API parameters - use adapter for R-ONE
            let apiParams = parsedQuery.filters || {};
            let endpoint: string;
            let normalizedData: any;

            if (sourceId === 'rone') {
              logger.debug('[R-ONE] NLP integration for R-ONE not yet implemented');
              // TODO: Implement NLP filter adaptation for R-ONE
              // apiParams = RoneAdapter.adaptFilters(parsedQuery.filters);
              // const validation = RoneAdapter.validateParams(apiParams);
              throw new Error('R-ONE NLP query integration not yet implemented. Use RoneService directly.');
            } else if (sourceId === 'public_data_party_policy') {
              logger.debug('[PARTY-POLICY] Adapting filters to Party Policy API format');
              logger.debug('[PARTY-POLICY] Original filters:', JSON.stringify(parsedQuery.filters));

              // Use adapter pattern for filter conversion
              let adaptedParams = PartyPolicyAdapter.adaptFilters(parsedQuery.filters);

              // Infer missing params from context
              adaptedParams = PartyPolicyAdapter.inferMissingParams(adaptedParams, {
                keywords: parsedQuery.filters.keywords,
                query: parsedQuery.rawQuery,
              });

              logger.debug('[PARTY-POLICY] Adapted params:', JSON.stringify(adaptedParams));

              // Extract election IDs
              let electionIds: string[] = [];
              if (adaptedParams.sgId) {
                electionIds = [adaptedParams.sgId];
              } else if (parsedQuery.filters.sgId) {
                electionIds = Array.isArray(parsedQuery.filters.sgId)
                  ? parsedQuery.filters.sgId
                  : [parsedQuery.filters.sgId];
              }

              logger.debug('[PARTY-POLICY] Election IDs to query:', electionIds);

              // Determine party names to query
              let partyNames: string[] = [];
              if (adaptedParams.partyName) {
                // Specific party from adapter
                partyNames = [adaptedParams.partyName];
              } else if (adaptedParams._queryAllMajorParties) {
                // Query all major parties
                partyNames = PartyPolicyAdapter.getMajorParties();
              } else {
                // Fallback: Extract from keywords or use major parties
                const genericKeywords = ['공약', '정책', '지방선거', '총선', '대선', '주요정당'];
                const partyKeywords = (parsedQuery.filters.keywords || []).filter(
                  (k: string) => !genericKeywords.includes(k)
                );
                partyNames = partyKeywords.length > 0
                  ? partyKeywords.map((k: string) => PartyPolicyAdapter.normalizePartyName(k))
                  : PartyPolicyAdapter.getMajorParties();
              }

              logger.debug('[PARTY-POLICY] Will query parties:', partyNames);

              // Query each party for each election and aggregate results
              const allPolicies: any[] = [];
              const successParties: string[] = [];
              const failedParties: string[] = [];
              const queriedCombinations: string[] = [];

              // If no election IDs specified, use adapter's default
              if (electionIds.length === 0) {
                electionIds = [PartyPolicyAdapter.getRecentElectionIds()[0] || '20220601'];
                logger.debug('[PARTY-POLICY] No election IDs found, using default:', electionIds);
              }

              const baseParams = {
                pageNo: adaptedParams.pageNo || 1,
                numOfRows: adaptedParams.numOfRows || 100,
                resultType: adaptedParams.resultType || 'json',
              };

              for (const sgId of electionIds) {
                logger.debug(`[PARTY-POLICY] Querying election: ${sgId}`);

                for (const partyName of partyNames) {
                  const partyParams = { ...baseParams, sgId, partyName };
                  const combinationKey = `${sgId}-${partyName}`;
                  queriedCombinations.push(combinationKey);
                  logger.debug(`[PARTY-POLICY] Querying: ${combinationKey}`);

                  try {
                    const partyResponse = await connector.fetch({
                      endpoint: '/getPartyPlcInfoInqire',
                      params: partyParams,
                    });

                    const normalized = PartyPolicyAdapter.normalizeResponse(partyResponse.data);
                    if (normalized.success && normalized.data?.length > 0) {
                      // Add election ID to each policy for traceability
                      const policiesWithElection = normalized.data.map((policy: any) => ({
                        ...policy,
                        _electionId: sgId,
                      }));
                      allPolicies.push(...policiesWithElection);
                      if (!successParties.includes(partyName)) {
                        successParties.push(partyName);
                      }
                    } else {
                      // Only mark as failed if no success for this party yet
                      if (!successParties.includes(partyName) && !failedParties.includes(partyName)) {
                        failedParties.push(partyName);
                      }
                    }
                  } catch (partyError: any) {
                    logger.warn(`[PARTY-POLICY] Failed to fetch policies for ${combinationKey}:`, { error: partyError.message });
                    // Only mark as failed if no success for this party yet
                    if (!successParties.includes(partyName) && !failedParties.includes(partyName)) {
                      failedParties.push(partyName);
                    }
                    // Continue with other parties/elections
                  }
                }
              }

              // Clean up failedParties - remove any that actually succeeded in at least one election
              const actuallyFailed = failedParties.filter(p => !successParties.includes(p));

              logger.debug(`[PARTY-POLICY] Total policies fetched: ${allPolicies.length}`);
              logger.debug(`[PARTY-POLICY] Elections queried: ${electionIds.length}`);
              logger.debug(`[PARTY-POLICY] Success parties: ${successParties.join(', ')}`);
              logger.debug(`[PARTY-POLICY] Failed parties: ${actuallyFailed.join(', ')}`);

              // Set normalized data
              normalizedData = {
                success: true,
                totalCount: allPolicies.length,
                data: allPolicies,
              };

              // Set result directly
              result = {
                data: normalizedData,
                source: sourceId,
                isStubData: false,
                metadata: {
                  statusCode: 200,
                  timestamp: new Date().toISOString(),
                  apiChainUsed: true,
                  queriedParties: partyNames,
                  debug: {
                    electionIds,
                    electionsQueried: electionIds.length,
                    successCount: successParties.length,
                    failedCount: actuallyFailed.length,
                    successParties,
                    failedParties: actuallyFailed,
                    queriedCombinations,
                    originalFilters: parsedQuery.filters,
                    adaptedParams,
                    inferredInfo: adaptedParams._inferred,
                  },
                },
              };

              // Break early - we already have the result
              break;
            } else if (sourceId === 'public_data_election') {
              logger.debug('[NEC-MANIFESTO] Adapting filters to NEC Manifesto API format');
              logger.debug('[NEC-MANIFESTO] Original filters:', JSON.stringify(parsedQuery.filters));

              // Convert natural language filters to NEC Manifesto API parameters
              apiParams = NecManifestoAdapter.adaptFilters(parsedQuery.filters);

              // Infer missing params from context (candidate name, election info)
              apiParams = NecManifestoAdapter.inferMissingParams(apiParams, {
                keywords: parsedQuery.filters.keywords,
                query: parsedQuery.rawQuery,
              });

              logger.debug('[NEC-MANIFESTO] Adapted params:', JSON.stringify(apiParams));
              if (apiParams._inferred) {
                logger.debug('[NEC-MANIFESTO] Inferred info:', JSON.stringify(apiParams._inferred));
              }

              // ⚠️ Check if cnddtId is missing - if so, use API chain
              if (!apiParams.cnddtId && parsedQuery.filters.keywords?.length > 0) {
                logger.debug('[NEC-MANIFESTO] cnddtId not provided, initiating API chain...');
                logger.debug('[NEC-MANIFESTO] Candidate name from keywords:', parsedQuery.filters.keywords);

                // Extract candidate name from keywords
                // Filter out generic keywords like "공약", "정책", "주요정당"
                const genericKeywords = ['공약', '정책', '주요정당', '지방선거', '총선', '대선'];
                const candidateKeywords = parsedQuery.filters.keywords.filter(
                  (k: string) => !genericKeywords.includes(k)
                );

                if (candidateKeywords.length === 0) {
                  throw new Error(
                    'NEC Manifesto API requires specific candidate name. ' +
                    'Please provide a candidate name (e.g., "윤석열", "이재명") or candidate ID (cnddtId). ' +
                    'Queries like "주요정당 공약" are not supported by the NEC API.'
                  );
                }

                const candidateName = candidateKeywords[0];

                // Use API chain to get pledges by candidate name
                const chainResult = await NecApiChainService.getCandidatePledgesByName(
                  apiParams.sgId,
                  apiParams.sgTypecode,
                  candidateName,
                  apiKeyValue
                );

                // Return chain result directly (skip normal API flow)
                normalizedData = chainResult;

                result = {
                  data: normalizedData,
                  source: sourceId,
                  isStubData: false,
                  metadata: {
                    apiChainUsed: true,
                    stages: ['candidate_lookup', 'manifesto_lookup'],
                    timestamp: new Date().toISOString(),
                    debug: {
                      candidateName,
                      originalFilters: parsedQuery.filters,
                      adaptedParams: apiParams,
                    },
                  },
                };

                // Break early - we already have the result from API chain
                break;
              }

              // cnddtId provided - use normal single API call
              logger.debug('[NEC-MANIFESTO] cnddtId provided, using direct API call');

              // Validate parameters
              const validation = NecManifestoAdapter.validateParams(apiParams);
              if (!validation.valid) {
                throw new Error(`Invalid NEC Manifesto parameters: ${validation.errors.join(', ')}`);
              }

              // NEC Manifesto specific: use getPromises endpoint
              if (!apiConfig.endpoints || !apiConfig.endpoints.getPromises) {
                throw new Error('NEC Manifesto API endpoints not configured');
              }
              endpoint = apiConfig.endpoints.getPromises;
              if (!endpoint) {
                throw new Error('NEC Manifesto getPromises endpoint not configured');
              }
            } else if (sourceId === 'public_data_winner') {
              // 당선인 정보 API 핸들러
              logger.debug('[WINNER-INFO] Adapting filters to Winner Info API format');
              logger.debug('[WINNER-INFO] Original filters:', JSON.stringify(parsedQuery.filters));

              // Convert natural language filters to Winner Info API parameters
              apiParams = WinnerInfoAdapter.adaptFilters(parsedQuery.filters);

              // Use inferMissingParams to automatically infer sgId, sgTypecode from context
              apiParams = WinnerInfoAdapter.inferMissingParams(apiParams, {
                keywords: parsedQuery.filters.keywords,
                query: parsedQuery.rawQuery,
              });

              logger.debug('[WINNER-INFO] Adapted params:', JSON.stringify(apiParams));
              if (apiParams._inferred) {
                logger.debug('[WINNER-INFO] Inferred info:', JSON.stringify(apiParams._inferred));
              }

              // Validate parameters (with warnings for optional params)
              const winnerValidation = WinnerInfoAdapter.validateParams(apiParams);
              if (!winnerValidation.valid) {
                throw new Error(
                  `당선인 정보 조회를 위해 선거 정보가 필요합니다. ` +
                  `예: "2022년 지방선거 당선자", "2024년 총선 당선인". ` +
                  `오류: ${winnerValidation.errors.join(', ')}`
                );
              }

              // Log warnings if any
              if (winnerValidation.warnings.length > 0) {
                logger.warn('[WINNER-INFO] Warnings:', winnerValidation.warnings.join(', '));
              }

              // Use getWinners endpoint
              if (!apiConfig.endpoints || !apiConfig.endpoints.getWinners) {
                throw new Error('Winner Info API endpoints not configured');
              }
              endpoint = apiConfig.endpoints.getWinners;
              if (!endpoint) {
                throw new Error('Winner Info getWinners endpoint not configured');
              }

              logger.debug(`[WINNER-INFO] Querying with sgId=${apiParams.sgId}, sgTypecode=${apiParams.sgTypecode}`);

              // Execute API request
              const winnerResponse = await Promise.race([
                connector.fetch({
                  endpoint: endpoint,
                  params: apiParams,
                }),
                new Promise((_, reject) =>
                  setTimeout(() => reject(new Error('API request timeout')), 30000)
                ),
              ]) as any;

              // Normalize response
              normalizedData = WinnerInfoAdapter.normalizeResponse(winnerResponse.data);

              // Check for API errors
              if (!normalizedData.success && normalizedData.error) {
                throw new Error(
                  `당선인 정보 조회 실패: ${normalizedData.error.message || WinnerInfoAdapter.interpretErrorCode(normalizedData.error.code)}`
                );
              }

              // 득표율 쿼리인 경우 결과 필터링
              if (apiParams._queryType === 'vote_rate' && normalizedData.data) {
                logger.debug('[WINNER-INFO] Vote rate query detected, filtering results...');
                let filteredData = normalizedData.data;

                // 후보자 이름으로 필터링
                if (apiParams._filterCandidate) {
                  filteredData = filteredData.filter((item: any) =>
                    item.nameKr === apiParams._filterCandidate ||
                    item._raw?.name === apiParams._filterCandidate
                  );
                  logger.debug(`[WINNER-INFO] Filtered by candidate: ${apiParams._filterCandidate}, results: ${filteredData.length}`);
                }

                // 정당으로 필터링
                if (apiParams._filterParty) {
                  filteredData = filteredData.filter((item: any) =>
                    item.party === apiParams._filterParty ||
                    item._raw?.jdName === apiParams._filterParty ||
                    item.party?.includes(apiParams._filterParty) ||
                    apiParams._filterParty?.includes(item.party)
                  );
                  logger.debug(`[WINNER-INFO] Filtered by party: ${apiParams._filterParty}, results: ${filteredData.length}`);
                }

                // 득표율 정보만 추출하여 요약 생성
                if (filteredData.length > 0) {
                  normalizedData.voteRateSummary = filteredData.map((item: any) => ({
                    name: item.nameKr,
                    party: item.party,
                    voteCount: item.voteCount,
                    voteRate: item.voteRate,
                    constituency: item.constituencyName,
                    electionName: item.electionName,
                  }));
                  normalizedData.data = filteredData;
                  normalizedData.totalCount = filteredData.length;
                  logger.debug('[WINNER-INFO] Vote rate summary generated:', JSON.stringify(normalizedData.voteRateSummary));
                } else {
                  // 필터링 결과 없음 - 전체 데이터에서 득표율 있는 항목만 반환
                  const dataWithVoteRate = normalizedData.data.filter((item: any) =>
                    item.voteRate !== null && item.voteRate !== undefined
                  );
                  if (dataWithVoteRate.length > 0) {
                    normalizedData.data = dataWithVoteRate;
                    normalizedData.totalCount = dataWithVoteRate.length;
                    normalizedData.message = '검색 조건에 맞는 특정 후보자/정당을 찾지 못해 전체 득표율 데이터를 반환합니다.';
                  }
                }
              }

              result = {
                data: normalizedData,
                source: sourceId,
                isStubData: false,
                metadata: {
                  statusCode: winnerResponse.statusCode || 200,
                  timestamp: new Date().toISOString(),
                  electionId: apiParams.sgId,
                  electionType: apiParams.sgTypecode,
                  queryType: apiParams._queryType,
                  debug: {
                    originalFilters: parsedQuery.filters,
                    adaptedParams: apiParams,
                  },
                },
              };

              // Break early - we already have the result
              break;
            } else {
              // For other APIs, use specified endpoint or first available
              const endpoints = apiConfig.endpoints || {};
              endpoint = parsedQuery.endpoint || Object.values(endpoints)[0];
              if (!endpoint) {
                throw new Error(`No valid endpoint found for API: ${sourceId}`);
              }
            }

            logger.debug(`[API] Using endpoint: ${endpoint}`);

            // Execute API request with adapted filters
            const apiResponse = await Promise.race([
              connector.fetch({
                endpoint: endpoint,
                params: apiParams,
              }),
              new Promise((_, reject) =>
                setTimeout(() => reject(new Error('API request timeout')), 30000)
              ),
            ]) as any;

            // Apply API-specific response normalization
            normalizedData = apiResponse.data;
            if (sourceId === 'rone') {
              logger.debug('[R-ONE] Using raw response (NLP normalization not yet implemented)');
              // TODO: Implement normalized response for NLP queries
              // normalizedData = RoneAdapter.normalizeResponse(apiResponse.data, apiParams);
            } else if (sourceId === 'public_data_party_policy') {
              logger.debug('[PARTY-POLICY] Normalizing response');
              normalizedData = PartyPolicyAdapter.normalizeResponse(apiResponse.data);
            } else if (sourceId === 'public_data_election') {
              logger.debug('[NEC-MANIFESTO] Normalizing response');
              normalizedData = NecManifestoAdapter.normalizeResponse(apiResponse.data);
            } else if (sourceId === 'public_data_winner') {
              logger.debug('[WINNER-INFO] Normalizing response');
              normalizedData = WinnerInfoAdapter.normalizeResponse(apiResponse.data);
            }

            result = {
              data: normalizedData,
              source: sourceId,
              isStubData: false,
              metadata: {
                statusCode: apiResponse.statusCode,
                timestamp: new Date().toISOString(),
              },
            };
          } catch (apiError: any) {
            logger.error(`API request failed for ${sourceId}:`, { error: apiError.message, stack: apiError.stack });
            throw new Error(`API request failed: ${apiError.message}`);
          }
          break;
        }

        case 'crawl_site': {
          // Use stub data in test environment
          if (process.env.NODE_ENV === 'test') {
            logger.debug(`[TEST MODE] Generating stub crawler data for source: ${parsedQuery.source.id}`);
            result = {
              data: StubDataGenerator.generate({
                source: parsedQuery.source.id || 'generic',
                filters: parsedQuery.filters,
                count: 20,
              }),
              source: parsedQuery.source.id,
              isStubData: true,
            };
            break;
          }

          // Real crawler logic
          const crawlerType = parsedQuery.source.crawlerType;
          if (!crawlerType) {
            throw new Error('Crawler type is required for crawl_site intent');
          }

          // Check if crawler is available
          const isAvailable = await CrawlerFactory.isAvailable(crawlerType);
          if (!isAvailable) {
            const availableCrawlers = await CrawlerFactory.getAvailableCrawlers();
            return res.status(503).json({
              success: false,
              error: {
                code: 'SERVICE_UNAVAILABLE',
                message: `Crawler type '${crawlerType}' is not yet implemented or unavailable`,
                availableCrawlers,
              },
            });
          }

          // Create crawler with timeout
          const crawler = CrawlerFactory.create(crawlerType);

          try {
            const crawlResult = await Promise.race([
              crawler.crawl({
                url: parsedQuery.source.url || '',
                filters: parsedQuery.filters,
              }),
              new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Crawler timeout')), 60000)
              ),
            ]) as any;

            result = {
              data: crawlResult.items,
              source: parsedQuery.source.id,
              isStubData: false,
              metadata: {
                itemCount: crawlResult.itemCount,
                pagesProcessed: crawlResult.metadata?.pagesProcessed,
                timestamp: new Date().toISOString(),
              },
            };
          } catch (crawlError: any) {
            logger.error(`Crawl failed for ${crawlerType}:`, { error: crawlError.message });
            throw new Error(`Crawl failed: ${crawlError.message}`);
          }
          break;
        }

        case 'analyze_data':
        case 'export_data': {
          // These intents are essentially fetch requests with post-processing
          // If source is available, treat as fetch_api and return data for client-side processing
          if (parsedQuery.source?.id) {
            logger.debug(`[${parsedQuery.intent.toUpperCase()}] Treating as fetch_api for source: ${parsedQuery.source.id}`);

            // Convert to fetch_api intent and let the next iteration handle it
            const originalIntent = parsedQuery.intent;
            parsedQuery.intent = 'fetch_api';

            // Note: This is a bit hacky - ideally we'd refactor to avoid code duplication
            // For now, return an error that guides users, or we can implement proper recursion later
            result = {
              data: {
                success: false,
                message: `Query parsed as '${originalIntent}'. Data fetching initiated - please use 'fetch_api' intent directly or rephrase your query (e.g., "지방선거 공약 가져와").`,
                suggestedQuery: parsedQuery.rawQuery?.replace(/요약|분석|정리/g, '가져와') || '지방선거 공약 가져와',
              },
              source: parsedQuery.source.id,
              isStubData: false,
              metadata: {
                originalIntent,
                timestamp: new Date().toISOString(),
              },
            };
            break;
          }
          throw new Error(
            `데이터 소스를 찾을 수 없습니다. "지방선거 공약 가져와" 처럼 구체적으로 질문해주세요.`
          );
        }

        case 'parse_pdf': {
          throw new Error(
            `PDF 파싱 기능은 아직 구현되지 않았습니다.`
          );
        }

        default:
          throw new Error(`Unsupported intent: ${parsedQuery.intent}`);
      }
    } catch (error: any) {
      executionError = error.message;
      throw error;
    } finally {
      // Save query to history
      await prisma.queryHistory
        .create({
          data: {
            naturalQuery: parsedQuery.rawQuery || '',
            parsedIntent: parsedQuery.intent || 'unknown',
            parsedParams: parsedQuery,
            resultCount: result?.data?.length || 0,
          },
        })
        .catch(() => {
          // Ignore history save errors to not block the main response
        });
    }

    return res.json({
      success: true,
      data: result,
    });
  } catch (error: any) {
    logger.error('[QUERY EXECUTE ERROR]:', { error: error.message, stack: error.stack });

    // Return 400 for validation/user input errors, 500 for server errors
    const isValidationError = error.message.includes('requires specific candidate name') ||
                              error.message.includes('is required') ||
                              error.message.includes('Invalid') ||
                              error.message.includes('not supported');

    const statusCode = isValidationError ? 400 : 500;
    return res.status(statusCode).json({ error: error.message });
  }
});

export default router;

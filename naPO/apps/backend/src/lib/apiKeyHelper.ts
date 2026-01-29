import { prisma } from './prisma';
import { logger } from '@/config/logger';

/**
 * Get active API key for a given source
 * @param sourceName - The name/id of the API source (e.g., 'public_data_election')
 * @returns The API key value or null if not found
 */
export async function getApiKey(sourceName: string): Promise<string | null> {
  try {
    // First try to find by source name
    const apiSource = await prisma.apiSource.findFirst({
      where: {
        OR: [{ name: sourceName }, { id: sourceName }],
        isActive: true,
      },
      include: {
        apiKeys: {
          where: { isActive: true },
          orderBy: { createdAt: 'desc' },
          take: 1,
        },
      },
    });

    if (apiSource?.apiKeys?.[0]?.keyValue) {
      return apiSource.apiKeys[0].keyValue;
    }

    // Fallback to environment variables
    const envKeyMap: Record<string, string | undefined> = {
      public_data_election: process.env.PUBLIC_DATA_API_KEY,
      public_data_winner: process.env.PUBLIC_DATA_API_KEY,
      public_data_candidate: process.env.PUBLIC_DATA_API_KEY,
      public_data_party_policy: process.env.PUBLIC_DATA_API_KEY,
      public_data_common_code: process.env.PUBLIC_DATA_API_KEY,
      rone: process.env.RONE_API_KEY,
      nabostats: process.env.NABOSTATS_API_KEY,
    };

    const envKey = envKeyMap[sourceName];
    if (envKey) {
      logger.debug(`Using environment variable for API key: ${sourceName}`);
      return envKey;
    }

    logger.warn(`No API key found for source: ${sourceName}`);
    return null;
  } catch (error) {
    logger.error(`Error fetching API key for ${sourceName}:`, { error });
    return null;
  }
}

/**
 * Check if an API source has a valid key configured
 */
export async function hasValidApiKey(sourceName: string): Promise<boolean> {
  const key = await getApiKey(sourceName);
  return key !== null && key.length > 0;
}

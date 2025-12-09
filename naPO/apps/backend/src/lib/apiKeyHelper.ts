import { prisma } from './prisma';
import { encrypt, decrypt, maskSensitiveData } from './encryption';

/**
 * Store an API key securely (encrypted)
 */
export async function storeApiKey(params: {
  sourceId: string;
  keyValue: string;
  label?: string;
  expiresAt?: Date;
}): Promise<{ id: string; maskedKey: string }> {
  const { sourceId, keyValue, label, expiresAt } = params;

  // Encrypt the API key before storing
  const encryptedKey = encrypt(keyValue);

  const apiKey = await prisma.apiKey.create({
    data: {
      sourceId,
      keyValue: encryptedKey,
      label: label || 'Default API Key',
      expiresAt,
      isActive: true,
    },
  });

  return {
    id: apiKey.id,
    maskedKey: maskSensitiveData(keyValue),
  };
}

/**
 * Retrieve and decrypt an API key by source name
 */
export async function getApiKey(sourceName: string): Promise<string | null> {
  // First, find the API source by name
  const apiSource = await prisma.apiSource.findFirst({
    where: { name: sourceName },
  });

  if (!apiSource) {
    console.warn(`API source not found: ${sourceName}`);
    return null;
  }

  // Then find the active API key for this source
  const apiKey = await prisma.apiKey.findFirst({
    where: {
      sourceId: apiSource.id,
      isActive: true,
      OR: [
        { expiresAt: null },
        { expiresAt: { gt: new Date() } }
      ],
    },
    orderBy: {
      createdAt: 'desc',
    },
  });

  if (!apiKey) {
    return null;
  }

  try {
    // Decrypt the API key
    return decrypt(apiKey.keyValue);
  } catch (error) {
    console.error(`Failed to decrypt API key for source ${sourceName}:`, error);
    throw new Error('Failed to decrypt API key');
  }
}

/**
 * Update an API key
 */
export async function updateApiKey(
  keyId: string,
  updates: {
    keyValue?: string;
    label?: string;
    isActive?: boolean;
    expiresAt?: Date;
  }
): Promise<{ maskedKey?: string }> {
  const data: any = { ...updates };

  // If updating the key value, encrypt it
  if (updates.keyValue) {
    data.keyValue = encrypt(updates.keyValue);
  }

  await prisma.apiKey.update({
    where: { id: keyId },
    data,
  });

  return {
    maskedKey: updates.keyValue ? maskSensitiveData(updates.keyValue) : undefined,
  };
}

/**
 * Delete (deactivate) an API key
 */
export async function deleteApiKey(keyId: string): Promise<void> {
  await prisma.apiKey.update({
    where: { id: keyId },
    data: { isActive: false },
  });
}

/**
 * List all API keys for a source (with masked values)
 */
export async function listApiKeys(sourceId: string): Promise<
  Array<{
    id: string;
    label: string | null;
    maskedKey: string;
    isActive: boolean;
    createdAt: Date;
    expiresAt: Date | null;
  }>
> {
  const apiKeys = await prisma.apiKey.findMany({
    where: { sourceId },
    orderBy: { createdAt: 'desc' },
  });

  return apiKeys.map((key) => {
    let maskedKey = '***';
    try {
      const decrypted = decrypt(key.keyValue);
      maskedKey = maskSensitiveData(decrypted);
    } catch (error) {
      // If decryption fails, show masked placeholder
      maskedKey = '*** (encrypted)';
    }

    return {
      id: key.id,
      label: key.label,
      maskedKey,
      isActive: key.isActive,
      createdAt: key.createdAt,
      expiresAt: key.expiresAt,
    };
  });
}

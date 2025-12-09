/**
 * 암호화 유틸리티 모듈
 *
 * API 키, 비밀번호 등 민감한 데이터를 안전하게 저장하기 위한
 * 암호화/복호화, 해싱 기능을 제공합니다.
 *
 * @module lib/encryption
 *
 * @example
 * ```typescript
 * import { encrypt, decrypt, hash, verifyHash } from '@/lib/encryption';
 *
 * // API 키 암호화/복호화
 * const encrypted = encrypt('sk-my-api-key-123');
 * const decrypted = decrypt(encrypted); // 'sk-my-api-key-123'
 *
 * // 비밀번호 해싱
 * const hashedPassword = hash('myPassword123');
 * const isValid = verifyHash('myPassword123', hashedPassword); // true
 * ```
 */
import crypto from 'crypto';

/**
 * 암호화 알고리즘 설정
 * AES-256-GCM은 인증된 암호화를 제공하여 기밀성과 무결성을 보장합니다.
 */
const ALGORITHM = 'aes-256-gcm';
/** 초기화 벡터(IV) 길이 (바이트) */
const IV_LENGTH = 16;
/** 인증 태그 길이 (바이트) - 사용되지 않지만 문서화 목적으로 유지 */
const AUTH_TAG_LENGTH = 16;
/** 해시용 솔트 길이 (바이트) */
const SALT_LENGTH = 64;

/**
 * Get encryption key from environment or generate one
 * WARNING: In production, this should come from a secure key management service (KMS)
 */
function getEncryptionKey(): Buffer {
  const key = process.env.ENCRYPTION_KEY;

  if (!key) {
    console.warn(
      'WARNING: ENCRYPTION_KEY not set in environment. Using default key. ' +
      'This is insecure for production use. Please set ENCRYPTION_KEY environment variable.'
    );
    // Default key for development only - DO NOT USE IN PRODUCTION
    return crypto.scryptSync('default-dev-key-change-in-production', 'salt', 32);
  }

  // Derive a 32-byte key from the environment variable
  return crypto.scryptSync(key, 'salt', 32);
}

/**
 * Encrypt sensitive data (like API keys) using AES-256-GCM
 * @param plaintext - The data to encrypt
 * @returns Base64-encoded encrypted data with IV and auth tag
 */
export function encrypt(plaintext: string): string {
  const key = getEncryptionKey();
  const iv = crypto.randomBytes(IV_LENGTH);
  const cipher = crypto.createCipheriv(ALGORITHM, key, iv);

  let encrypted = cipher.update(plaintext, 'utf8', 'hex');
  encrypted += cipher.final('hex');

  const authTag = cipher.getAuthTag();

  // Format: iv:authTag:encryptedData (all in hex)
  return `${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted}`;
}

/**
 * Decrypt sensitive data (like API keys) using AES-256-GCM
 * @param encryptedData - Base64-encoded encrypted data with IV and auth tag
 * @returns Decrypted plaintext
 */
export function decrypt(encryptedData: string): string {
  // Handle legacy unencrypted data (for backward compatibility during migration)
  if (!encryptedData.includes(':')) {
    console.warn('WARNING: Unencrypted data detected. Consider re-encrypting stored data.');
    return encryptedData;
  }

  const [ivHex, authTagHex, encrypted] = encryptedData.split(':');

  if (!ivHex || !authTagHex || encrypted === undefined) {
    throw new Error('Invalid encrypted data format');
  }

  const key = getEncryptionKey();
  const iv = Buffer.from(ivHex, 'hex');
  const authTag = Buffer.from(authTagHex, 'hex');

  const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
  decipher.setAuthTag(authTag);

  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');

  return decrypted;
}

/**
 * 데이터를 단방향 해시합니다.
 * 비밀번호나 토큰처럼 복호화가 필요 없는 데이터에 사용합니다.
 *
 * @param data - 해시할 원본 데이터
 * @returns salt:hash 형식의 해시된 문자열
 *
 * @example
 * ```typescript
 * const hashedPassword = hash('userPassword123');
 * // 결과: 'a1b2c3...salt...:d4e5f6...hash...'
 * ```
 */
export function hash(data: string): string {
  const salt = crypto.randomBytes(SALT_LENGTH).toString('hex');
  const hash = crypto.pbkdf2Sync(data, salt, 100000, 64, 'sha512').toString('hex');
  return `${salt}:${hash}`;
}

/**
 * 해시된 데이터를 검증합니다.
 *
 * @param data - 검증할 원본 데이터
 * @param hashedData - hash() 함수로 생성된 해시 문자열
 * @returns 데이터가 일치하면 true, 아니면 false
 *
 * @example
 * ```typescript
 * const storedHash = hash('password123');
 * verifyHash('password123', storedHash); // true
 * verifyHash('wrongPassword', storedHash); // false
 * ```
 */
export function verifyHash(data: string, hashedData: string): boolean {
  try {
    const [salt, originalHash] = hashedData.split(':');
    if (!salt || !originalHash) {
      return false;
    }
    const hash = crypto.pbkdf2Sync(data, salt, 100000, 64, 'sha512').toString('hex');
    return hash === originalHash;
  } catch (error) {
    return false;
  }
}

/**
 * 로깅용으로 민감한 데이터를 마스킹합니다.
 * 앞뒤 일부 문자만 보이고 중간은 별표(*)로 대체합니다.
 *
 * @param data - 마스킹할 데이터
 * @param visibleChars - 앞뒤로 보여줄 문자 수 (기본값: 4)
 * @returns 마스킹된 문자열
 *
 * @example
 * ```typescript
 * maskSensitiveData('sk-api-key-1234567890');
 * // 결과: 'sk-a**********7890'
 *
 * maskSensitiveData('short'); // '***' (너무 짧은 경우)
 * ```
 */
export function maskSensitiveData(data: string, visibleChars: number = 4): string {
  if (data.length <= visibleChars * 2) {
    return '***';
  }

  const start = data.substring(0, visibleChars);
  const end = data.substring(data.length - visibleChars);
  const middle = '*'.repeat(Math.min(data.length - visibleChars * 2, 10));

  return `${start}${middle}${end}`;
}

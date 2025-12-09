import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import { encrypt, decrypt, hash, verifyHash, maskSensitiveData } from '@/lib/encryption';

describe('Encryption Library', () => {
  const originalEnv = process.env.ENCRYPTION_KEY;

  afterEach(() => {
    // Restore original environment
    if (originalEnv !== undefined) {
      process.env.ENCRYPTION_KEY = originalEnv;
    } else {
      delete process.env.ENCRYPTION_KEY;
    }
  });

  describe('encrypt/decrypt', () => {
    it('should encrypt and decrypt data correctly', () => {
      const plaintext = 'my-secret-api-key-12345';
      const encrypted = encrypt(plaintext);
      const decrypted = decrypt(encrypted);

      expect(decrypted).toBe(plaintext);
    });

    it('should produce different encrypted values for same input (due to random IV)', () => {
      const plaintext = 'same-input-text';
      const encrypted1 = encrypt(plaintext);
      const encrypted2 = encrypt(plaintext);

      expect(encrypted1).not.toBe(encrypted2);
      expect(decrypt(encrypted1)).toBe(plaintext);
      expect(decrypt(encrypted2)).toBe(plaintext);
    });

    it('should handle empty string', () => {
      const encrypted = encrypt('');
      const decrypted = decrypt(encrypted);

      expect(decrypted).toBe('');
    });

    it('should handle unicode characters', () => {
      const plaintext = '한글 테스트 🔐 日本語';
      const encrypted = encrypt(plaintext);
      const decrypted = decrypt(encrypted);

      expect(decrypted).toBe(plaintext);
    });

    it('should handle long strings', () => {
      const plaintext = 'a'.repeat(10000);
      const encrypted = encrypt(plaintext);
      const decrypted = decrypt(encrypted);

      expect(decrypted).toBe(plaintext);
    });

    it('should return unencrypted data for legacy format (backward compatibility)', () => {
      const legacyData = 'plain-text-without-colons';
      const result = decrypt(legacyData);

      expect(result).toBe(legacyData);
    });

    it('should throw error for invalid encrypted format', () => {
      expect(() => decrypt('invalid:format')).toThrow('Invalid encrypted data format');
      expect(() => decrypt('::')).toThrow('Invalid encrypted data format');
    });
  });

  describe('hash/verifyHash', () => {
    it('should hash and verify data correctly', () => {
      const data = 'password123';
      const hashedData = hash(data);

      expect(verifyHash(data, hashedData)).toBe(true);
    });

    it('should produce different hashes for same input (due to random salt)', () => {
      const data = 'same-password';
      const hash1 = hash(data);
      const hash2 = hash(data);

      expect(hash1).not.toBe(hash2);
      expect(verifyHash(data, hash1)).toBe(true);
      expect(verifyHash(data, hash2)).toBe(true);
    });

    it('should reject wrong password', () => {
      const data = 'correct-password';
      const hashedData = hash(data);

      expect(verifyHash('wrong-password', hashedData)).toBe(false);
    });

    it('should return false for invalid hash format', () => {
      expect(verifyHash('data', 'invalid-hash-without-colon')).toBe(false);
      expect(verifyHash('data', '')).toBe(false);
    });

    it('should handle special characters in password', () => {
      const data = 'P@ssw0rd!#$%^&*()';
      const hashedData = hash(data);

      expect(verifyHash(data, hashedData)).toBe(true);
    });
  });

  describe('maskSensitiveData', () => {
    it('should mask middle characters of string', () => {
      const data = 'sk-api-key-1234567890';
      const masked = maskSensitiveData(data);

      expect(masked.startsWith('sk-a')).toBe(true);
      expect(masked.endsWith('7890')).toBe(true);
      expect(masked.includes('*')).toBe(true);
    });

    it('should return *** for short strings', () => {
      expect(maskSensitiveData('1234')).toBe('***');
      expect(maskSensitiveData('12345678')).toBe('***');
    });

    it('should respect custom visibleChars parameter', () => {
      const data = 'abcdefghijklmnop';
      const masked = maskSensitiveData(data, 2);

      expect(masked.startsWith('ab')).toBe(true);
      expect(masked.endsWith('op')).toBe(true);
    });

    it('should handle exact boundary case', () => {
      const data = '123456789'; // 9 chars
      const masked = maskSensitiveData(data, 4); // visible = 8 chars, 9 > 8

      expect(masked).not.toBe('***');
    });

    it('should limit asterisks to 10', () => {
      const data = 'a'.repeat(100);
      const masked = maskSensitiveData(data);

      // Count asterisks
      const asteriskCount = (masked.match(/\*/g) || []).length;
      expect(asteriskCount).toBe(10);
    });
  });
});

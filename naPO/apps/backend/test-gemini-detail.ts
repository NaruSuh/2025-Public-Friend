import 'dotenv/config';
import { GeminiClient } from './src/lib/geminiClient';

async function testGeminiDirect() {
  console.log('🧪 Testing Gemini API directly...\n');

  const apiKey = process.env.GEMINI_API_KEY;
  console.log(`API Key present: ${!!apiKey}`);
  console.log(`API Key length: ${apiKey?.length || 0}\n`);

  if (!apiKey) {
    console.error('❌ GEMINI_API_KEY not found in environment');
    process.exit(1);
  }

  const client = new GeminiClient(apiKey, {
    maxRetries: 3,
    initialDelayMs: 1000,
    maxDelayMs: 30000,
  });

  try {
    console.log('📝 Sending test message to Gemini...\n');

    const response = await client.chatCompletion({
      messages: [
        { role: 'system', content: 'You are a helpful assistant. Respond in JSON format.' },
        { role: 'user', content: 'Return a JSON object with a "test" field set to "success"' },
      ],
      temperature: 0.3,
    });

    console.log('✅ Gemini API response received:\n');
    console.log(JSON.stringify(response, null, 2));
  } catch (error: any) {
    console.error('❌ Gemini API call failed:');
    console.error('Error:', error.message);
    console.error('Stack:', error.stack);
    process.exit(1);
  }
}

testGeminiDirect();

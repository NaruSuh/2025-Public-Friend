import 'dotenv/config';
import { GoogleGenerativeAI } from '@google/generative-ai';

async function testGoogleSDK() {
  console.log('🧪 Testing Google Generative AI SDK directly...\n');

  const apiKey = process.env.GEMINI_API_KEY;
  console.log(`API Key: ${apiKey?.substring(0, 10)}...`);
  console.log(`API Key length: ${apiKey?.length}\n`);

  if (!apiKey) {
    console.error('❌ GEMINI_API_KEY not found');
    process.exit(1);
  }

  try {
    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });

    console.log('📝 Sending prompt to Gemini...\n');

    const result = await model.generateContent('안녕하세요. 간단히 인사해주세요.');
    const response = result.response;
    const text = response.text();

    console.log('✅ Success! Gemini response:\n');
    console.log(text);
  } catch (error: any) {
    console.error('❌ Failed:');
    console.error('Message:', error.message);
    console.error('Status:', error.status);
    console.error('Details:', error);
  }
}

testGoogleSDK();

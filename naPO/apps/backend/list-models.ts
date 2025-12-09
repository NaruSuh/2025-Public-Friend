import 'dotenv/config';
import { GoogleGenerativeAI } from '@google/generative-ai';

async function listAvailableModels() {
  console.log('🔍 Checking available Gemini models...\n');

  const apiKey = process.env.GEMINI_API_KEY;

  if (!apiKey) {
    console.error('❌ GEMINI_API_KEY not found');
    process.exit(1);
  }

  try {
    const genAI = new GoogleGenerativeAI(apiKey);
    const models = await genAI.listModels();

    console.log('Available models:\n');
    for (const model of models) {
      console.log(`- ${model.name}`);
      console.log(`  Display Name: ${model.displayName}`);
      console.log(`  Supported Methods: ${model.supportedGenerationMethods?.join(', ')}`);
      console.log('');
    }
  } catch (error: any) {
    console.error('❌ Failed to list models:');
    console.error('Message:', error.message);
    console.error('Status:', error.status);
  }
}

listAvailableModels();

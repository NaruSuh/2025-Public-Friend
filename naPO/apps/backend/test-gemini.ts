import 'dotenv/config';
import { NLQueryEngine } from './src/services/nlp/queryEngine';

async function testGeminiIntegration() {
  console.log('🧪 Testing Gemini Integration...\n');

  const queryEngine = new NLQueryEngine();

  // Check if Gemini is available
  const isAvailable = await queryEngine.isAvailable();
  console.log(`✓ Gemini API available: ${isAvailable}\n`);

  if (!isAvailable) {
    console.error('❌ Gemini API is not available. Check GEMINI_API_KEY in .env');
    process.exit(1);
  }

  // Test natural language query
  const testQuery = '서울의 2024년 11월 아파트 가격 데이터를 보여줘';
  console.log(`📝 Test query: "${testQuery}"\n`);

  try {
    const result = await queryEngine.parseQuery(testQuery);
    console.log('✓ Query parsing successful!\n');
    console.log('Parsed Query:', JSON.stringify(result.parsedQuery, null, 2));
    console.log('\nExplanation:', result.explanation);
    console.log('Suggested Actions:', result.suggestedActions);
  } catch (error: any) {
    console.error('❌ Query parsing failed:', error.message);
    process.exit(1);
  }

  console.log('\n✅ Gemini integration test completed successfully!');
}

testGeminiIntegration();

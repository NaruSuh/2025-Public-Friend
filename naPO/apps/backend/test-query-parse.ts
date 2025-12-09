import 'dotenv/config';
import { NLQueryEngine } from './src/services/nlp/queryEngine';

async function testQueryParsing() {
  console.log('🧪 Testing query parsing with Gemini...\n');

  const engine = new NLQueryEngine();

  const isAvailable = await engine.isAvailable();
  console.log(`Gemini available: ${isAvailable}\n`);

  const query = '지난 5년내 지방선거 주요정당 공약 요약해줘';
  console.log(`Query: "${query}"\n`);

  try {
    const result = await engine.parseQuery(query);
    console.log('✅ Parsed result:\n');
    console.log(JSON.stringify(result, null, 2));
  } catch (error: any) {
    console.error('❌ Failed to parse query:');
    console.error('Error:', error.message);
    console.error('Stack:', error.stack);
  }
}

testQueryParsing();

import { PrismaClient } from '@prisma/client';
import { RoneService } from './src/services/api/roneService';
import dotenv from 'dotenv';

dotenv.config();

const prisma = new PrismaClient();

async function testRone() {
  console.log('\n=== Testing R-ONE API ===\n');
  console.log('Note: Sample API key is limited to 5 results and page 1 only\n');

  try {
    // Get API key from environment
    const apiKey = process.env.RONE_API_KEY;
    if (!apiKey) {
      throw new Error('RONE_API_KEY not found in .env');
    }

    console.log('API Key loaded:', apiKey.substring(0, 10) + '...');

    // ============================================
    // Test 1: Get table list
    // ============================================
    console.log('\n[Test 1] Fetching table list (limited to 5 results)...');
    const tableList = await RoneService.getTableList(apiKey, { pSize: 5 });

    if (tableList.success) {
      console.log(' Table list retrieved successfully');
      console.log(`  - Total tables found: ${tableList.totalCount}`);
      console.log(`  - Results shown: ${tableList.data.length}`);
      if (tableList.data.length > 0) {
        console.log('\n  First 3 tables:');
        tableList.data.slice(0, 3).forEach((table: any, i: number) => {
          console.log(`    ${i + 1}. [${table.TBL_ID}] ${table.TBL_NM}`);
          console.log(`       Organization: ${table.ORG_NM}`);
          console.log(`       Cycle: ${table.CYCLE_NM} (${table.CYCLE})`);
          console.log(`       Key Statistics: ${table.KEY_YN}`);
        });
      }
    } else {
      console.error(' Failed to fetch table list:', tableList.error);
      return;
    }

    // ============================================
    // Test 2: Get key statistics only
    // ============================================
    console.log('\n[Test 2] Fetching key statistics only...');
    const keyStats = await RoneService.getKeyStatistics(apiKey);

    if (keyStats.success) {
      console.log(' Key statistics retrieved successfully');
      console.log(`  - Total key statistics: ${keyStats.totalCount}`);
      if (keyStats.data.length > 0) {
        console.log('\n  Key statistics:');
        keyStats.data.slice(0, 3).forEach((table: any, i: number) => {
          console.log(`    ${i + 1}. [${table.TBL_ID}] ${table.TBL_NM}`);
        });
      }
    } else {
      console.error(' Failed to fetch key statistics:', keyStats.error);
    }

    // ============================================
    // Test 3: Search statistics by keyword
    // ============================================
    console.log('\n[Test 3] Searching for "הה" in table names...');
    const searchResult = await RoneService.searchStatistics(apiKey, 'הה');

    if (searchResult.success) {
      console.log(' Search completed successfully');
      console.log(`  - Total matches: ${searchResult.totalCount}`);
      console.log(`  - Search keyword: "${searchResult.searchKeyword}"`);
      if (searchResult.data.length > 0) {
        console.log('\n  Matched tables:');
        searchResult.data.slice(0, 3).forEach((table: any, i: number) => {
          console.log(`    ${i + 1}. [${table.TBL_ID}] ${table.TBL_NM}`);
        });
      }
    } else {
      console.error(' Search failed:', searchResult.error);
    }

    // ============================================
    // Test 4: Get statistics by cycle (װ)
    // ============================================
    console.log('\n[Test 4] Fetching monthly (MM) statistics...');
    const monthlyStats = await RoneService.getStatisticsByCycle(apiKey, 'MM');

    if (monthlyStats.success) {
      console.log(' Monthly statistics retrieved successfully');
      console.log(`  - Total monthly statistics: ${monthlyStats.totalCount}`);
      if (monthlyStats.data.length > 0) {
        console.log('\n  Monthly statistics:');
        monthlyStats.data.slice(0, 3).forEach((table: any, i: number) => {
          console.log(`    ${i + 1}. [${table.TBL_ID}] ${table.TBL_NM}`);
        });
      }
    } else {
      console.error(' Failed to fetch monthly statistics:', monthlyStats.error);
    }

    // ============================================
    // Test 5: Get statistics summary
    // ============================================
    console.log('\n[Test 5] Generating statistics summary...');
    const summary = await RoneService.getStatisticsSummary(apiKey);

    if (summary.success) {
      console.log(' Statistics summary generated successfully');
      console.log(`  - Total statistics: ${summary.summary.totalCount}`);
      console.log(`  - Key statistics: ${summary.summary.keyStatisticsCount}`);
      console.log(`  - Area statistics: ${summary.summary.areaStatisticsCount}`);

      console.log('\n  Statistics by cycle:');
      Object.entries(summary.summary.byCycle).forEach(([cycle, count]: [string, any]) => {
        console.log(`    - ${cycle}: ${count}`);
      });

      console.log('\n  Statistics by organization:');
      Object.entries(summary.summary.byOrganization).slice(0, 3).forEach(([org, count]: [string, any]) => {
        console.log(`    - ${org}: ${count}`);
      });
    } else {
      console.error(' Failed to generate summary:', summary.error);
    }

    // ============================================
    // Test 6: Get table items (if table ID available)
    // ============================================
    if (tableList.success && tableList.data.length > 0) {
      const testTableId = tableList.data[0].TBL_ID;
      console.log(`\n[Test 6] Fetching items for table ${testTableId}...`);

      const tableItems = await RoneService.getTableItems(apiKey, testTableId, { pSize: 5 });

      if (tableItems.success) {
        console.log(' Table items retrieved successfully');
        console.log(`  - Total items: ${tableItems.totalCount}`);
        if (tableItems.data.length > 0) {
          console.log('\n  First 3 items:');
          tableItems.data.slice(0, 3).forEach((item: any, i: number) => {
            console.log(`    ${i + 1}. [${item.ITM_ID}] ${item.ITM_NM}`);
            if (item.C1_NM) console.log(`       Category 1: ${item.C1_NM}`);
            if (item.UNIT) console.log(`       Unit: ${item.UNIT}`);
          });

          // ============================================
          // Test 7: Get table data (if item ID available)
          // ============================================
          if (tableItems.data.length > 0) {
            const testItemId = tableItems.data[0].ITM_ID;
            console.log(`\n[Test 7] Fetching data for table ${testTableId}, item ${testItemId}...`);

            const tableData = await RoneService.getTableData(
              apiKey,
              testTableId,
              testItemId,
              { pSize: 5 }
            );

            if (tableData.success) {
              console.log(' Table data retrieved successfully');
              console.log(`  - Total data records: ${tableData.totalCount}`);
              if (tableData.data.length > 0) {
                console.log('\n  First 3 data records:');
                tableData.data.slice(0, 3).forEach((data: any, i: number) => {
                  console.log(`    ${i + 1}. ${data.DT_NM} (${data.DT})`);
                  if (data.DTA) console.log(`       Value: ${data.DTA} ${data.UNIT || ''}`);
                  if (data.C1_NM) console.log(`       Category: ${data.C1_NM}`);
                });
              }
            } else {
              console.error(' Failed to fetch table data:', tableData.error);
            }
          }
        }
      } else {
        console.error(' Failed to fetch table items:', tableItems.error);
      }
    }

    console.log('\n=== All Tests Complete ===\n');
  } catch (error: any) {
    console.error('Test failed:', error);
    throw error;
  } finally {
    await prisma.$disconnect();
  }
}

testRone().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});

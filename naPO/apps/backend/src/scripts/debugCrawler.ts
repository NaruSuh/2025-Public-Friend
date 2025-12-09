/**
 * 디버그용 크롤러 - HTML 구조 분석
 */

import puppeteer from 'puppeteer';

async function debugNEC() {
  console.log('=== NEC Policy 사이트 분석 ===\n');

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  try {
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');

    const url = 'https://policy.nec.go.kr/plc/policy/initUPAPolicy.do?menuId=PARTY5';
    console.log(`URL: ${url}\n`);

    await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

    // 추가 대기
    await new Promise(r => setTimeout(r, 3000));

    // HTML 가져오기
    const html = await page.content();

    // 정당명 관련 요소 찾기
    const partyElements = await page.evaluate(() => {
      const results: string[] = [];

      // 모든 텍스트에서 정당명 찾기
      const allText = document.body.innerText;
      const parties = ['더불어민주당', '국민의힘', '조국혁신당', '개혁신당', '진보당'];
      for (const party of parties) {
        if (allText.includes(party)) {
          results.push(`정당 발견: ${party}`);
        }
      }

      // 링크 분석
      const links = document.querySelectorAll('a');
      links.forEach((link, i) => {
        const href = link.getAttribute('href') || '';
        const text = link.textContent?.trim() || '';
        if (href.includes('download') || href.includes('pdf') || text.includes('공약') || text.includes('정책')) {
          results.push(`링크 ${i}: href="${href}", text="${text}"`);
        }
      });

      // 버튼 분석
      const buttons = document.querySelectorAll('button, [onclick]');
      buttons.forEach((btn, i) => {
        const onclick = btn.getAttribute('onclick') || '';
        const text = btn.textContent?.trim() || '';
        if (onclick.includes('download') || onclick.includes('pdf') || text.includes('다운') || text.includes('PDF')) {
          results.push(`버튼 ${i}: onclick="${onclick.substring(0, 100)}", text="${text}"`);
        }
      });

      // 이미지 분석 (정당 로고 등)
      const images = document.querySelectorAll('img');
      images.forEach((img, i) => {
        const src = img.getAttribute('src') || '';
        const alt = img.getAttribute('alt') || '';
        if (alt.includes('정당') || alt.includes('당') || src.includes('party') || src.includes('logo')) {
          results.push(`이미지 ${i}: src="${src}", alt="${alt}"`);
        }
      });

      return results;
    });

    console.log('발견된 요소들:');
    partyElements.forEach(e => console.log(`  - ${e}`));

    // 콘텐츠 영역 찾기
    const contentArea = await page.evaluate(() => {
      const content = document.querySelector('#content, .content, main, [role="main"]');
      if (content) {
        return content.innerHTML.substring(0, 2000);
      }
      return '콘텐츠 영역 못찾음';
    });

    console.log('\n--- 콘텐츠 영역 (처음 2000자) ---');
    console.log(contentArea);

  } finally {
    await browser.close();
  }
}

async function debugPPP() {
  console.log('\n\n=== 국민의힘 사이트 분석 ===\n');

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });

  try {
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');

    // 여러 URL 시도
    const urls = [
      'https://www.peoplepowerparty.kr/renewal/about/policyPledge.do',
      'https://www.peoplepowerparty.kr/web/policy/policy/mainPolicyView.do',
      'https://www.peoplepowerparty.kr/renewal/policy/basicPolicy.do',
    ];

    for (const url of urls) {
      console.log(`\nURL: ${url}`);

      try {
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
        await new Promise(r => setTimeout(r, 2000));

        const pageInfo = await page.evaluate(() => {
          const title = document.title;
          const h1 = document.querySelector('h1, h2')?.textContent?.trim() || 'no h1';
          const links = document.querySelectorAll('a');
          const pdfLinks: string[] = [];

          links.forEach(link => {
            const href = link.getAttribute('href') || '';
            const text = link.textContent?.trim() || '';
            if (href.includes('pdf') || href.includes('download') || text.includes('공약') || text.includes('정책')) {
              pdfLinks.push(`"${text}": ${href}`);
            }
          });

          return { title, h1, pdfLinks: pdfLinks.slice(0, 10) };
        });

        console.log(`  Title: ${pageInfo.title}`);
        console.log(`  H1: ${pageInfo.h1}`);
        console.log(`  PDF 링크들: ${JSON.stringify(pageInfo.pdfLinks, null, 2)}`);

      } catch (err: any) {
        console.log(`  ERROR: ${err.message}`);
      }
    }

  } finally {
    await browser.close();
  }
}

async function main() {
  await debugNEC();
  await debugPPP();
}

main().catch(console.error);

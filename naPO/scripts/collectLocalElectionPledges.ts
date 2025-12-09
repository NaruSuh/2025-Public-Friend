/**
 * 2018년/2022년 지방선거 광역단체장 공약 수집 스크립트
 *
 * 공공데이터포털 API 사용:
 * - PofelcddInfoInqireService: 후보자 정보 조회
 * - ElecPrmsInfoInqireService: 후보자 공약 조회
 */

import * as fs from 'fs';
import * as path from 'path';

// API 키는 환경변수에서 로드 (https://data.go.kr 에서 발급)
const API_KEY = process.env.DATA_GO_KR_API_KEY || '';

// 선거 정보
const ELECTIONS = [
  { sgId: '20180613', name: '제7회 전국동시지방선거 (2018)', year: 2018 },
  { sgId: '20220601', name: '제8회 전국동시지방선거 (2022)', year: 2022 },
];

// 선거 종류 코드
const SG_TYPECODES = {
  시도지사: '3',
  구시군의장: '4',
  교육감: '11',
};

interface Candidate {
  huboid: string;
  name: string;
  hanjaName: string;
  party: string;
  region: string;
  giho: string;
  gender: string;
  birthday: string;
  job: string;
  edu: string;
  career1: string;
  career2: string;
}

interface Pledge {
  order: number;
  realmName: string;
  title: string;
  content: string;
}

interface CandidateWithPledges extends Candidate {
  pledgeCount: number;
  pledges: Pledge[];
}

interface ElectionData {
  sgId: string;
  sgName: string;
  year: number;
  sgTypecode: string;
  sgTypeName: string;
  collectedAt: string;
  candidates: CandidateWithPledges[];
}

async function fetchXML(url: string): Promise<string> {
  const response = await fetch(url);
  return await response.text();
}

function parseXMLValue(xml: string, tag: string): string {
  const regex = new RegExp(`<${tag}>([\\s\\S]*?)</${tag}>`);
  const match = xml.match(regex);
  return match ? match[1].trim() : '';
}

function parseXMLItems(xml: string): string[] {
  const items: string[] = [];
  const regex = /<item>([\s\S]*?)<\/item>/g;
  let match;
  while ((match = regex.exec(xml)) !== null) {
    items.push(match[1]);
  }
  return items;
}

async function fetchCandidates(sgId: string, sgTypecode: string): Promise<Candidate[]> {
  const url = `http://apis.data.go.kr/9760000/PofelcddInfoInqireService/getPofelcddRegistSttusInfoInqire?ServiceKey=${API_KEY}&sgId=${sgId}&sgTypecode=${sgTypecode}&numOfRows=500`;

  console.log(`  후보자 목록 조회: ${sgId}, 선거종류: ${sgTypecode}`);

  const xml = await fetchXML(url);
  const resultCode = parseXMLValue(xml, 'resultCode');

  if (resultCode !== 'INFO-00') {
    console.error(`  API 오류: ${parseXMLValue(xml, 'resultMsg')}`);
    return [];
  }

  const items = parseXMLItems(xml);
  console.log(`  총 ${items.length}명의 후보자 발견`);

  return items.map(item => ({
    huboid: parseXMLValue(item, 'huboid'),
    name: parseXMLValue(item, 'name'),
    hanjaName: parseXMLValue(item, 'hanjaName'),
    party: parseXMLValue(item, 'jdName'),
    region: parseXMLValue(item, 'sggName'),
    giho: parseXMLValue(item, 'giho'),
    gender: parseXMLValue(item, 'gender'),
    birthday: parseXMLValue(item, 'birthday'),
    job: parseXMLValue(item, 'job'),
    edu: parseXMLValue(item, 'edu'),
    career1: parseXMLValue(item, 'career1'),
    career2: parseXMLValue(item, 'career2'),
  }));
}

async function fetchPledges(sgId: string, sgTypecode: string, cnddtId: string): Promise<{ pledgeCount: number; pledges: Pledge[] }> {
  const url = `http://apis.data.go.kr/9760000/ElecPrmsInfoInqireService/getCnddtElecPrmsInfoInqire?ServiceKey=${API_KEY}&sgId=${sgId}&sgTypecode=${sgTypecode}&cnddtId=${cnddtId}&numOfRows=10`;

  const xml = await fetchXML(url);
  const resultCode = parseXMLValue(xml, 'resultCode');

  if (resultCode !== 'INFO-00') {
    return { pledgeCount: 0, pledges: [] };
  }

  const items = parseXMLItems(xml);
  if (items.length === 0) {
    return { pledgeCount: 0, pledges: [] };
  }

  const item = items[0];
  const pledgeCount = parseInt(parseXMLValue(item, 'prmsCnt')) || 0;
  const pledges: Pledge[] = [];

  for (let i = 1; i <= 10; i++) {
    const order = parseXMLValue(item, `prmsOrd${i}`);
    const title = parseXMLValue(item, `prmsTitle${i}`);
    const content = parseXMLValue(item, `prmmCont${i}`);
    const realmName = parseXMLValue(item, `prmsRealmName${i}`);

    if (order && title) {
      pledges.push({
        order: parseInt(order),
        realmName,
        title,
        content,
      });
    }
  }

  return { pledgeCount, pledges };
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function collectElectionData(sgId: string, sgName: string, year: number, sgTypecode: string, sgTypeName: string): Promise<ElectionData> {
  console.log(`\n========================================`);
  console.log(`${sgName} - ${sgTypeName} 공약 수집 시작`);
  console.log(`========================================`);

  // 후보자 목록 가져오기
  const candidates = await fetchCandidates(sgId, sgTypecode);

  const candidatesWithPledges: CandidateWithPledges[] = [];

  // 각 후보자의 공약 가져오기
  for (let i = 0; i < candidates.length; i++) {
    const candidate = candidates[i];
    console.log(`  [${i + 1}/${candidates.length}] ${candidate.region} - ${candidate.name} (${candidate.party}) 공약 조회 중...`);

    const { pledgeCount, pledges } = await fetchPledges(sgId, sgTypecode, candidate.huboid);

    candidatesWithPledges.push({
      ...candidate,
      pledgeCount,
      pledges,
    });

    if (pledgeCount > 0) {
      console.log(`    -> ${pledgeCount}개 공약 수집 완료`);
    }

    // API 호출 간격 (rate limit 방지)
    await delay(100);
  }

  const totalPledges = candidatesWithPledges.reduce((sum, c) => sum + c.pledgeCount, 0);
  console.log(`\n${sgTypeName} 수집 완료: ${candidatesWithPledges.length}명 후보자, 총 ${totalPledges}개 공약`);

  return {
    sgId,
    sgName,
    year,
    sgTypecode,
    sgTypeName,
    collectedAt: new Date().toISOString(),
    candidates: candidatesWithPledges,
  };
}

async function main() {
  console.log('==========================================');
  console.log('  지방선거 공약 데이터 수집 시작');
  console.log('==========================================');
  console.log(`API Key: ${API_KEY.substring(0, 20)}...`);
  console.log(`수집 대상: 2018년, 2022년 지방선거`);
  console.log(`수집 선거종류: 시·도지사`);

  const outputDir = path.join(__dirname, '..', 'data', 'pledges');

  // 출력 디렉토리 생성
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const allData: ElectionData[] = [];

  // 2018년, 2022년 시·도지사 선거 공약 수집
  for (const election of ELECTIONS) {
    const data = await collectElectionData(
      election.sgId,
      election.name,
      election.year,
      SG_TYPECODES.시도지사,
      '시·도지사선거'
    );
    allData.push(data);

    // 개별 파일 저장
    const filename = `local_election_${election.year}_governor_pledges.json`;
    const filepath = path.join(outputDir, filename);
    fs.writeFileSync(filepath, JSON.stringify(data, null, 2), 'utf-8');
    console.log(`\n저장됨: ${filepath}`);
  }

  // 전체 데이터 통합 저장
  const combinedFilepath = path.join(outputDir, 'local_elections_2018_2022_all_pledges.json');
  fs.writeFileSync(combinedFilepath, JSON.stringify(allData, null, 2), 'utf-8');
  console.log(`\n통합 파일 저장됨: ${combinedFilepath}`);

  // 통계 출력
  console.log('\n==========================================');
  console.log('  수집 완료 통계');
  console.log('==========================================');

  for (const data of allData) {
    const totalPledges = data.candidates.reduce((sum, c) => sum + c.pledgeCount, 0);
    const withPledges = data.candidates.filter(c => c.pledgeCount > 0).length;

    console.log(`\n${data.sgName} (${data.sgTypeName}):`);
    console.log(`  - 총 후보자: ${data.candidates.length}명`);
    console.log(`  - 공약 등록 후보자: ${withPledges}명`);
    console.log(`  - 총 공약 수: ${totalPledges}개`);

    // 정당별 후보자 수
    const partyCount: Record<string, number> = {};
    data.candidates.forEach(c => {
      partyCount[c.party] = (partyCount[c.party] || 0) + 1;
    });

    console.log(`  - 정당별 후보자:`);
    Object.entries(partyCount)
      .sort((a, b) => b[1] - a[1])
      .forEach(([party, count]) => {
        console.log(`      ${party}: ${count}명`);
      });
  }
}

main().catch(console.error);

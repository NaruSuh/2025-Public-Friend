/**
 * 주요 정보 데이터
 * 선거 관련 핵심 정보 카드용
 * 생성일: 2026-01-27
 */

export interface KeyInfo {
  id: string;
  title: string;
  icon: string;
  items: string[];
  lawRef?: string;
}

export const keyInfo: KeyInfo[] = [
  {
    "id": "voting-rights",
    "title": "투표권 행사",
    "icon": "vote",
    "items": [
      "만 18세 이상 대한민국 국민",
      "선거일 현재 해당 지역 주민등록",
      "사전투표: 선거일 5일 전부터 2일간",
      "신분증 지참 필수"
    ],
    "lawRef": "공직선거법 제15조"
  },
  {
    "id": "campaign-period",
    "title": "선거운동 기간",
    "icon": "calendar",
    "items": [
      "대통령선거: 후보자등록마감 다음날부터 22일간",
      "국회의원선거: 후보자등록마감 다음날부터 13일간",
      "지방선거: 후보자등록마감 다음날부터 13일간",
      "선거일 당일 선거운동 금지"
    ],
    "lawRef": "공직선거법 제59조"
  },
  {
    "id": "prohibited-acts",
    "title": "금지되는 행위",
    "icon": "warning",
    "items": [
      "금품, 음식물 등 기부행위",
      "허위사실 공표, 비방",
      "선거일 선거운동",
      "호별방문, 서명날인 요구"
    ],
    "lawRef": "공직선거법 제112조, 제250조, 제251조"
  },
  {
    "id": "online-campaign",
    "title": "SNS/온라인 선거운동",
    "icon": "phone",
    "items": [
      "선거운동기간 중 SNS 지지 게시 가능",
      "선거일 당일 게시 금지",
      "허위사실, 비방 금지",
      "실명 표기 권장"
    ],
    "lawRef": "공직선거법 제82조의6"
  },
  {
    "id": "reporting",
    "title": "위반행위 신고",
    "icon": "report",
    "items": [
      "선관위 전화: 1390",
      "인터넷 신고: www.nec.go.kr",
      "신고 포상금 지급",
      "익명 신고 가능"
    ]
  }
];

/**
 * ID로 키 정보 조회
 */
export function getKeyInfoById(id: string): KeyInfo | undefined {
  return keyInfo.find((item) => item.id === id);
}

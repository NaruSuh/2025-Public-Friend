#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
산림청 입찰정보 크롤러
Target: https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardList.do?mn=NKFS_04_01_04&bbsId=BBSMSTR_1033
"""

import logging
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import sys
from urllib.parse import urljoin
from dateutil import parser as date_parser


class ForestBidCrawler:
    """산림청 입찰정보 크롤러"""

    BASE_URL = "https://www.forest.go.kr"
    LIST_URL = "https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardList.do"
    DETAIL_URL = "https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardArticle.do"

    def __init__(self, days=365, delay=1.0, page_delay=2.0):
        """
        초기화

        Args:
            days (int): 수집할 기간 (일 단위)
            delay (float): 요청 간 딜레이 (초)
            page_delay (float): 페이지 간 딜레이 (초)
        """
        self.days = days
        self.delay = delay
        self.page_delay = page_delay
        self.cutoff_date = datetime.now() - timedelta(days=days)

        # 세션 설정
        # 로깅 설정
        self.logger = logging.getLogger(self.__class__.__name__)

        self.session = requests.Session()
        # Note: avoid 'br' in Accept-Encoding unless brotli is ensured available in environment
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        self.data = []
        self.total_items = 0

    def fetch_page(self, url, params=None, max_retries=3):
        """
        페이지 가져오기 (재시도 로직 포함)

        Args:
            url (str): 요청 URL
            params (dict): 쿼리 파라미터
            max_retries (int): 최대 재시도 횟수

        Returns:
            BeautifulSoup: 파싱된 HTML
        """
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                # 응답 텍스트는 requests가 디코딩하므로 기본값 사용
                return BeautifulSoup(response.text, 'html.parser')
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"요청 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
                else:
                    self.logger.error(f"페이지 가져오기 실패: {url}")
                    return None

    def parse_list_page(self, soup):
        """
        리스트 페이지에서 게시글 정보 추출

        Args:
            soup (BeautifulSoup): 파싱된 HTML

        Returns:
            list: 게시글 정보 리스트 (번호, 링크, 날짜 등)
        """
        items = []

        try:
            # 테이블 행 찾기
            rows = soup.select('table tbody tr')

            for row in rows:
                try:
                    # 보다 견고하게 td 셀을 직접 가져와 인덱스 접근에 대비
                    cells = row.find_all('td')

                    # 기본값
                    number = 'N/A'
                    title = 'N/A'
                    link = None
                    department = 'N/A'
                    date_str = ''
                    post_date = None
                    views = 0
                    has_attachment = ''

                    # 번호 후보
                    if len(cells) >= 1:
                        try:
                            number = cells[0].get_text(strip=True)
                        except Exception:
                            number = 'N/A'

                    # 제목 및 링크: 테이블 안의 <a> 태그 우선 검색
                    title_a = row.select_one('a')
                    if title_a:
                        title = title_a.get_text(strip=True)
                        link = title_a.get('href')
                    else:
                        # 대체: 두 번째 셀 등에서 제목 추출 시도
                        if len(cells) >= 2:
                            title = cells[1].get_text(strip=True)

                    # 부서: 존재하면 3번째 셀 시도
                    if len(cells) >= 3:
                        department = cells[2].get_text(strip=True)

                    # 날짜: 4번째 셀 시도
                    if len(cells) >= 4:
                        date_str = cells[3].get_text(strip=True)
                        if date_str:
                            try:
                                post_date = date_parser.parse(date_str)
                            except Exception:
                                post_date = None

                    # 조회수: 마지막쪽 셀 또는 6번째 셀
                    try:
                        views_text = ''
                        if len(cells) >= 6:
                            views_text = cells[5].get_text(strip=True)
                        else:
                            # fallback: 검색으로 숫자 포함 텍스트 찾기
                            views_text = row.get_text(' ', strip=True)

                        views_numbers = re.findall(r"\d+", views_text.replace(',', ''))
                        views = int(views_numbers[0]) if views_numbers else 0
                    except Exception:
                        views = 0

                    # 첨부파일 유무: 5번째 셀의 <img> 또는 파일 아이콘 존재 검사
                    if len(cells) >= 5:
                        try:
                            attach_cell = cells[4]
                            if attach_cell.find('img') or attach_cell.find('a'):
                                has_attachment = 'O'
                        except Exception:
                            has_attachment = ''

                    # 상세 페이지 URL 구성
                    detail_url = None
                    if link:
                        if link.startswith('http'):
                            detail_url = link
                        else:
                            detail_url = urljoin(self.BASE_URL, link)

                    items.append({
                        'number': number,
                        'title': title,
                        'department': department,
                        'post_date': post_date,
                        'post_date_str': date_str,
                        'views': views,
                        'has_attachment': has_attachment,
                        'detail_url': detail_url
                    })

                except Exception as e:
                    self.logger.exception(f"행 파싱 오류: {e}")
                    continue

        except Exception as e:
            self.logger.exception(f"리스트 파싱 오류: {e}")

        return items

    def parse_detail_page(self, soup, basic_info):
        """
        상세 페이지에서 추가 정보 추출

        Args:
            soup (BeautifulSoup): 파싱된 HTML
            basic_info (dict): 리스트에서 가져온 기본 정보

        Returns:
            dict: 전체 정보
        """
        data = basic_info.copy()

        try:
            # 제목에서 담당산림청 추출
            title_elem = soup.select_one('.b_info strong')
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                # [동부지방산림청] 형태 추출
                office_match = re.search(r'\[([^\]]+)\]', title_text)
                if office_match:
                    data['forest_office'] = office_match.group(1)

            # 게시글 정보 리스트 (.bd_view_ul_info)에서 추출
            info_list = soup.select('.bd_view_ul_info li')

            for li in info_list:
                label_elem = li.select_one('.info_tit')
                if not label_elem:
                    continue

                label = label_elem.get_text(strip=True)

                # 전체 텍스트에서 레이블 제거
                full_text = li.get_text(strip=True)
                value = full_text.replace(label, '', 1).strip()

                # 작성자 (부서 / 담당자 / 연락처)
                if '작성자' in label:
                    # "영월국유림관리소 / 김가희 / 033-371-8112" 형태 파싱
                    parts = [p.strip() for p in value.split('/')]

                    if len(parts) >= 1:
                        data['department'] = parts[0]
                    if len(parts) >= 2:
                        data['manager'] = parts[1]
                    if len(parts) >= 3:
                        data['contact'] = parts[2]

                # 조회수
                elif '조회' in label:
                    # 숫자만 추출
                    numbers = re.findall(r'\d+', value.replace(',', ''))
                    data['views'] = int(numbers[0]) if numbers else 0

            # 본문 내용
            content_elem = soup.select_one('.b_content')
            if content_elem:
                data['content'] = content_elem.get_text(' ', strip=True)[:500]  # 500자까지만

            # 첨부파일 링크 추출
            attachments = []
            attach_section = soup.select_one('.file_list, .attach_file')
            if attach_section:
                attach_links = attach_section.select('a')
                for a in attach_links:
                    href = a.get('href')
                    if href:
                        attach_url = urljoin(self.BASE_URL, href)
                        attachments.append(attach_url)

            data['attachments'] = ', '.join(attachments) if attachments else ''

        except Exception as e:
            self.logger.exception(f"상세 페이지 파싱 오류: {e}")

        # 기본값 설정
        data.setdefault('forest_office', 'N/A')
        data.setdefault('manager', 'N/A')
        data.setdefault('contact', 'N/A')
        data.setdefault('attachments', '')

        return data

    def crawl(self):
        """메인 크롤링 로직"""
        print(f"[*] 산림청 입찰정보 크롤링 시작...")
        print(f"[*] 수집 기간: 최근 {self.days}일 (기준일: {self.cutoff_date.strftime('%Y-%m-%d')})")

        page_index = 1
        should_continue = True

        while should_continue:
            print(f"\n[*] 페이지 {page_index} 처리 중...")

            # 리스트 페이지 가져오기
            params = {
                'mn': 'NKFS_04_01_04',
                'bbsId': 'BBSMSTR_1033',
                'pageIndex': page_index,
                'pageUnit': 10
            }

            soup = self.fetch_page(self.LIST_URL, params)

            if not soup:
                print(f"[!] 페이지 {page_index} 가져오기 실패, 중단")
                break

            # 리스트 파싱
            items = self.parse_list_page(soup)

            if not items:
                print(f"[!] 페이지 {page_index}에 항목 없음, 크롤링 종료")
                break

            # 각 항목 처리
            for idx, item in enumerate(items, 1):
                # 상단 고정 공지는 번호가 비거나 '공지' 표기로 나타나므로 건너뛴다.
                number_text = str(item.get('number', '')).strip()
                is_notice = not number_text or '공지' in number_text

                # 날짜 체크 (공지 제외)
                if item['post_date'] and item['post_date'] < self.cutoff_date and not is_notice:
                    print(f"[*] 기준일 이전 게시글 도달 ({item['post_date_str']}), 크롤링 종료")
                    should_continue = False
                    break

                print(f"  [{idx}/10] {item['title'][:50]}...")

                # 상세 페이지 가져오기
                if item['detail_url']:
                    time.sleep(self.delay)
                    detail_soup = self.fetch_page(item['detail_url'])

                    if detail_soup:
                        detail_data = self.parse_detail_page(detail_soup, item)
                        self.data.append(detail_data)
                        self.total_items += 1
                    else:
                        print(f"    [!] 상세 페이지 가져오기 실패")
                        self.data.append(item)
                        self.total_items += 1
                else:
                    self.data.append(item)
                    self.total_items += 1

            # 다음 페이지로
            if should_continue:
                page_index += 1
                time.sleep(self.page_delay)

            # 중간 저장 (10페이지마다)
            if page_index % 10 == 0:
                self.save_to_excel(f'산림청_입찰정보_중간저장_{page_index}.xlsx')

        print(f"\n[✓] 크롤링 완료: 총 {self.total_items}개 항목 수집")

    def save_to_excel(self, filename=None):
        """
        수집한 데이터를 엑셀로 저장

        Args:
            filename (str): 출력 파일명
        """
        if not self.data:
            print("[!] 저장할 데이터가 없습니다.")
            return

        if not filename:
            filename = f"산림청_입찰정보_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # DataFrame 변환
        df = pd.DataFrame(self.data)

        # 컬럼 순서 및 출력 라벨 정의
        column_labels = [
            ('number', '번호'),
            ('title', '제목'),
            ('forest_office', '담당산림청'),
            ('department', '담당부서'),
            ('manager', '담당자'),
            ('contact', '연락처'),
            ('post_date_str', '공고일자'),
            ('views', '조회수'),
            ('has_attachment', '첨부파일'),
            ('attachments', '첨부파일링크'),
            ('detail_url', 'URL'),
        ]

        # 존재하는 컬럼만 사용하여 순서 보존
        available_columns = [(col, label) for col, label in column_labels if col in df.columns]

        if not available_columns:
            print("[!] 출력 가능한 컬럼이 없습니다.")
            return

        ordered_cols = [col for col, _ in available_columns]
        df = df[ordered_cols]

        # 가독성을 위해 라벨링 적용
        rename_map = {col: label for col, label in available_columns}
        df = df.rename(columns=rename_map)

        # 엑셀 저장
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"[✓] 엑셀 파일 저장: {filename}")


def main():
    """실행 진입점"""
    print("="*60)
    print("  산림청 입찰정보 크롤러")
    print("="*60)

    # 크롤러 실행
    crawler = ForestBidCrawler(
        days=365,      # 최근 1년
        delay=1.0,     # 요청 간 1초 대기
        page_delay=2.0 # 페이지 간 2초 대기
    )

    try:
        crawler.crawl()
        crawler.save_to_excel()
    except KeyboardInterrupt:
        print("\n\n[!] 사용자에 의해 중단됨")
        if crawler.data:
            print("[*] 수집한 데이터 저장 중...")
            crawler.save_to_excel(f'산림청_입찰정보_중단_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
    except Exception as e:
        print(f"\n[X] 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    print("\n[*] 프로그램 종료")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
산림청 입찰정보 크롤러
Target: https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardList.do?mn=NKFS_04_01_04&bbsId=BBSMSTR_1033
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import sys
from urllib.parse import urljoin
import re


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
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
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
                response.encoding = 'utf-8'
                return BeautifulSoup(response.text, 'html.parser')
            except requests.exceptions.RequestException as e:
                print(f"[!] 요청 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
                else:
                    print(f"[X] 페이지 가져오기 실패: {url}")
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
                    # 번호
                    num_cell = row.select_one('td:nth-of-type(1)')
                    number = num_cell.text.strip() if num_cell else 'N/A'

                    # 제목 및 링크
                    title_cell = row.select_one('td.left a')
                    title = title_cell.text.strip() if title_cell else 'N/A'
                    link = title_cell.get('href') if title_cell else None

                    # 부서
                    dept_cell = row.select_one('td:nth-of-type(3)')
                    department = dept_cell.text.strip() if dept_cell else 'N/A'

                    # 날짜
                    date_cell = row.select_one('td:nth-of-type(4)')
                    date_str = date_cell.text.strip() if date_cell else ''

                    # 조회수
                    view_cell = row.select_one('td:nth-of-type(6)')
                    views_text = view_cell.text.strip() if view_cell else '0'
                    # 숫자만 추출
                    views_numbers = re.findall(r'\d+', views_text)
                    views = views_numbers[0] if views_numbers else '0'

                    # 첨부파일 유무
                    attach_cell = row.select_one('td:nth-of-type(5)')
                    has_attachment = 'O' if attach_cell and attach_cell.select_one('img') else ''

                    # 날짜 파싱
                    post_date = None
                    if date_str:
                        try:
                            post_date = datetime.strptime(date_str, '%Y-%m-%d')
                        except ValueError:
                            pass

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
                    print(f"[!] 행 파싱 오류: {e}")
                    continue

        except Exception as e:
            print(f"[!] 리스트 파싱 오류: {e}")

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
                import re
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
                    import re
                    numbers = re.findall(r'\d+', value)
                    data['views'] = numbers[0] if numbers else value

            # 본문 내용
            content_elem = soup.select_one('.b_content')
            if content_elem:
                data['content'] = content_elem.get_text(strip=True)[:500]  # 500자까지만

            # 첨부파일 링크 추출
            attachments = []
            attach_section = soup.select_one('.file_list, .attach_file')
            if attach_section:
                attach_links = attach_section.select('a')
                for link in attach_links:
                    href = link.get('href')
                    if href:
                        attach_url = urljoin(self.BASE_URL, href)
                        attachments.append(attach_url)

            data['attachments'] = ', '.join(attachments) if attachments else ''

        except Exception as e:
            print(f"[!] 상세 페이지 파싱 오류: {e}")
            import traceback
            traceback.print_exc()

        # 기본값 설정
        data.setdefault('forest_office', 'N/A')
        data.setdefault('manager', 'N/A')
        data.setdefault('contact', 'N/A')
        data.setdefault('category', 'N/A')
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
                # 날짜 체크
                if item['post_date'] and item['post_date'] < self.cutoff_date:
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

        # 컬럼 순서 정리
        columns = [
            'number', 'title', 'category', 'forest_office', 'department',
            'manager', 'contact', 'post_date_str', 'views', 'has_attachment',
            'attachments', 'detail_url'
        ]

        # 존재하는 컬럼만 선택
        columns = [col for col in columns if col in df.columns]
        df = df[columns]

        # 컬럼명 한글화
        df.columns = [
            '번호', '제목', '분류', '담당산림청', '담당부서',
            '담당자', '연락처', '공고일자', '조회수', '첨부파일',
            '첨부파일링크', 'URL'
        ][:len(columns)]

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

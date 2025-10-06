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
from datetime import datetime, timedelta, timezone
import time
import sys
from urllib.parse import urljoin
from dateutil import parser as date_parser
from typing import Optional, Dict, List, Any
import json
from pathlib import Path
from email.utils import parsedate_to_datetime


class CrawlCheckpoint:
    """크롤링 체크포인트 관리"""

    def __init__(self, checkpoint_file='crawl_checkpoint.json'):
        self.file = Path(checkpoint_file)
        self.state = self._load()

    def _load(self) -> Dict[str, Any]:
        """저장된 체크포인트 로드"""
        if self.file.exists():
            try:
                with open(self.file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return self._empty_state()
        return self._empty_state()

    def _empty_state(self) -> Dict[str, Any]:
        """빈 상태 반환"""
        return {
            'last_page': 0,
            'collected_items': 0,
            'last_url': None,
            'timestamp': None,
            'completed': False
        }

    def save(self, page: int, url: str, items_count: int):
        """현재 상태 저장"""
        self.state.update({
            'last_page': page,
            'last_url': url,
            'collected_items': items_count,
            'timestamp': datetime.now().isoformat(),
            'completed': False
        })

        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def mark_completed(self):
        """크롤링 완료 표시"""
        self.state['completed'] = True
        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def can_resume(self) -> bool:
        """재개 가능 여부"""
        return self.state['last_page'] > 0 and not self.state['completed']

    def clear(self):
        """체크포인트 삭제"""
        if self.file.exists():
            self.file.unlink()
        self.state = self._empty_state()


class CrawlerException(Exception):
    """크롤러 관련 예외"""
    pass


class ParsingException(Exception):
    """파싱 관련 예외"""
    pass


class ForestBidCrawler:
    """산림청 입찰정보 크롤러"""

    BASE_URL = "https://www.forest.go.kr"
    LIST_URL = "https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardList.do"
    DETAIL_URL = "https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardArticle.do"

    def __init__(self, days=365, delay=1.0, page_delay=2.0, start_date=None, end_date=None):
        """
        초기화

        Args:
            days (int): 수집할 기간 (일 단위) - 하위 호환성
            delay (float): 요청 간 딜레이 (초)
            page_delay (float): 페이지 간 딜레이 (초)
            start_date (datetime): 크롤링 시작일 (이 날짜부터 수집)
            end_date (datetime): 크롤링 종료일 (이 날짜까지 수집)
        """
        self.days = days
        self.delay = delay
        self.page_delay = page_delay

        # start_date가 제공되면 그것을 cutoff_date로 사용
        if start_date:
            self.cutoff_date = start_date if isinstance(start_date, datetime) else datetime.combine(start_date, datetime.min.time())
        else:
            # 하위 호환성: days 방식
            self.cutoff_date = datetime.now() - timedelta(days=days)

        # end_date 저장 (향후 필요시 사용)
        self.end_date = end_date

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

        # 체크포인트 시스템
        self.checkpoint = CrawlCheckpoint()

        # 입력 검증
        self._validate_params(days, delay, page_delay, start_date, end_date)

    def _validate_params(self, days, delay, page_delay, start_date, end_date):
        """입력 파라미터 검증"""
        # 최대 수집 기간: 10년
        max_range_days = 3650

        if start_date and end_date:
            range_days = (end_date - start_date).days if hasattr(end_date, 'days') else (end_date - start_date).total_seconds() / 86400
            if range_days > max_range_days:
                raise ValueError(f"날짜 범위는 최대 {max_range_days}일({max_range_days//365}년)을 초과할 수 없습니다.")
            if range_days < 0:
                raise ValueError("종료일은 시작일보다 나중이어야 합니다.")
        elif days > max_range_days:
            raise ValueError(f"수집 기간은 최대 {max_range_days}일({max_range_days//365}년)을 초과할 수 없습니다.")

        # 딜레이 최소값 검증
        if delay < 0.5:
            raise ValueError("요청 간 딜레이는 최소 0.5초 이상이어야 합니다 (서버 보호).")
        if page_delay < 1.0:
            raise ValueError("페이지 간 딜레이는 최소 1.0초 이상이어야 합니다 (서버 보호).")

        self.logger.info(f"파라미터 검증 완료: days={days}, delay={delay}s, page_delay={page_delay}s")

    def _parse_date_safe(self, date_str: str) -> Optional[datetime]:
        """안전한 날짜 파싱 (타임존 처리 포함)"""
        if not date_str or not date_str.strip():
            return None

        # 먼저 예상 포맷으로 빠른 파싱 시도
        try:
            dt = datetime.strptime(date_str.strip(), '%Y-%m-%d')
            return dt
        except ValueError:
            pass

        # 유연한 파싱 시도
        try:
            dt = date_parser.parse(date_str, fuzzy=False)

            # 합리적인 범위 검증
            if dt.year < 2000 or dt.year > 2100:
                self.logger.warning(f"날짜 범위 벗어남: {date_str} (year={dt.year})")
                return None

            # 타임존이 있으면 UTC 기준으로 변환 후 naive 로 통일
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)

            return dt
        except Exception as e:
            self.logger.warning(f"날짜 파싱 실패: '{date_str}' - {e}")
            return None

    def fetch_page(self, url, params=None, max_retries=3):
        """
        페이지 가져오기 (재시도 로직 포함)

        Args:
            url (str): 요청 URL
            params (dict): 쿼리 파라미터
            max_retries (int): 최대 재시도 횟수

        Returns:
            BeautifulSoup: 파싱된 HTML

        Raises:
            CrawlerException: 모든 재시도 실패 시
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()

                # Rate limit 헤더 확인
                retry_after_header = response.headers.get('Retry-After')
                if retry_after_header:
                    wait_seconds: Optional[float] = None
                    try:
                        wait_seconds = float(retry_after_header)
                    except ValueError:
                        try:
                            retry_dt = parsedate_to_datetime(retry_after_header)
                        except (TypeError, ValueError) as parse_err:
                            self.logger.warning(
                                f"Retry-After 헤더 파싱 실패: {retry_after_header} ({parse_err})"
                            )
                            retry_dt = None

                        if retry_dt:
                            if retry_dt.tzinfo is None:
                                retry_dt = retry_dt.replace(tzinfo=timezone.utc)
                            delta = (retry_dt - datetime.now(timezone.utc)).total_seconds()
                            if delta > 0:
                                wait_seconds = delta

                    if wait_seconds is not None and wait_seconds > 0:
                        bounded_wait = min(wait_seconds, 300.0)
                        self.logger.warning(f"서버에서 {bounded_wait:.1f}초 대기 요청")
                        time.sleep(bounded_wait)

                # 응답 텍스트는 requests가 디코딩하므로 기본값 사용
                return BeautifulSoup(response.text, 'html.parser')

            except requests.exceptions.Timeout as e:
                last_exception = e
                self.logger.warning(f"타임아웃 (시도 {attempt + 1}/{max_retries}): {url}")

            except requests.exceptions.HTTPError as e:
                last_exception = e
                status_code = e.response.status_code if e.response else 'N/A'
                self.logger.warning(f"HTTP 오류 {status_code} (시도 {attempt + 1}/{max_retries}): {url}")

                # 4xx 에러는 재시도 무의미
                if e.response and 400 <= e.response.status_code < 500:
                    self.logger.error(f"클라이언트 오류 (재시도 중단): {status_code}")
                    raise CrawlerException(f"HTTP {status_code} 오류: {url}") from e

            except requests.exceptions.ConnectionError as e:
                last_exception = e
                self.logger.warning(f"연결 오류 (시도 {attempt + 1}/{max_retries}): {e}")

            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.warning(f"요청 실패 (시도 {attempt + 1}/{max_retries}): {e}")

            # 재시도 대기 (지수 백오프, 최대 60초)
            if attempt < max_retries - 1:
                backoff = min(2 ** attempt, 60)  # 최대 60초
                self.logger.info(f"{backoff}초 후 재시도...")
                time.sleep(backoff)

        # 모든 재시도 실패
        self.logger.error(f"페이지 가져오기 완전 실패 ({max_retries}회 시도): {url}")
        raise CrawlerException(f"{max_retries}회 재시도 후 실패: {url}") from last_exception

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

            table = rows[0].find_parent('table') if rows else None
            header_map: Dict[str, int] = {}

            if table:
                header_cells = []

                thead = table.find('thead')
                if thead:
                    header_row = thead.find('tr')
                    if header_row:
                        header_cells = header_row.find_all('th')

                if not header_cells:
                    tbody = table.find('tbody')
                    candidate_row = None
                    if tbody:
                        candidate_row = tbody.find('tr')
                    if not candidate_row:
                        candidate_row = table.find('tr')
                    if candidate_row:
                        header_cells = candidate_row.find_all('th')

                for idx, th in enumerate(header_cells):
                    header_text = th.get_text(strip=True)
                    if header_text:
                        header_map[header_text] = idx

            def _lookup_index(labels: List[str], default: int) -> int:
                for header_text, idx in header_map.items():
                    for label in labels:
                        if label in header_text:
                            return idx
                return default

            number_idx = _lookup_index(['번호', 'No', 'NO'], 0)
            title_idx = _lookup_index(['제목', 'Title'], 1)
            department_idx = _lookup_index(['부서', '담당', '기관'], 2)
            date_idx = _lookup_index(['일자', '날짜', '등록'], 3)
            attachment_idx = _lookup_index(['첨부', '파일'], 4)
            views_idx = _lookup_index(['조회', 'View'], 5)

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

                    def _cell_text(index: int, default: str = 'N/A') -> str:
                        try:
                            if index is not None and index < len(cells):
                                return cells[index].get_text(strip=True)
                        except Exception:
                            pass
                        return default

                    number = _cell_text(number_idx, 'N/A')

                    # 제목 및 링크: 테이블 안의 <a> 태그 우선 검색
                    title_a = row.select_one('a')
                    if title_a:
                        title = title_a.get_text(strip=True)
                        link = title_a.get('href')
                    else:
                        title = _cell_text(title_idx, 'N/A')

                    # 부서: 존재하면 3번째 셀 시도
                    department = _cell_text(department_idx, 'N/A')

                    # 날짜: 4번째 셀 시도
                    if date_idx is not None and date_idx < len(cells):
                        date_str = _cell_text(date_idx, '')
                        if date_str:
                            # 날짜 부분만 추출 (조회수 등이 붙어있을 수 있음)
                            # 예: "2021-02-242937" → "2021-02-24"
                            date_match = re.search(r'(\d{4}[-.\s]\d{1,2}[-.\s]\d{1,2})', date_str)
                            if date_match:
                                clean_date_str = date_match.group(1)
                                post_date = self._parse_date_safe(clean_date_str)
                                date_str = clean_date_str  # 깨끗한 날짜 문자열로 업데이트
                            else:
                                post_date = self._parse_date_safe(date_str)

                    # 조회수: 지정된 헤더 인덱스를 우선 사용
                    try:
                        views_text = ''
                        if views_idx is not None and views_idx < len(cells):
                            views_text = cells[views_idx].get_text(strip=True)
                        else:
                            # fallback: 검색으로 숫자 포함 텍스트 찾기
                            views_text = row.get_text(' ', strip=True)

                        views_numbers = re.findall(r"\d+", views_text.replace(',', ''))
                        views = int(views_numbers[0]) if views_numbers else 0
                    except Exception:
                        views = 0

                    # 첨부파일 유무: 추정 셀의 <img> 또는 파일 아이콘 존재 검사
                    if attachment_idx is not None and attachment_idx < len(cells):
                        try:
                            attach_cell = cells[attachment_idx]
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
        self.logger.info("=" * 60)
        self.logger.info("산림청 입찰정보 크롤링 시작")
        self.logger.info(f"수집 기간: 최근 {self.days}일 (기준일: {self.cutoff_date.strftime('%Y-%m-%d')})")
        self.logger.info("=" * 60)

        # 체크포인트 확인 및 재개
        page_index = 1
        if self.checkpoint.can_resume():
            page_index = self.checkpoint.state['last_page'] + 1
            self.total_items = self.checkpoint.state['collected_items']
            self.logger.info(f"⚡ 중단된 크롤링 재개: 페이지 {page_index}부터 시작 (기존 {self.total_items}개 항목)")
        else:
            # 새로운 크롤링 시작 - 기존 체크포인트 삭제
            self.checkpoint.clear()

        should_continue = True

        while should_continue:
            self.logger.info(f"페이지 {page_index} 처리 중...")

            # 리스트 페이지 가져오기
            params = {
                'mn': 'NKFS_04_01_04',
                'bbsId': 'BBSMSTR_1033',
                'pageIndex': page_index,
                'pageUnit': 10
            }

            try:
                soup = self.fetch_page(self.LIST_URL, params)
            except CrawlerException as e:
                self.logger.error(f"페이지 {page_index} 가져오기 실패, 크롤링 중단: {e}")
                break

            # 리스트 파싱
            items = self.parse_list_page(soup)

            if not items:
                self.logger.warning(f"페이지 {page_index}에 항목 없음, 크롤링 종료")
                break

            # 각 항목 처리
            for idx, item in enumerate(items, 1):
                # 상단 고정 공지는 번호가 비거나 '공지' 표기로 나타나므로 건너뛴다.
                number_text = str(item.get('number', '')).strip()
                is_notice = not number_text or '공지' in number_text

                # 날짜 체크 (공지 제외)
                if item['post_date'] and item['post_date'] < self.cutoff_date and not is_notice:
                    self.logger.info(f"기준일 이전 게시글 도달 ({item['post_date_str']}), 크롤링 종료")
                    should_continue = False
                    break

                self.logger.debug(f"[{idx}/10] {item['title'][:50]}...")

                # 상세 페이지 가져오기
                if item['detail_url']:
                    time.sleep(self.delay)
                    try:
                        detail_soup = self.fetch_page(item['detail_url'])
                        detail_data = self.parse_detail_page(detail_soup, item)
                        self.data.append(detail_data)
                        self.total_items += 1
                    except CrawlerException as e:
                        self.logger.warning(f"상세 페이지 가져오기 실패: {item['title'][:30]}... - {e}")
                        # 기본 정보라도 저장
                        self.data.append(item)
                        self.total_items += 1
                else:
                    self.data.append(item)
                    self.total_items += 1

            # 체크포인트 저장 (매 페이지마다)
            self.checkpoint.save(page_index, self.LIST_URL, self.total_items)

            # 다음 페이지로
            if should_continue:
                page_index += 1
                time.sleep(self.page_delay)

            # 중간 저장 (10페이지마다)
            if page_index % 10 == 0:
                self.logger.info(f"중간 저장 중 (페이지 {page_index})...")
                self.save_to_excel(f'산림청_입찰정보_중간저장_{page_index}.xlsx')

        # 크롤링 완료 - 체크포인트 완료 표시
        self.checkpoint.mark_completed()

        self.logger.info("=" * 60)
        self.logger.info(f"크롤링 완료: 총 {self.total_items}개 항목 수집")
        self.logger.info("=" * 60)

    def save_to_excel(self, filename=None):
        """
        수집한 데이터를 엑셀로 저장

        Args:
            filename (str): 출력 파일명
        """
        if not self.data:
            self.logger.warning("저장할 데이터가 없습니다.")
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
            self.logger.error("출력 가능한 컬럼이 없습니다.")
            return

        ordered_cols = [col for col, _ in available_columns]
        df = df[ordered_cols]

        # 가독성을 위해 라벨링 적용
        rename_map = {col: label for col, label in available_columns}
        df = df.rename(columns=rename_map)

        # 엑셀 저장
        df.to_excel(filename, index=False, engine='openpyxl')
        self.logger.info(f"엑셀 파일 저장 완료: {filename}")


def setup_logging(log_level=logging.INFO):
    """로깅 설정"""
    # 로그 디렉토리 생성
    import os
    os.makedirs('logs', exist_ok=True)

    # 로그 포맷 설정
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # 루트 로거 설정
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # 파일 핸들러 (모든 로그)
            logging.FileHandler(
                f'logs/crawler_{datetime.now().strftime("%Y%m%d")}.log',
                encoding='utf-8'
            ),
            # 콘솔 핸들러 (INFO 이상)
            logging.StreamHandler(sys.stdout)
        ]
    )

    # 로거 가져오기
    logger = logging.getLogger(__name__)
    return logger


def main():
    """실행 진입점"""
    # 로깅 설정
    logger = setup_logging(logging.INFO)

    logger.info("=" * 60)
    logger.info("산림청 입찰정보 크롤러")
    logger.info("=" * 60)

    try:
        # 크롤러 실행
        crawler = ForestBidCrawler(
            days=365,      # 최근 1년
            delay=1.0,     # 요청 간 1초 대기
            page_delay=2.0 # 페이지 간 2초 대기
        )

        crawler.crawl()
        crawler.save_to_excel()

    except KeyboardInterrupt:
        logger.warning("사용자에 의해 중단됨")
        if 'crawler' in locals() and crawler.data:
            logger.info("수집한 데이터 저장 중...")
            crawler.save_to_excel(f'산림청_입찰정보_중단_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')

    except ValueError as e:
        # 입력 검증 오류
        logger.error(f"입력 파라미터 오류: {e}")
        sys.exit(1)

    except CrawlerException as e:
        # 크롤러 오류
        logger.error(f"크롤링 오류: {e}")
        if 'crawler' in locals() and crawler.data:
            logger.info("수집된 데이터 저장 중...")
            crawler.save_to_excel(f'산림청_입찰정보_오류_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
        sys.exit(1)

    except Exception as e:
        logger.exception(f"예상치 못한 오류: {e}")
        sys.exit(1)

    logger.info("프로그램 정상 종료")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()

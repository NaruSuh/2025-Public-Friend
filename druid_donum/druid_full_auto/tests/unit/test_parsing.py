"""
Unit tests for HTML parsing functions
"""
import pytest
from bs4 import BeautifulSoup
from main import ForestBidCrawler


class TestListParsing:
    """리스트 페이지 파싱 테스트"""

    def test_parse_valid_table_row(self):
        """정상적인 테이블 행 파싱"""
        html = """
        <table>
            <tbody>
                <tr>
                    <td>123</td>
                    <td><a href="/detail/123">테스트 입찰 공고</a></td>
                    <td>동부지방산림청</td>
                    <td>2024-10-06</td>
                    <td></td>
                    <td>42</td>
                </tr>
            </tbody>
        </table>
        """
        crawler = ForestBidCrawler(days=365, delay=1.0, page_delay=2.0)
        soup = BeautifulSoup(html, 'html.parser')
        items = crawler.parse_list_page(soup)

        assert len(items) == 1
        assert items[0]['number'] == '123'
        assert items[0]['title'] == '테스트 입찰 공고'
        assert items[0]['department'] == '동부지방산림청'

    def test_parse_empty_table(self):
        """빈 테이블 파싱"""
        html = """
        <table>
            <tbody>
            </tbody>
        </table>
        """
        crawler = ForestBidCrawler(days=365, delay=1.0, page_delay=2.0)
        soup = BeautifulSoup(html, 'html.parser')
        items = crawler.parse_list_page(soup)

        assert items == []

    def test_parse_row_without_link(self):
        """링크 없는 행 처리"""
        html = """
        <table>
            <tbody>
                <tr>
                    <td>공지</td>
                    <td>공지사항입니다</td>
                    <td>산림청</td>
                    <td>2024-10-06</td>
                </tr>
            </tbody>
        </table>
        """
        crawler = ForestBidCrawler(days=365, delay=1.0, page_delay=2.0)
        soup = BeautifulSoup(html, 'html.parser')
        items = crawler.parse_list_page(soup)

        assert len(items) == 1
        assert items[0]['title'] == '공지사항입니다'
        assert items[0]['detail_url'] is None

    def test_parse_malformed_date(self):
        """잘못된 날짜 형식 처리"""
        html = """
        <table>
            <tbody>
                <tr>
                    <td>456</td>
                    <td><a href="/detail/456">테스트</a></td>
                    <td>산림청</td>
                    <td>잘못된날짜</td>
                </tr>
            </tbody>
        </table>
        """
        crawler = ForestBidCrawler(days=365, delay=1.0, page_delay=2.0)
        soup = BeautifulSoup(html, 'html.parser')
        items = crawler.parse_list_page(soup)

        assert len(items) == 1
        assert items[0]['post_date'] is None  # 파싱 실패 시 None

    def test_parse_incomplete_row(self):
        """불완전한 행 처리 (셀 부족)"""
        html = """
        <table>
            <tbody>
                <tr>
                    <td>789</td>
                    <td><a href="/detail/789">제목만 있는 행</a></td>
                </tr>
            </tbody>
        </table>
        """
        crawler = ForestBidCrawler(days=365, delay=1.0, page_delay=2.0)
        soup = BeautifulSoup(html, 'html.parser')
        items = crawler.parse_list_page(soup)

        # 기본값으로 처리되어야 함
        assert len(items) == 1
        assert items[0]['title'] == '제목만 있는 행'
        assert items[0]['department'] == 'N/A'  # 기본값

    def test_parse_row_with_header_cells_in_body(self):
        """데이터 행에서 th가 사용되어도 헤더 매핑이 안정적인지 확인"""
        html = """
        <table>
            <thead>
                <tr>
                    <th>번호</th>
                    <th>제목</th>
                    <th>부서</th>
                    <th>등록일</th>
                    <th>조회수</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <th scope="row">공지</th>
                    <td><a href="/detail/999">공지사항</a></td>
                    <td>산림청</td>
                    <td>2024-10-01</td>
                    <td>15</td>
                </tr>
            </tbody>
        </table>
        """
        crawler = ForestBidCrawler(days=365, delay=1.0, page_delay=2.0)
        soup = BeautifulSoup(html, 'html.parser')
        items = crawler.parse_list_page(soup)

        assert len(items) == 1
        assert items[0]['number'] == '공지'
        assert items[0]['title'] == '공지사항'
        assert items[0]['views'] == 15

    def test_parse_table_with_tbody_header_row(self):
        """thead가 없고 tbody 첫 행이 헤더인 경우에도 컬럼을 정확히 매핑"""
        html = """
        <table>
            <tbody>
                <tr>
                    <th>번호</th>
                    <th>제목</th>
                    <th>부서</th>
                    <th>등록일</th>
                </tr>
                <tr>
                    <td>321</td>
                    <td><a href="/detail/321">테스트 공고</a></td>
                    <td>북부지방산림청</td>
                    <td>2024-09-30</td>
                </tr>
            </tbody>
        </table>
        """
        crawler = ForestBidCrawler(days=365, delay=1.0, page_delay=2.0)
        soup = BeautifulSoup(html, 'html.parser')
        items = crawler.parse_list_page(soup)

        assert len(items) == 1
        assert items[0]['number'] == '321'
        assert items[0]['department'] == '북부지방산림청'


class TestDetailParsing:
    """상세 페이지 파싱 테스트"""

    def test_parse_detail_with_forest_office(self):
        """담당산림청 정보 추출"""
        html = """
        <div class="b_info">
            <strong>[동부지방산림청] 2024년 조림사업 입찰공고</strong>
        </div>
        """
        crawler = ForestBidCrawler(days=365, delay=1.0, page_delay=2.0)
        soup = BeautifulSoup(html, 'html.parser')
        basic_info = {'title': '테스트'}

        result = crawler.parse_detail_page(soup, basic_info)

        assert result['forest_office'] == '동부지방산림청'

    def test_parse_detail_with_author_info(self):
        """작성자 정보 파싱"""
        html = """
        <ul class="bd_view_ul_info">
            <li>
                <span class="info_tit">작성자</span>
                영월국유림관리소 / 김가희 / 033-371-8112
            </li>
        </ul>
        """
        crawler = ForestBidCrawler(days=365, delay=1.0, page_delay=2.0)
        soup = BeautifulSoup(html, 'html.parser')
        basic_info = {'title': '테스트'}

        result = crawler.parse_detail_page(soup, basic_info)

        assert result['department'] == '영월국유림관리소'
        assert result['manager'] == '김가희'
        assert result['contact'] == '033-371-8112'

    def test_parse_detail_missing_info(self):
        """정보 누락 시 기본값 처리"""
        html = """
        <div class="empty"></div>
        """
        crawler = ForestBidCrawler(days=365, delay=1.0, page_delay=2.0)
        soup = BeautifulSoup(html, 'html.parser')
        basic_info = {'title': '테스트'}

        result = crawler.parse_detail_page(soup, basic_info)

        # 기본값 확인
        assert result['forest_office'] == 'N/A'
        assert result['manager'] == 'N/A'
        assert result['contact'] == 'N/A'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
Unit tests for ForestBidCrawler
"""
import pytest
from datetime import datetime, timedelta
from main import ForestBidCrawler, CrawlerException, CrawlCheckpoint


class TestCrawlerValidation:
    """입력 검증 테스트"""

    def test_valid_params(self):
        """정상 파라미터로 크롤러 생성"""
        crawler = ForestBidCrawler(days=365, delay=1.0, page_delay=2.0)
        assert crawler.days == 365
        assert crawler.delay == 1.0
        assert crawler.page_delay == 2.0

    def test_excessive_days_raises_error(self):
        """10년 초과 기간 설정 시 오류"""
        with pytest.raises(ValueError, match="3650일"):
            ForestBidCrawler(days=5000, delay=1.0, page_delay=2.0)

    def test_invalid_delay_raises_error(self):
        """너무 짧은 딜레이 설정 시 오류"""
        with pytest.raises(ValueError, match="0.5초"):
            ForestBidCrawler(days=365, delay=0.1, page_delay=2.0)

    def test_invalid_page_delay_raises_error(self):
        """너무 짧은 페이지 딜레이 설정 시 오류"""
        with pytest.raises(ValueError, match="1.0초"):
            ForestBidCrawler(days=365, delay=1.0, page_delay=0.5)

    def test_date_range_validation(self):
        """날짜 범위 검증"""
        start = datetime(2020, 1, 1)
        end = datetime(2035, 1, 1)  # 15년 범위
        with pytest.raises(ValueError, match="3650일"):
            ForestBidCrawler(
                days=365,
                delay=1.0,
                page_delay=2.0,
                start_date=start,
                end_date=end
            )


class TestDateParsing:
    """날짜 파싱 테스트"""

    def test_parse_standard_date(self):
        """표준 형식 날짜 파싱"""
        crawler = ForestBidCrawler(days=365, delay=1.0, page_delay=2.0)
        result = crawler._parse_date_safe('2024-10-06')
        assert result is not None
        assert result.year == 2024
        assert result.month == 10
        assert result.day == 6

    def test_parse_invalid_date_returns_none(self):
        """잘못된 날짜는 None 반환"""
        crawler = ForestBidCrawler(days=365, delay=1.0, page_delay=2.0)
        result = crawler._parse_date_safe('invalid-date')
        assert result is None

    def test_parse_empty_date_returns_none(self):
        """빈 문자열은 None 반환"""
        crawler = ForestBidCrawler(days=365, delay=1.0, page_delay=2.0)
        result = crawler._parse_date_safe('')
        assert result is None

    def test_parse_future_year_returns_none(self):
        """미래 연도(2100 초과)는 None 반환"""
        crawler = ForestBidCrawler(days=365, delay=1.0, page_delay=2.0)
        result = crawler._parse_date_safe('2150-01-01')
        assert result is None


class TestCheckpoint:
    """체크포인트 시스템 테스트"""

    def test_checkpoint_empty_state(self, tmp_path):
        """빈 체크포인트 상태"""
        checkpoint_path = tmp_path / 'checkpoint.json'
        checkpoint = CrawlCheckpoint(checkpoint_path)
        checkpoint.clear()
        assert checkpoint.can_resume() is False
        assert checkpoint.state['last_page'] == 0

    def test_checkpoint_save_and_load(self, tmp_path):
        """체크포인트 저장 및 로드"""
        checkpoint_path = tmp_path / 'checkpoint.json'
        checkpoint = CrawlCheckpoint(checkpoint_path)
        checkpoint.save(page=5, url='http://test.com', items_count=50)

        # 새로운 인스턴스로 로드
        checkpoint2 = CrawlCheckpoint(checkpoint_path)
        assert checkpoint2.state['last_page'] == 5
        assert checkpoint2.state['collected_items'] == 50
        assert checkpoint2.can_resume() is True

        # 정리
        checkpoint2.clear()

    def test_checkpoint_mark_completed(self, tmp_path):
        """크롤링 완료 표시"""
        checkpoint_path = tmp_path / 'checkpoint.json'
        checkpoint = CrawlCheckpoint(checkpoint_path)
        checkpoint.save(page=10, url='http://test.com', items_count=100)
        assert checkpoint.can_resume() is True

        checkpoint.mark_completed()
        assert checkpoint.can_resume() is False

        # 정리
        checkpoint.clear()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

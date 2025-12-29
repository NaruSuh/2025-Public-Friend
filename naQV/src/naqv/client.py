"""ECOS API Client for Korean Bank Economic Statistics."""

import os
from typing import Optional
from urllib.parse import quote

import httpx

from .models import (
    KeyStatistic,
    StatisticData,
    StatisticItem,
    StatisticMeta,
    StatisticTable,
    StatisticWord,
)


class EcosError(Exception):
    """ECOS API Error."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class EcosClient:
    """한국은행 ECOS API 클라이언트.

    Base URL: https://ecos.bok.or.kr/api/

    Available services:
    - KeyStatisticList: 100대 통계지표
    - StatisticTableList: 서비스 통계 목록
    - StatisticItemList: 통계 세부항목 목록
    - StatisticSearch: 통계 조회 조건 (실제 데이터)
    - StatisticMeta: 통계 메타DB
    - StatisticWord: 통계 용어사전
    """

    BASE_URL = "https://ecos.bok.or.kr/api"

    def __init__(
        self,
        api_key: Optional[str] = None,
        language: str = "kr",
        format: str = "json",
    ) -> None:
        """Initialize ECOS client.

        Args:
            api_key: ECOS API key. If None, reads from ECOS_API_KEY env var.
            language: Response language - 'kr' (Korean) or 'en' (English).
            format: Response format - 'json' or 'xml'.
        """
        self.api_key = api_key or os.environ.get("ECOS_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Set ECOS_API_KEY or pass api_key.")

        self.language = language
        self.format = format
        self._client = httpx.Client(timeout=30.0)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "EcosClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(
        self,
        service: str,
        start: int = 1,
        end: int = 100,
        *args: str,
    ) -> dict:
        """Make API request.

        URL format: {BASE_URL}/{service}/{api_key}/{format}/{language}/{start}/{end}/{args...}
        """
        path_parts = [
            service,
            self.api_key,
            self.format,
            self.language,
            str(start),
            str(end),
        ]
        path_parts.extend(quote(str(arg), safe="") for arg in args if arg)

        url = f"{self.BASE_URL}/{'/'.join(path_parts)}"
        response = self._client.get(url)
        response.raise_for_status()

        data = response.json()

        # Check for API errors
        if "RESULT" in data:
            result = data["RESULT"]
            code_str = result.get("CODE", "0")
            # Handle codes like "INFO-200" or just "200"
            if "-" in str(code_str):
                code = int(code_str.split("-")[1])
            else:
                code = int(code_str)
            message = result.get("MESSAGE", "Unknown error")
            raise EcosError(code, message)

        return data

    def get_key_statistics(
        self,
        start: int = 1,
        end: int = 100,
    ) -> list[KeyStatistic]:
        """100대 통계지표 조회.

        Args:
            start: 시작 번호
            end: 끝 번호

        Returns:
            List of KeyStatistic objects
        """
        data = self._request("KeyStatisticList", start, end)
        rows = data.get("KeyStatisticList", {}).get("row", [])

        return [
            KeyStatistic(
                class_name=row.get("CLASS_NAME", ""),
                keystat_name=row.get("KEYSTAT_NAME", ""),
                data_value=row.get("DATA_VALUE", ""),
                cycle=row.get("CYCLE", ""),
                unit_name=row.get("UNIT_NAME", ""),
            )
            for row in rows
        ]

    def get_statistic_tables(
        self,
        stat_code: Optional[str] = None,
        start: int = 1,
        end: int = 100,
    ) -> list[StatisticTable]:
        """서비스 통계 목록 조회.

        Args:
            stat_code: 통계표코드 (optional, for filtering)
            start: 시작 번호
            end: 끝 번호

        Returns:
            List of StatisticTable objects
        """
        args = [stat_code] if stat_code else []
        data = self._request("StatisticTableList", start, end, *args)
        rows = data.get("StatisticTableList", {}).get("row", [])

        return [
            StatisticTable(
                p_stat_code=row.get("P_STAT_CODE", ""),
                stat_code=row.get("STAT_CODE", ""),
                stat_name=row.get("STAT_NAME", ""),
                cycle=row.get("CYCLE", ""),
                srch_yn=row.get("SRCH_YN", ""),
                org_name=row.get("ORG_NAME", ""),
            )
            for row in rows
        ]

    def get_statistic_items(
        self,
        stat_code: str,
        start: int = 1,
        end: int = 100,
    ) -> list[StatisticItem]:
        """통계 세부항목 목록 조회.

        Args:
            stat_code: 통계표코드 (required)
            start: 시작 번호
            end: 끝 번호

        Returns:
            List of StatisticItem objects
        """
        data = self._request("StatisticItemList", start, end, stat_code)
        rows = data.get("StatisticItemList", {}).get("row", [])

        return [
            StatisticItem(
                stat_code=row.get("STAT_CODE", ""),
                stat_name=row.get("STAT_NAME", ""),
                item_code1=row.get("ITEM_CODE1", ""),
                item_name1=row.get("ITEM_NAME1", ""),
                item_code2=row.get("ITEM_CODE2"),
                item_name2=row.get("ITEM_NAME2"),
                item_code3=row.get("ITEM_CODE3"),
                item_name3=row.get("ITEM_NAME3"),
                item_code4=row.get("ITEM_CODE4"),
                item_name4=row.get("ITEM_NAME4"),
                cycle=row.get("CYCLE"),
                start_time=row.get("START_TIME"),
                end_time=row.get("END_TIME"),
                data_cnt=int(row["DATA_CNT"]) if row.get("DATA_CNT") else None,
            )
            for row in rows
        ]

    def search(
        self,
        stat_code: str,
        cycle: str,
        start_time: str,
        end_time: str,
        item_code1: str = "?",
        item_code2: str = "?",
        item_code3: str = "?",
        item_code4: str = "?",
        start: int = 1,
        end: int = 100,
    ) -> list[StatisticData]:
        """통계 데이터 조회 (핵심 API).

        Args:
            stat_code: 통계표코드
            cycle: 주기 (Y: 년, Q: 분기, M: 월, D: 일)
            start_time: 검색시작일자 (YYYY, YYYYMM, YYYYMMDD 등)
            end_time: 검색종료일자
            item_code1~4: 통계항목코드 (?: 전체, 특정코드: 해당항목만)
            start: 시작 번호
            end: 끝 번호

        Returns:
            List of StatisticData objects
        """
        data = self._request(
            "StatisticSearch",
            start,
            end,
            stat_code,
            cycle,
            start_time,
            end_time,
            item_code1,
            item_code2,
            item_code3,
            item_code4,
        )
        rows = data.get("StatisticSearch", {}).get("row", [])

        return [
            StatisticData(
                stat_code=row.get("STAT_CODE", ""),
                stat_name=row.get("STAT_NAME", ""),
                item_code1=row.get("ITEM_CODE1", ""),
                item_name1=row.get("ITEM_NAME1", ""),
                item_code2=row.get("ITEM_CODE2"),
                item_name2=row.get("ITEM_NAME2"),
                item_code3=row.get("ITEM_CODE3"),
                item_name3=row.get("ITEM_NAME3"),
                item_code4=row.get("ITEM_CODE4"),
                item_name4=row.get("ITEM_NAME4"),
                unit_name=row.get("UNIT_NAME"),
                time=row.get("TIME"),
                data_value=row.get("DATA_VALUE"),
            )
            for row in rows
        ]

    def get_meta(
        self,
        data_name: str,
        start: int = 1,
        end: int = 100,
    ) -> list[StatisticMeta]:
        """통계 메타DB 조회.

        Args:
            data_name: 데이터명 (예: '경제심리지수')
            start: 시작 번호
            end: 끝 번호

        Returns:
            List of StatisticMeta objects
        """
        data = self._request("StatisticMeta", start, end, data_name)
        rows = data.get("StatisticMeta", {}).get("row", [])

        return [
            StatisticMeta(
                lvl=int(row.get("LVL", 0)),
                p_cont_code=row.get("P_CONT_CODE", ""),
                cont_code=row.get("CONT_CODE", ""),
                cont_name=row.get("CONT_NAME", ""),
                meta_data=row.get("META_DATA", ""),
            )
            for row in rows
        ]

    def search_word(
        self,
        word: str,
        start: int = 1,
        end: int = 100,
    ) -> list[StatisticWord]:
        """통계 용어사전 검색.

        Args:
            word: 검색할 용어
            start: 시작 번호
            end: 끝 번호

        Returns:
            List of StatisticWord objects
        """
        data = self._request("StatisticWord", start, end, word)
        rows = data.get("StatisticWord", {}).get("row", [])

        return [
            StatisticWord(
                word=row.get("WORD", ""),
                content=row.get("CONTENT", ""),
            )
            for row in rows
        ]

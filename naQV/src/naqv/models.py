"""Data models for ECOS API responses."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class KeyStatistic:
    """100대 통계지표 항목."""

    class_name: str  # 통계그룹명
    keystat_name: str  # 통계명
    data_value: str  # 값
    cycle: str  # 시점
    unit_name: str  # 단위


@dataclass
class StatisticTable:
    """통계표 정보."""

    p_stat_code: str  # 상위통계표코드
    stat_code: str  # 통계표코드
    stat_name: str  # 통계명
    cycle: str  # 주기 (Y, Q, M, D)
    srch_yn: str  # 검색가능여부
    org_name: str  # 출처


@dataclass
class StatisticItem:
    """통계 세부항목."""

    stat_code: str  # 통계표코드
    stat_name: str  # 통계명
    item_code1: str  # 통계항목코드1
    item_name1: str  # 통계항목명1
    item_code2: Optional[str] = None  # 통계항목코드2
    item_name2: Optional[str] = None  # 통계항목명2
    item_code3: Optional[str] = None  # 통계항목코드3
    item_name3: Optional[str] = None  # 통계항목명3
    item_code4: Optional[str] = None  # 통계항목코드4
    item_name4: Optional[str] = None  # 통계항목명4
    cycle: Optional[str] = None  # 주기
    start_time: Optional[str] = None  # 수록시작일자
    end_time: Optional[str] = None  # 수록종료일자
    data_cnt: Optional[int] = None  # 자료수


@dataclass
class StatisticData:
    """통계 데이터 조회 결과."""

    stat_code: str  # 통계표코드
    stat_name: str  # 통계명
    item_code1: str  # 통계항목코드1
    item_name1: str  # 통계항목명1
    item_code2: Optional[str] = None
    item_name2: Optional[str] = None
    item_code3: Optional[str] = None
    item_name3: Optional[str] = None
    item_code4: Optional[str] = None
    item_name4: Optional[str] = None
    unit_name: Optional[str] = None  # 단위
    time: Optional[str] = None  # 시점
    data_value: Optional[str] = None  # 값


@dataclass
class StatisticMeta:
    """통계 메타데이터."""

    lvl: int  # 레벨
    p_cont_code: str  # 상위통계항목코드
    cont_code: str  # 통계항목코드
    cont_name: str  # 통계항목명
    meta_data: str  # 메타데이터


@dataclass
class StatisticWord:
    """통계 용어."""

    word: str  # 용어
    content: str  # 용어설명

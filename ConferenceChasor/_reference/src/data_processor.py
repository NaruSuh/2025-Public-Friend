"""
데이터 처리 및 통계 분석 모듈
CSV, Excel 등 다양한 형식의 설문조사 데이터를 처리하고 통계 분석
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
import json


class SurveyDataProcessor:
    """설문조사 데이터 처리 및 통계 분석 클래스"""

    def __init__(self, data_path: str):
        """
        Args:
            data_path: 데이터 파일 경로 (CSV, Excel 등)
        """
        self.data_path = Path(data_path)
        self.df = None
        self.stats = {}

    def load_data(self) -> pd.DataFrame:
        """데이터 로드"""
        if self.data_path.suffix == '.csv':
            self.df = pd.read_csv(self.data_path, encoding='utf-8-sig')
        elif self.data_path.suffix in ['.xlsx', '.xls']:
            self.df = pd.read_excel(self.data_path)
        elif self.data_path.suffix == '.json':
            self.df = pd.read_json(self.data_path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {self.data_path.suffix}")

        return self.df

    def get_basic_stats(self) -> Dict[str, Any]:
        """기본 통계 정보"""
        if self.df is None:
            self.load_data()

        stats = {
            'total_responses': len(self.df),
            'columns': list(self.df.columns),
            'missing_data': self.df.isnull().sum().to_dict(),
        }

        return stats

    def analyze_numeric_column(self, column: str) -> Dict[str, Any]:
        """숫자형 컬럼 분석 (평점, 점수 등)"""
        if self.df is None:
            self.load_data()

        if column not in self.df.columns:
            raise ValueError(f"컬럼 '{column}'을 찾을 수 없습니다")

        data = self.df[column].dropna()

        analysis = {
            'column_name': column,
            'count': int(len(data)),
            'mean': float(data.mean()),
            'median': float(data.median()),
            'std': float(data.std()),
            'min': float(data.min()),
            'max': float(data.max()),
            'q1': float(data.quantile(0.25)),
            'q3': float(data.quantile(0.75)),
        }

        # 분포 계산 (1-5점 척도 가정)
        value_counts = data.value_counts().sort_index()
        analysis['distribution'] = value_counts.to_dict()

        # 백분율 분포
        analysis['distribution_percent'] = (value_counts / len(data) * 100).to_dict()

        return analysis

    def analyze_categorical_column(self, column: str, top_n: int = 10) -> Dict[str, Any]:
        """범주형 컬럼 분석 (선택지, 텍스트 응답 등)"""
        if self.df is None:
            self.load_data()

        if column not in self.df.columns:
            raise ValueError(f"컬럼 '{column}'을 찾을 수 없습니다")

        data = self.df[column].dropna()
        value_counts = data.value_counts()

        analysis = {
            'column_name': column,
            'count': int(len(data)),
            'unique_values': int(data.nunique()),
            'top_values': value_counts.head(top_n).to_dict(),
            'top_values_percent': (value_counts.head(top_n) / len(data) * 100).to_dict(),
        }

        return analysis

    def analyze_satisfaction_scores(self, score_columns: List[str]) -> Dict[str, Any]:
        """만족도 점수 항목들 종합 분석"""
        if self.df is None:
            self.load_data()

        results = {}
        overall_scores = []

        for col in score_columns:
            if col in self.df.columns:
                col_analysis = self.analyze_numeric_column(col)
                results[col] = col_analysis
                overall_scores.extend(self.df[col].dropna().tolist())

        # 전체 평균 만족도
        if overall_scores:
            results['overall'] = {
                'mean': float(np.mean(overall_scores)),
                'median': float(np.median(overall_scores)),
                'std': float(np.std(overall_scores)),
                'total_responses': len(overall_scores),
            }

        return results

    def calculate_satisfaction_index(self, score_columns: List[str],
                                     max_score: float = 5.0) -> float:
        """만족도 지수 계산 (0-100 스케일)"""
        if self.df is None:
            self.load_data()

        scores = []
        for col in score_columns:
            if col in self.df.columns:
                scores.extend(self.df[col].dropna().tolist())

        if not scores:
            return 0.0

        # 0-100 스케일로 변환
        satisfaction_index = (np.mean(scores) / max_score) * 100
        return round(float(satisfaction_index), 2)

    def get_text_responses(self, column: str) -> List[str]:
        """텍스트 응답 추출 (주관식 답변 등)"""
        if self.df is None:
            self.load_data()

        if column not in self.df.columns:
            return []

        responses = self.df[column].dropna().astype(str).tolist()
        return [r for r in responses if r.strip()]

    def export_summary(self, output_path: str):
        """분석 결과 JSON으로 저장"""
        summary = {
            'basic_stats': self.get_basic_stats(),
            'statistics': self.stats,
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

    def cross_tabulation(self, column1: str, column2: str) -> pd.DataFrame:
        """교차 분석"""
        if self.df is None:
            self.load_data()

        return pd.crosstab(self.df[column1], self.df[column2], margins=True)


def quick_analysis(data_path: str, score_columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """빠른 분석 함수"""
    processor = SurveyDataProcessor(data_path)
    processor.load_data()

    result = {
        'basic_stats': processor.get_basic_stats(),
    }

    if score_columns:
        result['satisfaction_analysis'] = processor.analyze_satisfaction_scores(score_columns)
        result['satisfaction_index'] = processor.calculate_satisfaction_index(score_columns)

    return result

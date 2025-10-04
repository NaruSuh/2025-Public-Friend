#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
산림청 입찰정보 크롤러 - Streamlit Web App
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from main import ForestBidCrawler
import os

# 페이지 설정
st.set_page_config(
    page_title="산림청 입찰정보 크롤러",
    page_icon="🌲",
    layout="wide"
)

# 제목
st.title("🌲 산림청 입찰정보 크롤러")
st.markdown("---")

# 사이드바 설정
st.sidebar.header("⚙️ 크롤링 설정")

# 수집 기간 설정
days = st.sidebar.slider(
    "수집 기간 (일)",
    min_value=7,
    max_value=365,
    value=30,
    step=7,
    help="최근 며칠 동안의 입찰정보를 수집할지 설정합니다."
)

# 요청 간격 설정
delay = st.sidebar.slider(
    "요청 간 딜레이 (초)",
    min_value=0.5,
    max_value=3.0,
    value=1.0,
    step=0.5,
    help="각 요청 사이의 대기 시간입니다. 너무 짧으면 서버에서 차단될 수 있습니다."
)

page_delay = st.sidebar.slider(
    "페이지 간 딜레이 (초)",
    min_value=1.0,
    max_value=5.0,
    value=2.0,
    step=0.5,
    help="페이지 이동 시 대기 시간입니다."
)

# 메인 영역
col1, col2 = st.columns([2, 1])

with col1:
    st.info(f"""
    📅 **수집 기간**: 최근 {days}일
    ⏱️ **요청 딜레이**: {delay}초
    📄 **페이지 딜레이**: {page_delay}초
    🎯 **대상**: 산림청 입찰공고 게시판
    """)

with col2:
    st.metric("수집 기준일", (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'))

# 크롤링 시작 버튼
if st.button("🚀 크롤링 시작", type="primary", use_container_width=True):

    # 진행 상황 표시 영역
    progress_bar = st.progress(0)
    status_text = st.empty()
    info_text = st.empty()

    # 결과 테이블 표시 영역
    result_placeholder = st.empty()

    try:
        # 크롤러 초기화
        crawler = ForestBidCrawler(
            days=days,
            delay=delay,
            page_delay=page_delay
        )

        status_text.info("🔄 크롤링 시작...")

        # 크롤링 실행 (수정된 버전)
        page_index = 1
        should_continue = True
        total_pages_estimate = 50  # 예상 페이지 수

        while should_continue:
            info_text.text(f"📄 페이지 {page_index} 처리 중...")

            # 리스트 페이지 가져오기
            params = {
                'mn': 'NKFS_04_01_04',
                'bbsId': 'BBSMSTR_1033',
                'pageIndex': page_index,
                'pageUnit': 10
            }

            soup = crawler.fetch_page(crawler.LIST_URL, params)

            if not soup:
                break

            items = crawler.parse_list_page(soup)

            if not items:
                break

            # 각 항목 처리
            for idx, item in enumerate(items, 1):
                # 날짜 체크
                if item['post_date'] and item['post_date'] < crawler.cutoff_date:
                    should_continue = False
                    break

                # 상세 페이지 가져오기
                if item['detail_url']:
                    time.sleep(crawler.delay)
                    detail_soup = crawler.fetch_page(item['detail_url'])

                    if detail_soup:
                        detail_data = crawler.parse_detail_page(detail_soup, item)
                        crawler.data.append(detail_data)
                        crawler.total_items += 1
                else:
                    crawler.data.append(item)
                    crawler.total_items += 1

                # 진행률 업데이트
                progress = min(page_index / total_pages_estimate, 0.99)
                progress_bar.progress(progress)

            # 중간 결과 표시
            if crawler.data:
                df = pd.DataFrame(crawler.data)
                result_placeholder.dataframe(
                    df.head(20),
                    use_container_width=True,
                    hide_index=True
                )

            if should_continue:
                page_index += 1
                time.sleep(crawler.page_delay)

            # 최대 페이지 제한 (무한 루프 방지)
            if page_index > 100:
                break

        progress_bar.progress(1.0)
        status_text.success(f"✅ 크롤링 완료! 총 {crawler.total_items}개 항목 수집")

        # 최종 결과 표시
        if crawler.data:
            df = pd.DataFrame(crawler.data)

            # 컬럼 순서 정리
            columns = [
                'number', 'title', 'forest_office', 'department',
                'manager', 'contact', 'post_date_str', 'views',
                'has_attachment', 'detail_url'
            ]
            columns = [col for col in columns if col in df.columns]
            df = df[columns]

            # 컬럼명 한글화
            df.columns = [
                '번호', '제목', '담당산림청', '담당부서',
                '담당자', '연락처', '공고일자', '조회수',
                '첨부', 'URL'
            ][:len(columns)]

            # 결과 표시
            st.markdown("---")
            st.subheader("📊 수집 결과")

            # 통계 정보
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("총 항목 수", len(df))
            with col2:
                st.metric("담당산림청 수", df['담당산림청'].nunique() if '담당산림청' in df.columns else 0)
            with col3:
                st.metric("수집 페이지", page_index)
            with col4:
                st.metric("평균 조회수", int(df['조회수'].astype(str).str.extract('(\d+)')[0].astype(float).mean()) if '조회수' in df.columns else 0)

            # 데이터 테이블
            st.dataframe(df, use_container_width=True, hide_index=True)

            # 엑셀 다운로드
            filename = f"산림청_입찰정보_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

            # 엑셀 파일 생성
            df.to_excel(filename, index=False, engine='openpyxl')

            # 다운로드 버튼
            with open(filename, 'rb') as f:
                st.download_button(
                    label="📥 엑셀 파일 다운로드",
                    data=f.read(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            # 임시 파일 삭제
            os.remove(filename)

    except Exception as e:
        status_text.error(f"❌ 오류 발생: {e}")
        st.exception(e)

# 사용 안내
st.markdown("---")
st.markdown("""
### 📖 사용 안내

1. **왼쪽 사이드바**에서 크롤링 설정을 조정하세요.
2. **크롤링 시작** 버튼을 클릭하여 데이터 수집을 시작합니다.
3. 진행 상황을 실시간으로 확인할 수 있습니다.
4. 완료 후 **엑셀 파일 다운로드** 버튼으로 결과를 저장하세요.

### ⚠️ 주의사항

- 크롤링에 시간이 소요될 수 있습니다 (수집 기간에 따라 수 분 ~ 수십 분)
- 서버 부하를 최소화하기 위해 적절한 딜레이를 설정하세요
- 공개된 정보만 수집하며, 연구 목적으로만 사용하세요

### 📊 수집 정보

- 번호, 제목, 담당산림청, 담당부서
- 담당자, 연락처, 공고일자, 조회수
- 첨부파일 여부, 상세 페이지 URL
""")

# 푸터
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "🌲 산림청 입찰정보 크롤러 v1.0 | "
    "산림공학 전문가 / 산림학 연구자"
    "</div>",
    unsafe_allow_html=True
)

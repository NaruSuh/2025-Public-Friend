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
from io import BytesIO
from functools import lru_cache

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

# 수집 기간 설정 (년 단위)
years = st.sidebar.slider(
    "수집 기간 (년)",
    min_value=1,
    max_value=10,
    value=1,
    step=1,
    help="지난 몇 년 동안의 입찰정보를 수집할지 설정합니다."
)

# 년을 일로 변환
days = years * 365

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
    min_value=0.5,
    max_value=5.0,
    value=2.0,
    step=0.5,
    help="페이지 이동 시 대기 시간입니다."
)

# 사이드바 하단: 크롤링 히스토리
if st.session_state.crawl_history:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 이전 크롤링 결과")

    for idx, item in enumerate(reversed(st.session_state.crawl_history)):
        # timestamp를 unique key로 사용
        unique_key = item['timestamp'].replace(':', '').replace(' ', '').replace('-', '')

        with st.sidebar.expander(f"🕐 {item['timestamp'].replace('_', ' ')}", expanded=False):
            st.write(f"**수집 기간**: {item['period']}")
            st.write(f"**항목 수**: {item['total_items']}개")

            # 다운로드 버튼
            col_a, col_b = st.columns(2)

            with col_a:
                # Excel 다운로드 (캐싱 사용)
                try:
                    # DataFrame을 dict로 변환하여 캐싱 가능하게
                    df_dict = item['data'].to_dict()
                    excel_data = generate_excel_data(df_dict, item['timestamp'])

                    st.download_button(
                        label="📥 Excel",
                        data=excel_data,
                        file_name=f"산림청_입찰_{item['timestamp']}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"excel_{unique_key}"
                    )
                except Exception as e:
                    st.error(f"Excel 생성 실패")

            with col_b:
                # CSV 다운로드 (캐싱 사용)
                try:
                    # DataFrame을 dict로 변환하여 캐싱 가능하게
                    df_dict = item['data'].to_dict()
                    csv = generate_csv_data(df_dict, item['timestamp'])

                    st.download_button(
                        label="📥 CSV",
                        data=csv,
                        file_name=f"산림청_입찰_{item['timestamp']}.csv",
                        mime="text/csv",
                        key=f"csv_{unique_key}"
                    )
                except Exception as e:
                    st.error(f"CSV 생성 실패")

# 메인 영역
col1, col2 = st.columns([2, 1])

with col1:
    st.info(f"""
    📅 **수집 기간**: 최근 {years}년 (약 {days}일)
    ⏱️ **요청 딜레이**: {delay}초
    📄 **페이지 딜레이**: {page_delay}초
    🎯 **대상**: 산림청 입찰공고 게시판
    """)

with col2:
    st.metric("수집 기준일", (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'))

# 세션 상태 초기화
if 'crawl_logs' not in st.session_state:
    st.session_state.crawl_logs = []
if 'crawl_data' not in st.session_state:
    st.session_state.crawl_data = None
if 'crawl_completed' not in st.session_state:
    st.session_state.crawl_completed = False
if 'crawl_history' not in st.session_state:
    st.session_state.crawl_history = []  # 완료된 크롤링 히스토리

# 로그 추가 함수
def add_log(message, log_type="INFO"):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    st.session_state.crawl_logs.append(f"[{timestamp}] [{log_type}] {message}")

# Excel 데이터 생성 함수 (캐싱)
@st.cache_data
def generate_excel_data(df_dict, timestamp):
    """DataFrame을 Excel 바이너리로 변환 (캐싱됨)"""
    df = pd.DataFrame(df_dict)
    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    return buffer.getvalue()

# CSV 데이터 생성 함수 (캐싱)
@st.cache_data
def generate_csv_data(df_dict, timestamp):
    """DataFrame을 CSV로 변환 (캐싱됨)"""
    df = pd.DataFrame(df_dict)
    return df.to_csv(index=False, encoding='utf-8-sig')

# 크롤링 실행 함수 (중복 제거)
def run_crawling(years, days, delay, page_delay):
    """크롤링 실행 및 결과 반환"""
    # years를 전역처럼 사용하기 위해 함수 내부에서 접근 가능하게 저장
    crawl_years = years
    # 진행 상황 표시 영역
    progress_bar = st.progress(0)
    status_text = st.empty()
    info_text = st.empty()
    result_placeholder = st.empty()

    try:
        add_log(f"크롤링 시작 - 수집 기간: 최근 {years}년 ({days}일)")
        add_log(f"설정 - 요청 딜레이: {delay}초, 페이지 딜레이: {page_delay}초")

        # 크롤러 초기화
        crawler = ForestBidCrawler(
            days=days,
            delay=delay,
            page_delay=page_delay
        )

        status_text.info("🔄 크롤링 시작...")

        # 크롤링 실행
        page_index = 1
        should_continue = True
        total_pages_estimate = 50

        while should_continue:
            info_text.text(f"📄 페이지 {page_index} 처리 중...")
            add_log(f"페이지 {page_index} 처리 시작")

            # 리스트 페이지 가져오기
            params = {
                'mn': 'NKFS_04_01_04',
                'bbsId': 'BBSMSTR_1033',
                'pageIndex': page_index,
                'pageUnit': 10
            }

            soup = crawler.fetch_page(crawler.LIST_URL, params)

            if not soup:
                add_log(f"페이지 {page_index} 가져오기 실패", "ERROR")
                break

            items = crawler.parse_list_page(soup)

            if not items:
                add_log(f"페이지 {page_index}에 항목 없음", "WARNING")
                break

            add_log(f"페이지 {page_index}에서 {len(items)}개 항목 발견")

            # 각 항목 처리
            for idx, item in enumerate(items, 1):
                # 날짜 체크
                if item['post_date'] and item['post_date'] < crawler.cutoff_date:
                    add_log(f"기준일 이전 게시글 도달 ({item['post_date_str']}) - 크롤링 종료", "INFO")
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
                        add_log(f"항목 수집 완료: {item['title'][:30]}...")
                    else:
                        add_log(f"상세 페이지 가져오기 실패: {item['title'][:30]}...", "ERROR")
                        crawler.data.append(item)
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
                add_log("최대 페이지 수(100) 도달 - 크롤링 종료", "WARNING")
                break

        progress_bar.progress(1.0)
        status_text.success(f"✅ 크롤링 완료! 총 {crawler.total_items}개 항목 수집")
        add_log(f"크롤링 완료 - 총 {crawler.total_items}개 항목 수집")

        # 데이터 처리 및 반환
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

            # 세션에 데이터 저장
            st.session_state.crawl_data = df
            st.session_state.crawl_completed = True

            # 히스토리에 추가 (최대 5개까지만 유지)
            history_item = {
                'timestamp': datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),  # 파일명 안전
                'data': df.copy(),
                'total_items': len(df),
                'period': f"{crawl_years}년"
            }
            st.session_state.crawl_history.append(history_item)

            # 최대 5개까지만 유지 (메모리 절약)
            if len(st.session_state.crawl_history) > 5:
                st.session_state.crawl_history.pop(0)  # 가장 오래된 것 제거

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
                # 평균 조회수 계산 (안전하게 처리)
                avg_views = 0
                if '조회수' in df.columns and len(df) > 0:
                    try:
                        views_numbers = df['조회수'].astype(str).str.extract('(\d+)')[0].astype(float)
                        avg_views = int(views_numbers.mean()) if not views_numbers.isna().all() else 0
                    except:
                        avg_views = 0
                st.metric("평균 조회수", avg_views)

            # 데이터 테이블
            st.dataframe(df, use_container_width=True, hide_index=True)

            return True
        else:
            return False

    except Exception as e:
        status_text.error(f"❌ 오류 발생: {e}")
        add_log(f"오류 발생: {str(e)}", "ERROR")
        st.exception(e)
        return False

# 크롤링 시작 버튼
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    start_crawl = st.button("🚀 크롤링 시작", type="primary", use_container_width=True)

with col_btn2:
    export_data = st.button("📥 크롤링 및 완료시 엑셀파일 작성", type="secondary", use_container_width=True)

# 크롤링 시작 버튼
if start_crawl:
    # 초기화
    st.session_state.crawl_logs = []
    st.session_state.crawl_data = None
    st.session_state.crawl_completed = False

    # 크롤링 실행
    run_crawling(years, days, delay, page_delay)

# "크롤링 및 완료시 엑셀파일 작성" 버튼 기능
if export_data:
    # 초기화
    st.session_state.crawl_logs = []
    st.session_state.crawl_data = None
    st.session_state.crawl_completed = False

    # 크롤링 실행
    run_crawling(years, days, delay, page_delay)

# 크롤링 완료 후 다운로드 섹션 (두 버튼 모두에서 사용 가능)
if st.session_state.crawl_completed and st.session_state.crawl_data is not None:
    st.markdown("---")
    st.subheader("📥 데이터 다운로드")

    df = st.session_state.crawl_data
    col1, col2 = st.columns(2)

    with col1:
        # 엑셀 다운로드
        try:
            buffer = BytesIO()
            df.to_excel(buffer, index=False, engine='openpyxl')
            excel_data = buffer.getvalue()

            st.download_button(
                label="📥 엑셀 파일 다운로드 (.xlsx)",
                data=excel_data,
                file_name=f"산림청_입찰정보_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"엑셀 생성 실패: {e}")

    with col2:
        # CSV 다운로드
        csv = df.to_csv(index=False, encoding='utf-8-sig')

        st.download_button(
            label="📥 CSV 파일 다운로드 (.csv)",
            data=csv,
            file_name=f"산림청_입찰정보_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# 로그 뷰어 (좌측 하단)
if st.session_state.crawl_logs and len(st.session_state.crawl_logs) > 0:
    st.markdown("---")

    log_col1, log_col2 = st.columns([3, 1])

    with log_col1:
        st.subheader("📋 크롤링 로그")

    with log_col2:
        # 로그 다운로드 버튼
        log_content = "# 산림청 입찰정보 크롤링 로그\n\n"
        log_content += f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        log_content += "## 로그 내역\n\n"
        log_content += "\n".join(st.session_state.crawl_logs)

        st.download_button(
            label="📥 로그 다운로드 (.md)",
            data=log_content,
            file_name=f"크롤링_로그_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )

    # 로그 표시 (확장 가능한 형태)
    with st.expander("로그 보기", expanded=False):
        log_text = "\n".join(st.session_state.crawl_logs)
        st.text_area(
            "로그 내용",
            value=log_text,
            height=300,
            disabled=True,
            label_visibility="collapsed"
        )

# 사용 안내
st.markdown("---")
st.markdown("""
### 📖 사용 안내

1. **왼쪽 사이드바**에서 크롤링 설정을 조정하세요.
2. **크롤링 시작** 버튼을 클릭하여 데이터 수집을 시작합니다.
3. 진행 상황을 실시간으로 확인할 수 있습니다.
4. 완료 후 **엑셀/CSV 파일 다운로드** 버튼으로 결과를 저장하세요.
5. **로그 보기**에서 크롤링 과정을 확인하고, 로그를 마크다운 파일로 다운로드할 수 있습니다.

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

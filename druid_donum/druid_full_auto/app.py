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
import logging
import traceback

APP_VERSION = "Ver 1.1.02"

# 페이지 설정
st.set_page_config(
    page_title="산림청 입찰정보 크롤러",
    page_icon="🌲",
    layout="wide"
)

# 세션 상태 초기화 (가장 먼저!)
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
def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """DataFrame을 Excel 바이너리로 변환(안정적 직렬화)"""
    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    return buffer.getvalue()

# CSV 데이터 생성 함수 (캐싱)
def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

# 제목
st.markdown(
    f"<div style='text-align: left; font-weight: 600; color: #6c757d;'>{APP_VERSION}</div>",
    unsafe_allow_html=True
)
st.title("🌲 산림청 입찰정보 크롤러")
st.markdown("---")

# 사이드바 설정
st.sidebar.header("⚙️ 크롤링 설정")

# 수집 기간 설정 (날짜 범위)
st.sidebar.markdown("#### 📅 수집 기간 설정")

col_date1, col_date2 = st.sidebar.columns(2)

with col_date1:
    start_date = st.date_input(
        "시작일",
        value=datetime.now() - timedelta(days=365),
        max_value=datetime.now(),
        help="크롤링 시작 날짜"
    )

with col_date2:
    end_date = st.date_input(
        "종료일",
        value=datetime.now(),
        max_value=datetime.now(),
        help="크롤링 종료 날짜"
    )

# 날짜 유효성 검사
if start_date > end_date:
    st.sidebar.error("⚠️ 시작일이 종료일보다 늦습니다!")
    days = 0
else:
    days = (end_date - start_date).days
    st.sidebar.info(f"📊 수집 기간: **{days}일** ({start_date} ~ {end_date})")

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

# 사이드바: 캐시된 파일 드롭다운
st.sidebar.subheader("📁 지금까지 캐시된 파일")

history_items = list(reversed(st.session_state.crawl_history))
history_labels = ["선택하세요"]
history_map = {}

for item in history_items:
    label = f"{item['timestamp'].replace('_', ' ')} · {item['period']} · {item['total_items']}개"
    history_labels.append(label)
    history_map[label] = item

if 'selected_history_label' not in st.session_state or st.session_state.selected_history_label not in history_labels:
    st.session_state.selected_history_label = history_labels[0]

selected_history_label = st.sidebar.selectbox(
    "지금까지 캐시된 파일",
    options=history_labels,
    key="selected_history_label"
)
if selected_history_label == history_labels[0]:
    if not history_items:
        st.sidebar.caption("아직 캐시된 파일이 없습니다.")
else:
    selected_history = history_map[selected_history_label]
    st.sidebar.markdown(
        f"**수집 기간**: {selected_history['period']}  \
        **항목 수**: {selected_history['total_items']}개"
    )

    # selected_history['data']는 DataFrame으로 저장되어 있음
    df = selected_history['data']

    col_a, col_b = st.sidebar.columns(2)

    with col_a:
        try:
            excel_data = df_to_excel_bytes(df)
            st.download_button(
                label="📥 Excel",
                data=excel_data,
                file_name=f"산림청_입찰_{selected_history['timestamp']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"sidebar_excel_{selected_history['timestamp']}"
            )
        except Exception as e:
            st.error(f"Excel 생성 실패: {e}")

    with col_b:
        try:
            csv_data = df_to_csv_bytes(df)
            st.download_button(
                label="📥 CSV",
                data=csv_data,
                file_name=f"산림청_입찰_{selected_history['timestamp']}.csv",
                mime="text/csv",
                key=f"sidebar_csv_{selected_history['timestamp']}"
            )
        except Exception as e:
            st.error(f"CSV 생성 실패: {e}")

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
                    excel_data = df_to_excel_bytes(item['data'])
                    st.download_button(
                        label="📥 Excel",
                        data=excel_data,
                        file_name=f"산림청_입찰_{item['timestamp']}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"excel_{unique_key}"
                    )
                except Exception as e:
                    st.error(f"Excel 생성 실패: {e}")

            with col_b:
                # CSV 다운로드 (캐싱 사용)
                try:
                    csv = df_to_csv_bytes(item['data'])
                    st.download_button(
                        label="📥 CSV",
                        data=csv,
                        file_name=f"산림청_입찰_{item['timestamp']}.csv",
                        mime="text/csv",
                        key=f"csv_{unique_key}"
                    )
                except Exception as e:
                    st.error(f"CSV 생성 실패: {e}")

# 메인 영역
col1, col2 = st.columns([2, 1])

with col1:
    st.info(f"""
    📅 **수집 기간**: {start_date} ~ {end_date} (총 {days}일)
    ⏱️ **요청 딜레이**: {delay}초
    📄 **페이지 딜레이**: {page_delay}초
    🎯 **대상**: 산림청 입찰공고 게시판
    """)

with col2:
    st.metric("시작일", start_date.strftime('%Y-%m-%d'))
    st.metric("종료일", end_date.strftime('%Y-%m-%d'))

# 크롤링 실행 함수 (중복 제거)
def run_crawling(start_date, end_date, days, delay, page_delay):
    """크롤링 실행 및 결과 반환"""
    # 기간 정보 저장
    period_str = f"{start_date} ~ {end_date}"

    # 진행 상황 표시 영역
    progress_bar = st.progress(0)
    status_text = st.empty()
    info_text = st.empty()
    result_placeholder = st.empty()

    try:
        add_log(f"크롤링 시작 - 수집 기간: {period_str} ({days}일)")
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
            status_text.info(f"📄 페이지 {page_index} 처리 중...")
            info_text.info(f"🔍 페이지 {page_index} 항목 분석 중...")
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
                # 상단 고정 공지는 번호가 비거나 '공지' 표기로 나타나므로 건너뛴다.
                number_text = str(item.get('number', '')).strip()
                is_notice = not number_text or '공지' in number_text

                # 날짜 체크 (공지 제외)
                if item['post_date'] and item['post_date'] < crawler.cutoff_date and not is_notice:
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
                        info_text.text(f"✅ {page_index}페이지 {idx}/10 처리 완료: {item['title'][:30]}...")
                    else:
                        add_log(f"상세 페이지 가져오기 실패: {item['title'][:30]}...", "ERROR")
                        crawler.data.append(item)
                        crawler.total_items += 1
                        info_text.text(f"⚠️ 상세 페이지 실패: {item['title'][:30]}...")
                else:
                    crawler.data.append(item)
                    crawler.total_items += 1
                    info_text.text(f"ℹ️ 상세 페이지 링크 없음: {item['title'][:30]}...")

                # 진행률 업데이트
                progress = min(page_index / total_pages_estimate, 0.99)
                progress_bar.progress(progress)

            # 중간 결과 표시
            if crawler.data:
                df = pd.DataFrame(crawler.data)
                latest_rows = df.tail(20)

                preview_columns = [
                    ('number', '번호'),
                    ('title', '제목'),
                    ('forest_office', '담당산림청'),
                    ('department', '담당부서'),
                    ('manager', '담당자'),
                    ('contact', '연락처'),
                    ('post_date_str', '공고일자'),
                    ('views', '조회수'),
                    ('has_attachment', '첨부'),
                ]

                available_preview_cols = [col for col, _ in preview_columns if col in latest_rows.columns]
                preview_df = latest_rows[available_preview_cols].copy()
                rename_map = {col: label for col, label in preview_columns if col in preview_df.columns}
                preview_df = preview_df.rename(columns=rename_map)

                result_placeholder.dataframe(
                    preview_df,
                    use_container_width=True,
                    hide_index=True
                )

            if should_continue:
                page_index += 1
                time.sleep(crawler.page_delay)

            # 최대 페이지 제한 (무한 루프 방지) - 500페이지 = 5000개 항목
            if page_index > 500:
                add_log("최대 페이지 수(500) 도달 - 크롤링 종료", "WARNING")
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
                'period': period_str
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
    run_crawling(start_date, end_date, days, delay, page_delay)

# "크롤링 및 완료시 엑셀파일 작성" 버튼 기능
if export_data:
    # 초기화
    st.session_state.crawl_logs = []
    st.session_state.crawl_data = None
    st.session_state.crawl_completed = False

    # 크롤링 실행
    run_crawling(start_date, end_date, days, delay, page_delay)

# 크롤링 완료 후 다운로드 섹션 (두 버튼 모두에서 사용 가능)
if st.session_state.crawl_completed and st.session_state.crawl_data is not None:
    st.markdown("---")
    st.subheader("📥 데이터 다운로드")

    df = st.session_state.crawl_data
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    col1, col2 = st.columns(2)

    with col1:
        # 엑셀 다운로드
        try:
            excel_data = df_to_excel_bytes(df)

            st.download_button(
                label="📥 엑셀 파일 다운로드 (.xlsx)",
                data=excel_data,
                file_name=f"산림청_입찰정보_{timestamp.replace('-', '').replace('_', '')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"엑셀 생성 실패: {e}")

    with col2:
        # CSV 다운로드
        try:
            csv_data = df_to_csv_bytes(df)

            st.download_button(
                label="📥 CSV 파일 다운로드 (.csv)",
                data=csv_data,
                file_name=f"산림청_입찰정보_{timestamp.replace('-', '').replace('_', '')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"CSV 생성 실패: {e}")

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

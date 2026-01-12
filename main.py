import streamlit as st
import base64
from io import BytesIO
from PIL import Image
from pathlib import Path
import boto3

# =========================================================
# 1. 파일 지정
# =========================================================
BUCKET_NAME = "ivekorea-airflow-practice-taeeunk"

# =============================================================================
# 4. 앱 전체 설정
# =============================================================================
st.markdown(
    """
    <!-- 구글 폰트 불러오기 -->
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans&display=swap" rel="stylesheet">
    <style>
        /* 전체 앱 폰트 변경 */
        html, body, [class*="css"] {
            font-family: 'Noto Sans', sans-serif;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    /* 사이드바 실제 컨텐츠 영역 */
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(
            230deg,
            #FFFFFF 0%,
            #FFF1F2 50%,
            #E9353E 100%
        ) !important;

        border-right: 1px solid #E5E7EB;
    }

    /* 사이드바 글자 색 */
    section[data-testid="stSidebar"] * {
        color: #111827;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 기본 페이지 지정
st.set_page_config(
    page_title="광고 추천 시스템",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# 5. Session State 초기값 설정
# =============================================================================
if 'selected_industry' not in st.session_state:
    st.session_state['selected_industry'] = "금융/보험"
if 'selected_os' not in st.session_state:
    st.session_state['selected_os'] = "WEB"
if 'selected_limited' not in st.session_state:
    st.session_state['selected_limited'] = "UNLIMITED"


# =============================================================================
# 6. 페이지 정의 (st.Page)
# =============================================================================
home_page = st.Page(
    page="pages/home.py", 
    title="광고 데이터 정보",
    icon="📊",
    default=True
)

viz_page = st.Page(
    page="pages/TOP_3.py", 
    title="광고 추천 모델",
    icon="🔍"
)

info_page = st.Page(
    page="pages/information.py",
    title="대시보드 소개",
    icon="📋"
)


# =============================================================================
# 7. 네비게이션 구성
# =============================================================================
pg = st.navigation({
    "메인": [home_page, viz_page],
    "더보기": [info_page]
})


# =============================================================================
# 8. 공통 사이드바
# =============================================================================
with st.sidebar:
    st.header("🔍 광고 옵션 선택")

    st.selectbox(
        "산업군", 
        ["금융/보험", "커머스/유통","서비스", "게임", "교육/공공", "뷰티/헬스", "F&B/식품", "가전/제조"], 
        key='selected_industry'
    )
    
    st.selectbox(
        "OS 환경", 
        ["WEB", "ANDROID", "IOS"], 
        key='selected_os'
    )
    
    st.selectbox(
        "목표 제한 여부", 
        ["UNLIMITED", "LIMITED"], 
        key='selected_limited'
    )
    

# =============================================================================
# 9. 실행
# =============================================================================
pg.run()


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
OBJECT_KEY = "image/cursor_image.png"
# =========================================================
# 2. 이미지 처리 함수 (PNG 리사이징 및 Base64 변환)
# =========================================================
@st.cache_data
def get_s3_resized_png_b64(BUCKET_NAME, OBJECT_KEY, new_width):
    try:
        # 1. boto3 S3 클라이언트 생성
        s3 = boto3.client(
            's3',
            aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
            region_name=st.secrets.get("AWS_DEFAULT_REGION", "ap-southeast-2")
        )

        # 2. S3에서 객체(이미지) 가져오기
        response = s3.get_object(Bucket=BUCKET_NAME, Key=OBJECT_KEY)
        image_content = response['Body'].read()

        # 3. 이미지 열기 및 처리
        img = Image.open(BytesIO(image_content))
        img = img.convert("RGBA") # 투명 배경 지원

        # 4. 이미지 비율 유지하며 리사이징 계산
        w_percent = (new_width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        
        # 고품질 리사이징
        resized_img = img.resize((new_width, h_size), Image.Resampling.LANCZOS)
        
        # 5. 메모리 버퍼에 PNG 형식으로 저장
        buffer = BytesIO()
        resized_img.save(buffer, format="PNG")
        
        # 6. Base64로 인코딩해서 문자열로 반환
        return base64.b64encode(buffer.getvalue()).decode()

    except Exception as e:
        raise Exception(f"S3 이미지 처리 실패 (Key: {OBJECT_KEY}): {e}")

try:
    cursor_b64 = get_s3_resized_png_b64(BUCKET_NAME, OBJECT_KEY, 32)

    if cursor_b64:
        hotspot_x = 0
        hotspot_y = 0
        
        cursor_css_value = f'url("data:image/png;base64,{cursor_b64}") {hotspot_x} {hotspot_y}, auto !important'

        st.markdown(f"""
        <style>
        /* 전체 페이지 적용 */
        * {{
            cursor: {cursor_css_value};
        }}
        
        /* 사이드바 영역 강제 적용 */
        section[data-testid="stSidebar"] * {{
            cursor: {cursor_css_value};
        }}
        
        /* 버튼, 입력창 등 인터랙티브 요소 강제 적용 */
        button, select, input, textarea, label, a, div[data-testid="stMetricValue"] {{
            cursor: {cursor_css_value};
        }}
        </style>
        """, unsafe_allow_html=True)

except Exception as e:
    # 네트워크 에러 등을 잡기 위해 포괄적인 예외 처리
    st.error(f"🚨 커서 설정 중 오류 발생: {e}")


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


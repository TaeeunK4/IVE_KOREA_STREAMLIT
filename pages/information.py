# =============================================================================
# 대시보드 소개 페이지
# =============================================================================
import streamlit as st


# =============================================================================
# 1. CSS 설정
# =============================================================================
st.markdown("""
<style>
/* ==============================
   KPI 카드 스타일
============================== */
.kpi-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 18px 20px;
    width: 100%;
    box-shadow:
        0 4px 10px rgba(0,0,0,0.05),
        0 12px 28px rgba(0,0,0,0.08);
    border: 1px solid #E5E7EB;
}

.kpi-title {
    font-size: 22px;
    color: #6B7280;
    margin-bottom: 6px;
}

.kpi-value {
    font-size: 18px;
    font-weight: 650;
    color: #111827;
}

.kpi-sub {
    font-size: 12px;
    color: #9CA3AF;
    margin-top: 4px;
}

/* ==============================
   Info 카드 (페이지 소개용)
============================== */
.info-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 22px 24px;
    width: 100%;
    box-shadow:
        0 6px 16px rgba(0,0,0,0.08),
        0 12px 28px rgba(0,0,0,0.06);
    border: 1px solid #E5E7EB;
}

.info-db-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 22px 24px;
    width: 100%;
    box-shadow:
        0 6px 16px rgba(0,0,0,0.08),
        0 12px 28px rgba(0,0,0,0.06);
    border: 1px solid #E5E7EB;
    padding-bottom: 28px;
    padding-top: 28px;
}
                        
.info-title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 6px;
    color: #111827;
}

.info-desc {
    font-size: 14px;
    color: gray;
    margin-bottom: 10px;
}

.info-list {
    padding-left: 18px;
    margin: 0;
}

.info-list li {
    font-size: 14px;
    color: #374151;
    margin-bottom: 6px;
}
.info-list li.empty {
    height: 22px;  
    list-style: none;
}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 2. 제목 설정
# =============================================================================
st.markdown(
    """
    <h2 style="margin-top: -30px; margin-bottom: 10px;">📋 대시보드 소개</h2>
    """,
    unsafe_allow_html=True
)

st.divider()

st.text("") # 공백


# =============================================================================
# 3. 대시보드 소개
# =============================================================================
st.markdown("""
    <div class="info-db-card">
        <ul class="info-list">
            광고 성과 분석과 전략 수립을 체계화하기 위해 자체 데이터 분석 대시보드를 통해 캠페인을 운영합니다.</li>
            <br>
            <br>
            본 대시보드는 광고 데이터를 실시간으로 시각화 하고 성과 기반 분석을 통해 
            <br>
            최적의 광고 조합을 도출함으로써 클라이언트에게 적합한 <b>광고 형태를 지원</b>합니다.</li>
            <br>
        </ul>
    </div>
    """, unsafe_allow_html=True)



st.text("") #공백
st.text("") #공백
st.text("") #공백
st.text("") #공백
st.text("") #공백


# =============================================================================
# 4. 페이지 소개
# =============================================================================
st.markdown("""
<h3 style="margin-bottom: 12px;">📑 페이지 소개</h3>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

# 4.2 광고데이터 정보
with col1:
    st.markdown("""
    <div class="info-card">
        <div class="info-title">📊 광고 데이터 정보</div>
        <div class="info-desc">데이터 가공 및 성과 탐색</div>
        <ul class="info-list">
            <li>선택한 조건 데이터 정리</li>
            <li>주요 성과 지표 및 시각화 제공</li>
            <li class="empty"></li>
            <li class="empty"></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# 4.3 광고 추천 모델
with col2:
    st.markdown("""
    <div class="info-card">
        <div class="info-title">🔍 광고 추천 모델</div>
        <div class="info-desc">선택한 옵션을 기반으로 최적의 광고 형태 제공</div>
        <ul class="info-list">
            <li>자동 그룹 찾기</li>
            <li>그룹별 상위 광고 형태 보기</li>
            <li>TOP 3 광고 추천 제시</li>
            <li>예산 배분 안내</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

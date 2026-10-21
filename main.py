import datetime
import pandas as pd
import plotly.express as px
import pytz
import requests
import streamlit as st

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="박스오피스 대시보드",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. 고급 모던 다크 & 그라데이션 CSS (날짜 입력창 스타일 완전 보정)
st.markdown(
    """
    <style>
    /* 메인 앱 배경 (딥 다크 블루 그라데이션) */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        color: #f8fafc;
    }
    
    /* 사이드바 배경 그라데이션 및 테두리 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%) !important;
        border-right: 1px solid #334155;
    }
    
    /* 사이드바 내부 기본 텍스트 색상 (선명한 흰색/밝은 톤) */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        color: #f8fafc !important;
    }

    /* 날짜 입력창(Date Input) 박스 스타일 수정 (어두운 배경 + 명확한 흰색 글씨) */
    [data-testid="stSidebar"] div[data-baseweb="input"] {
        background-color: #334155 !important;
        border: 1px solid #475569 !important;
        border-radius: 10px !important;
    }
    
    [data-testid="stSidebar"] input {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 600 !important;
        background-color: transparent !important;
    }

    /* 날짜 선택 아이콘 색상 수정 */
    [data-testid="stSidebar"] svg {
        fill: #94a3b8 !important;
        color: #94a3b8 !important;
    }
    
    /* 사이드바 캡션(범례 내용) */
    [data-testid="stSidebar"] .stCaption {
        color: #cbd5e1 !important;
        font-size: 0.9rem !important;
    }

    /* 메인 타이틀 그라데이션 */
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 1.8rem;
    }

    /* 1위 영화 하이라이트 고급 그라데이션 카드 */
    .hero-card {
        background: linear-gradient(135deg, rgba(67, 56, 202, 0.4) 0%, rgba(147, 51, 234, 0.4) 100%);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(168, 85, 247, 0.4);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5);
    }
    .hero-badge {
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
        color: #000;
        font-weight: 800;
        font-size: 0.8rem;
        padding: 4px 12px;
        border-radius: 20px;
        display: inline-block;
        margin-bottom: 10px;
        letter-spacing: 0.5px;
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    }

    /* Streamlit Metric 커스텀 카드 */
    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(8px);
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 14px 18px;
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stMetricValue"] {
        color: #f8fafc !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }

    /* 구분선 라이트 처리 */
    hr {
        border-color: #334155 !important;
        margin: 1.5rem 0 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 3. API 키 검증
if "KOBIS_KEY" not in st.secrets:
    st.error(
        "🔑 **인증키 오류**: secrets에 `KOBIS_KEY`가 설정되지 않았습니다.\n\n"
        "**확인 사항:**\n"
        "1. `.streamlit/secrets.toml` 파일에 `KOBIS_KEY = '발급받은키'`를 등록했는지 확인하세요.\n"
        "2. Streamlit Cloud Settings의 Secrets 란에 키를 등록했는지 확인하세요."
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]

# 4. 사이드바 컨트롤러
seoul_tz = pytz.timezone("Asia/Seoul")
now_seoul = datetime.datetime.now(seoul_tz)
yesterday = (now_seoul - datetime.timedelta(days=1)).date()

with st.sidebar:
    st.markdown("## 🎬 **BOX OFFICE**")
    st.markdown("---")

    selected_date = st.date_input(
        "📅 조회 날짜 선택",
        value=yesterday,
        max_value=yesterday,
        help="오늘 날짜 데이터는 아직 집계 중이므로 어제 날짜까지 선택 가능합니다.",
    )

    st.markdown("---")
    st.markdown("### 📌 **범례 안내**")
    st.caption("• 🏆 : 누적 관객수 100만 명 돌파")
    st.caption("• 🔺 : 전일 대비 순위 상승")
    st.caption("• 🔹 : 전일 대비 순위 하강")

target_dt = selected_date.strftime("%Y%m%d")
formatted_date = selected_date.strftime("%Y년 %m월 %d일")

# 5. 메인 헤더
st.markdown(
    f'<div class="main-title">{selected_date.strftime("%Y.%m.%d")} 일별 박스오피스</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="sub-title">영화진흥위원회(KOBIS) 공식 집계 데이터 기준 ({formatted_date})</div>',
    unsafe_allow_html=True,
)

# 6. KOBIS API 데이터 요청
url = (
    "http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    f"?key={api_key}&targetDt={target_dt}"
)

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException:
    st.error("📡 **네트워크 요청 실패**: KOBIS 서버와 통신할 수 없습니다.")
    st.stop()

# 7. 응답 예외 처리
if "faultInfo" in data:
    fault_msg = data["faultInfo"].get("message", "알 수 없는 오류가 발생했습니다.")
    st.error(f"⚠️ **KOBIS API 오류**: {fault_msg}")
    st.stop()

box_office_result = data.get("boxOfficeResult", {})
daily_list = box_office_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.info("ℹ️ **그날은 아직 집계 전입니다.**")
    st.stop()

# 8. 데이터 가공
df = pd.DataFrame(daily_list)

numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt", "showCnt"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")


def format_rank_change(row):
    if row.get("rankOldAndNew") == "NEW":
        return "NEW"
    change = row["rankInten"]
    if change > 0:
        return f"🔺 {abs(change)}"
    elif change < 0:
        return f"🔹 {abs(change)}"
    else:
        return "-"


df["rankChange"] = df.apply(format_rank_change, axis=1)

df["display_movieNm"] = df.apply(
    lambda x: f"🏆 {x['movieNm']}" if x["audiAcc"] >= 1000000 else x["movieNm"],
    axis=1,
)

# 9. 1위 영화 하이라이트 배너 (Hero Section)
top_1 = df.iloc[0]

st.markdown(
    f"""
    <div class="hero-card">
        <div class="hero-badge">DAILY NO.1</div>
        <div class="hero-title">{top_1['display_movieNm']}</div>
    </div>
""",
    unsafe_allow_html=True,
)

m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    st.metric(label="당일 관객수", value=f"{top_1['audiCnt']:,} 명")
with m_col2:
    st.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")
with m_col3:
    st.metric(label="스크린 수", value=f"{top_1['scrnCnt']:,} 개")

st.markdown("---")

# 10. 차트 및 데이터 표 (2열 레이아웃)
col_chart, col_table = st.columns([1, 1], gap="large")

with col_chart:
    st.markdown("### 📊 **관객수 TOP 5**")

    top_5_df = df.head(5).sort_values(by="audiCnt", ascending=True)

    # Plotly 세련된 화려한 그라데이션 가로 막대그래프
    fig = px.bar(
        top_5_df,
        x="audiCnt",
        y="movieNm",
        orientation="h",
        text_auto=",.0f",
        labels={"audiCnt": "관객수", "movieNm": ""},
        color="audiCnt",
        color_continuous_scale=["#38bdf8", "#a855f7", "#ec4899"],
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>관객수: %{x:,}명<extra></extra>",
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True,
            gridcolor="#334155",
            title="",
            tickfont=dict(color="#94a3b8"),
        ),
        yaxis=dict(showgrid=False, tickfont=dict(color="#f8fafc", size=13)),
        coloraxis_showscale=False,
        margin=dict(l=0, r=45, t=10, b=0),
        height=350,
    )

    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("### 📋 **박스오피스 전체 순위**")

    display_df = df[
        [
            "rank",
            "rankChange",
            "display_movieNm",
            "openDt",
            "audiCnt",
            "audiAcc",
            "scrnCnt",
        ]
    ].copy()
    display_df.columns = [
        "순위",
        "변동",
        "영화명",
        "개봉일",
        "관객수",
        "누적관객",
        "스크린수",
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=350,
        column_config={
            "순위": st.column_config.NumberColumn(width="small"),
            "변동": st.column_config.TextColumn(width="small"),
            "관객수": st.column_config.NumberColumn(format="%d 명"),
            "누적관객": st.column_config.NumberColumn(format="%d 명"),
            "스크린수": st.column_config.NumberColumn(format="%d 개"),
        },
    )

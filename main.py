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

# 2. 다크 & 세련된 CSS (탭 메뉴 및 글자 시인성 완벽 고정)
st.markdown(
    """
    <style>
    /* 전체 배경 */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* 🔥 탭(Tabs) 글자 시인성 완벽 해결 🔥 */
    /* 비선택 탭 글자색 (밝은 회색) */
    button[data-baseweb="tab"] p,
    button[data-baseweb="tab"] span,
    div[data-baseweb="tab"] p,
    div[data-baseweb="tab"] span {
        color: #cbd5e1 !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
    }
    
    /* 선택된 탭 글자색 (밝은 하늘색) */
    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] span,
    div[data-baseweb="tab"][aria-selected="true"] p,
    div[data-baseweb="tab"][aria-selected="true"] span {
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }

    /* 사이드바 기본 텍스트 */
    [data-testid="stSidebar"] *,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: #f8fafc !important;
    }
    
    /* 메인 타이틀 그라데이션 */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #cbd5e1;
        margin-bottom: 1.5rem;
    }

    /* 1위 영화 배너 카드 */
    .hero-card {
        background: linear-gradient(135deg, rgba(67, 56, 202, 0.6) 0%, rgba(147, 51, 234, 0.6) 100%);
        border: 1px solid rgba(168, 85, 247, 0.5);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 20px;
    }
    .hero-badge {
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
        color: #000000;
        font-weight: 800;
        font-size: 0.75rem;
        padding: 3px 10px;
        border-radius: 12px;
        display: inline-block;
        margin-bottom: 8px;
    }
    .hero-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #ffffff;
    }

    /* Metric 수치 카드 글자색 */
    [data-testid="stMetric"] {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 14px !important;
        padding: 14px 18px !important;
    }
    [data-testid="stMetricLabel"] p {
        color: #cbd5e1 !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] div {
        color: #38bdf8 !important;
        font-size: 1.7rem !important;
        font-weight: 800 !important;
    }

    /* 영화 프로필 카드 */
    .profile-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
    }
    .profile-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #38bdf8;
        margin-bottom: 10px;
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
    st.title("🎬 BOX OFFICE")
    st.divider()

    selected_date = st.date_input(
        "📅 조회 날짜 선택",
        value=yesterday,
        max_value=yesterday,
        help="오늘 날짜 데이터는 아직 집계 중이므로 어제 날짜까지 선택 가능합니다.",
    )

    st.divider()
    st.subheader("📌 범례 안내")
    st.markdown("• **🏆** : 누적 관객수 100만 명 돌파")
    st.markdown("• **🔺** : 전일 대비 순위 상승")
    st.markdown("• **🔹** : 전일 대비 순위 하강")

target_dt = selected_date.strftime("%Y%m%d")
formatted_date = selected_date.strftime("%Y년 %m월 %d일")

# 5. KOBIS API 데이터 요청
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

# 6. 응답 예외 처리
if "faultInfo" in data:
    fault_msg = data["faultInfo"].get("message", "알 수 없는 오류가 발생했습니다.")
    st.error(f"⚠️ **KOBIS API 오류**: {fault_msg}")
    st.stop()

box_office_result = data.get("boxOfficeResult", {})
daily_list = box_office_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.info("ℹ️ **그날은 아직 집계 전입니다.**")
    st.stop()

# 7. 데이터 가공
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

# 8. 메인 헤더 표시
st.markdown(
    f'<div class="main-title">{selected_date.strftime("%Y.%m.%d")} 일별 박스오피스</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="sub-title">영화진흥위원회(KOBIS) 공식 집계 데이터 기준 ({formatted_date})</div>',
    unsafe_allow_html=True,
)

# 9. 탭 메뉴
tab1, tab2 = st.tabs(["📊 메인 대시보드", "🏆 100만 관객 돌파 영화 목록"])

with tab1:
    # 1위 영화 하이라이트
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

    st.divider()

    # 차트 및 표
    col_chart, col_table = st.columns([1, 1], gap="large")

    with col_chart:
        st.markdown("### 📊 **관객수 TOP 5**")
        top_5_df = df.head(5).sort_values(by="audiCnt", ascending=True)

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

with tab2:
    st.markdown("### 🏆 **누적 관객수 100만 명 돌파 영화 프로필**")

    million_df = df[df["audiAcc"] >= 1000000]

    if million_df.empty:
        st.info("해당 날짜 박스오피스 TOP 10 내에 누적 관객 100만 명을 돌파한 영화가 없습니다.")
    else:
        for idx, row in million_df.iterrows():
            st.markdown(
                f"""
                <div class="profile-card">
                    <div class="profile-title">🏆 {row['rank']}위 : {row['movieNm']}</div>
                    <p style="margin-bottom: 4px; color: #f8fafc;"><b>📅 개봉일:</b> {row['openDt']}</p>
                    <p style="margin-bottom: 4px; color: #f8fafc;"><b>🎟️ 누적 관객수:</b> {row['audiAcc']:,} 명</p>
                    <p style="margin-bottom: 4px; color: #f8fafc;"><b>👥 당일 관객수:</b> {row['audiCnt']:,} 명</p>
                    <p style="margin-bottom: 0px; color: #f8fafc;"><b>🖥️ 상영 스크린수:</b> {row['scrnCnt']:,} 개</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

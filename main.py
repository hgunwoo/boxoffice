import datetime
import pandas as pd
import plotly.express as px
import pytz
import requests
import streamlit as st

# 1. 페이지 기본 설정 및 모던 웹 스타일링 (CSS)
st.set_page_config(
    page_title="박스오피스 대시보드",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 심플하고 세련된 UI 스타일을 위한 Custom CSS
st.markdown(
    """
    <style>
    /* 메인 배경 및 패딩 정리 */
    .main {
        background-color: #f8f9fa;
    }
    
    /* 헤더 타이틀 스타일 */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    
    /* Metric 카드 디자인 개선 */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #1f2937 !important;
    }
    
    /* 세퍼레이터 라이트 스타일 */
    hr {
        margin: 2rem 0 !important;
        border-top: 1px solid #e5e7eb !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 2. API 키 검증
if "KOBIS_KEY" not in st.secrets:
    st.error(
        "🔑 **인증키 오류**: secrets에 `KOBIS_KEY`가 설정되지 않았습니다.\n\n"
        "**확인 사항:**\n"
        "1. `.streamlit/secrets.toml` 파일에 `KOBIS_KEY = '발급받은키'`를 등록했는지 확인하세요.\n"
        "2. Streamlit Cloud Settings의 Secrets 란에 키를 등록했는지 확인하세요."
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]

# 3. 사이드바 컨트롤러 (날짜 선택기 및 서비스 안내)
seoul_tz = pytz.timezone("Asia/Seoul")
now_seoul = datetime.datetime.now(seoul_tz)
yesterday = (now_seoul - datetime.timedelta(days=1)).date()

with st.sidebar:
    st.title("🎬 BoxOffice")
    st.markdown("---")

    selected_date = st.date_input(
        "📅 조회 날짜 선택",
        value=yesterday,
        max_value=yesterday,
        help="오늘 날짜 데이터는 아직 집계 중이므로 어제 날짜까지 선택 가능합니다.",
    )

    st.markdown("---")
    st.caption("💡 **Tip**")
    st.caption("• 🏆 : 누적 관객수 100만 명 돌파 영화")
    st.caption("• 🔺 / 🔹 : 전일 대비 순위 변동")

target_dt = selected_date.strftime("%Y%m%d")
formatted_date = selected_date.strftime("%Y년 %m월 %d일")

# 4. 메인 타이틀 영역
st.markdown(
    f'<div class="main-header">{selected_date.strftime("%Y.%m.%d")} 일별 박스오피스</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="sub-header">영화진흥위원회(KOBIS) 공식 집계 데이터 기준 ({formatted_date})</div>',
    unsafe_allow_html=True,
)

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
    st.error(
        "📡 **네트워크 요청 실패**: KOBIS 서버와 통신할 수 없습니다.\n\n"
        "잠시 후 다시 시도해 주거나 인터넷 연결을 확인하세요."
    )
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

# 7. 데이터 정제 및 가공
df = pd.DataFrame(daily_list)

numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt", "showCnt"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")


# 순위 증감 레이블 생성 함수
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

# 100만 관객 돌파 시 트로피 아이콘 추가
df["display_movieNm"] = df.apply(
    lambda x: f"🏆 {x['movieNm']}" if x["audiAcc"] >= 1000000 else x["movieNm"],
    axis=1,
)

# 8. 상단 1위 영화 하이라이트 (KPI Metrics)
top_1 = df.iloc[0]

st.markdown(f"### 🥇 1위 영화 · **{top_1['display_movieNm']}**")

m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    st.metric(label="당일 관객수", value=f"{top_1['audiCnt']:,} 명")
with m_col2:
    st.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")
with m_col3:
    st.metric(label="스크린 수", value=f"{top_1['scrnCnt']:,} 개")

st.markdown("---")

# 9. 세련된 Plotly 가로 막대그래프 (TOP 5)
col_chart, col_table = st.columns([1, 1], gap="large")

with col_chart:
    st.markdown("### 📊 관객수 TOP 5")

    top_5_df = df.head(5).sort_values(by="audiCnt", ascending=True)

    # Plotly 커스텀 막대그래프
    fig = px.bar(
        top_5_df,
        x="audiCnt",
        y="movieNm",
        orientation="h",
        text_auto=",.0f",
        labels={"audiCnt": "관객수", "movieNm": ""},
    )

    fig.update_traces(
        marker_color="#3B82F6",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="#f3f4f6", title=""),
        yaxis=dict(showgrid=False),
        margin=dict(l=0, r=40, t=10, b=0),
        height=320,
    )

    st.plotly_chart(fig, use_container_width=True)

# 10. 전체 박스오피스 데이터 테이블
with col_table:
    st.markdown("### 📋 박스오피스 순위표")

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
        height=320,
        column_config={
            "순위": st.column_config.NumberColumn(width="small"),
            "변동": st.column_config.TextColumn(width="small"),
            "관객수": st.column_config.NumberColumn(format="%d 명"),
            "누적관객": st.column_config.NumberColumn(format="%d 명"),
            "스크린수": st.column_config.NumberColumn(format="%d 개"),
        },
    )

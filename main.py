import datetime
import pandas as pd
import pytz
import requests
import streamlit as st

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="일별 박스오피스 순위",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. 어두운 그라데이션 배경 및 글씨 대조 CSS 설정
st.markdown(
    """
    <style>
    /* 전체 메인 배경 (어두운 블루-퍼플 그라데이션) */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%) !important;
        color: #ffffff !important;
    }

    /* 사이드바 어두운 배경 및 테두리 */
    [data-testid="stSidebar"] {
        background: #0f172a !important;
        border-right: 1px solid #334155 !important;
    }

    /* 모든 텍스트 및 라벨 흰색으로 대조 강제 처리 */
    html, body, [class*="css"], .stMarkdown, p, span, label, h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }

    /* 탭(Tabs) 글자 시인성 강화 */
    button[data-baseweb="tab"] p {
        color: #cbd5e1 !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #38bdf8 !important;
        font-size: 1.05rem !important;
        font-weight: 800 !important;
    }

    /* 1위 영화 하이라이트 배너 카드 */
    .hero-card {
        background: linear-gradient(135deg, rgba(67, 56, 202, 0.7) 0%, rgba(147, 51, 234, 0.7) 100%);
        border: 1px solid #818cf8;
        border-radius: 16px;
        padding: 24px;
        height: 100%;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
    }
    .hero-badge {
        background-color: #f59e0b;
        color: #000000 !important;
        font-weight: 800;
        font-size: 0.8rem;
        padding: 4px 10px;
        border-radius: 12px;
        display: inline-block;
        margin-bottom: 10px;
    }
    .hero-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #ffffff !important;
        margin-bottom: 12px;
    }

    /* 영화 프로필 카드 (어두운 카드 + 밝은 글씨 대조) */
    .profile-card {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid #475569;
        border-radius: 16px;
        padding: 24px;
        height: 100%;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    }
    .profile-header {
        font-size: 1.3rem;
        font-weight: 800;
        color: #38bdf8 !important;
        margin-bottom: 14px;
        border-bottom: 1px solid #475569;
        padding-bottom: 8px;
    }
    .profile-item {
        font-size: 0.98rem;
        color: #f8fafc !important;
        margin-bottom: 8px;
    }

    /* Metric 수치 카드 보정 */
    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid #475569 !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
    }
    [data-testid="stMetricLabel"] p {
        color: #cbd5e1 !important;
    }
    [data-testid="stMetricValue"] div {
        color: #38bdf8 !important;
        font-weight: 800 !important;
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

# 4. 사이드바 날짜 선택 기능
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

# 5. KOBIS 일별 박스오피스 API 데이터 요청
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
    st.error(f"⚠️ **KOBIS API 오류 발생**: {fault_msg}")
    st.stop()

# 7. 데이터 추출 및 가공
box_office_result = data.get("boxOfficeResult", {})
daily_list = box_office_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning("ℹ️ **그날은 아직 집계 전입니다.**")
    st.stop()

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

# 8. 영화 상세정보(장르, 감독, 상영시간 등) 조회 함수 (KOBIS 상세 API)
def get_movie_detail(movie_cd):
    detail_url = (
        "http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json"
        f"?key={api_key}&movieCd={movie_cd}"
    )
    try:
        res = requests.get(detail_url, timeout=5)
        res_data = res.json()
        movie_info = res_data.get("movieInfoResult", {}).get("movieInfo", {})

        genres = ", ".join(
            [g.get("genreNm") for g in movie_info.get("genres", [])]
        )
        directors = ", ".join(
            [d.get("peopleNm") for d in movie_info.get("directors", [])]
        )
        show_tm = movie_info.get("showTm", "")
        nation = (
            movie_info.get("nations", [{}])[0].get("nationNm", "")
            if movie_info.get("nations")
            else ""
        )

        return {
            "genre": genres if genres else "정보 없음",
            "director": directors if directors else "정보 없음",
            "showTm": f"{show_tm}분" if show_tm else "정보 없음",
            "nation": nation if nation else "정보 없음",
        }
    except Exception:
        return {
            "genre": "정보 없음",
            "director": "정보 없음",
            "showTm": "정보 없음",
            "nation": "정보 없음",
        }


# 9. 메인 헤더
st.markdown(
    f"<h1 style='font-size: 2.2rem; font-weight: 800; color: #38bdf8 !important;'>{selected_date.strftime('%Y.%m.%d')} 일별 박스오피스</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<p style='color: #cbd5e1 !important; margin-bottom: 20px;'>영화진흥위원회(KOBIS) 공식 집계 데이터 기준 ({formatted_date})</p>",
    unsafe_allow_html=True,
)

# 10. 탭 메뉴 구성
tab1, tab2 = st.tabs(["📊 메인 대시보드", "🏆 100만 관객 돌파 영화 목록"])

with tab1:
    top_1 = df.iloc[0]
    top_1_detail = get_movie_detail(top_1["movieCd"])

    # 1위 영화 하이라이트 & 상세 프로필(영화 설명 포함) 좌우 배치
    col_hero, col_profile = st.columns([1.2, 1], gap="medium")

    with col_hero:
        st.markdown(
            f"""
            <div class="hero-card">
                <div class="hero-badge">DAILY NO.1</div>
                <div class="hero-title">{top_1['display_movieNm']}</div>
                <p style="color: #e2e8f0 !important; margin-bottom: 8px;"><b>개봉일:</b> {top_1['openDt']}</p>
                <p style="color: #e2e8f0 !important; margin-bottom: 8px;"><b>장르/국가:</b> {top_1_detail['genre']} ({top_1_detail['nation']})</p>
                <p style="color: #e2e8f0 !important; margin-bottom: 0px;"><b>러닝타임:</b> {top_1_detail['showTm']}</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with col_profile:
        st.markdown(
            f"""
            <div class="profile-card">
                <div class="profile-header">🎬 1위 영화 상세 개요</div>
                <div class="profile-item"><b>📌 영화명:</b> {top_1['movieNm']}</div>
                <div class="profile-item"><b>🎬 감독:</b> {top_1_detail['director']}</div>
                <div class="profile-item"><b>🎟️ 누적 관객수:</b> {top_1['audiAcc']:,} 명</div>
                <div class="profile-item"><b>👥 당일 관객수:</b> {top_1['audiCnt']:,} 명</div>
                <div class="profile-item"><b>🖥️ 상영 스크린수:</b> {top_1['scrnCnt']:,} 개</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.write("")
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric(label="당일 관객수", value=f"{top_1['audiCnt']:,} 명")
    with m_col2:
        st.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")
    with m_col3:
        st.metric(label="상영 스크린수", value=f"{top_1['scrnCnt']:,} 개")

    st.divider()

    # 상위 5개 영화 막대그래프 & 전체 순위 표
    col_chart, col_table = st.columns([1, 1], gap="large")

    with col_chart:
        st.markdown("### 📊 관객수 상위 5개 영화")
        top_5_df = df.head(5)[["movieNm", "audiCnt"]].copy()
        top_5_df.columns = ["영화명", "관객수"]
        top_5_df = top_5_df.set_index("영화명")
        st.bar_chart(top_5_df)

    with col_table:
        st.markdown("### 📋 박스오피스 전체 순위")
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
            "순위증감",
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
            column_config={
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
            m_detail = get_movie_detail(row["movieCd"])
            st.markdown(
                f"""
                <div class="profile-card" style="margin-bottom: 12px;">
                    <div class="profile-header">🏆 {row['rank']}위 : {row['movieNm']}</div>
                    <div class="profile-item"><b>📅 개봉일:</b> {row['openDt']} | <b>장르:</b> {m_detail['genre']} | <b>감독:</b> {m_detail['director']}</div>
                    <div class="profile-item"><b>🎟️ 누적 관객수:</b> {row['audiAcc']:,} 명</div>
                    <div class="profile-item"><b>👥 당일 관객수:</b> {row['audiCnt']:,} 명</div>
                    <div class="profile-item"><b>🖥️ 상영 스크린수:</b> {row['scrnCnt']:,} 개</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

import datetime
import pandas as pd
import pytz
import requests
import streamlit as st

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="일별 박스오피스 순위 조회",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 일별 박스오피스 순위")

# 2. API 키 불러오기 (streamlit secrets 이용)
if "KOBIS_KEY" not in st.secrets:
    st.error(
        "🔑 **인증키 오류**: secrets에 `KOBIS_KEY`가 설정되지 않았습니다.\n\n"
        "**확인 사항:**\n"
        "1. `.streamlit/secrets.toml` 파일에 `KOBIS_KEY = '발급받은키'`를 등록했는지 확인하세요.\n"
        "2. Streamlit Cloud Settings의 Secrets 란에 키를 등록했는지 확인하세요."
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]

# 3. 사이드바 날짜 선택 기능
seoul_tz = pytz.timezone("Asia/Seoul")
now_seoul = datetime.datetime.now(seoul_tz)
yesterday = (now_seoul - datetime.timedelta(days=1)).date()

with st.sidebar:
    st.header("🎬 BOX OFFICE")
    st.divider()

    selected_date = st.date_input(
        "📅 조회 날짜 선택",
        value=yesterday,
        max_value=yesterday,
        help="오늘 날짜 데이터는 아직 집계 중이므로 어제 날짜까지 선택 가능합니다.",
    )

    st.divider()
    st.subheader("📌 범례 안내")
    st.write("• **🏆** : 누적 관객수 100만 명 돌파")
    st.write("• **🔺** : 전일 대비 순위 상승")
    st.write("• **🔹** : 전일 대비 순위 하강")

target_dt = selected_date.strftime("%Y%m%d")
formatted_date = selected_date.strftime("%Y년 %m월 %d일")

st.caption(f"기준 일자: {formatted_date} (한국 시간)")

# 4. KOBIS API 데이터 요청
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
        "**확인 사항:**\n"
        "1. 인터넷 연결 상태를 확인하세요.\n"
        "2. KOBIS API 서버 점검 여부를 확인하세요."
    )
    st.stop()

# 5. 응답 예외 처리
if "faultInfo" in data:
    fault_msg = data["faultInfo"].get("message", "알 수 없는 오류가 발생했습니다.")
    st.error(
        f"⚠️ **KOBIS API 오류 발생**: {fault_msg}\n\n"
        "**확인 사항:**\n"
        "1. secrets에 입력한 `KOBIS_KEY` 값이 정확한지 확인하세요.\n"
        "2. KOBIS 개발자센터에서 일일 요청 한도가 초과되지 않았는지 확인하세요."
    )
    st.stop()

# 6. 영화 목록 데이터 추출
box_office_result = data.get("boxOfficeResult", {})
daily_list = box_office_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning("ℹ️ **그날은 아직 집계 전입니다.**")
    st.stop()

# 7. 데이터프레임 변환 및 가공
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

# 누적 관객수 100만 이상 트로피 표시
df["display_movieNm"] = df.apply(
    lambda x: f"🏆 {x['movieNm']}" if x["audiAcc"] >= 1000000 else x["movieNm"],
    axis=1,
)

# 8. 탭 메뉴 구성
tab1, tab2 = st.tabs(["📊 메인 대시보드", "🏆 100만 관객 돌파 영화 목록"])

with tab1:
    # 1위 영화 지표 카드 표시
    top_1 = df.iloc[0]

    st.subheader(f"🥇 1위 영화: {top_1['display_movieNm']}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="당일 관객수", value=f"{top_1['audiCnt']:,} 명")
    with col2:
        st.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")
    with col3:
        st.metric(label="상영 스크린수", value=f"{top_1['scrnCnt']:,} 개")

    st.divider()

    # 상위 5개 영화 막대그래프
    st.subheader("📊 관객수 상위 5개 영화")
    top_5_df = df.head(5)[["movieNm", "audiCnt"]].copy()
    top_5_df.columns = ["영화명", "관객수"]
    top_5_df = top_5_df.set_index("영화명")

    st.bar_chart(top_5_df)

    st.divider()

    # 전체 순위 표
    st.subheader("📋 박스오피스 전체 순위")

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
    st.subheader("🏆 누적 관객수 100만 명 돌파 영화 프로필")

    million_df = df[df["audiAcc"] >= 1000000]

    if million_df.empty:
        st.info("해당 날짜 박스오피스 TOP 10 내에 누적 관객 100만 명을 돌파한 영화가 없습니다.")
    else:
        for idx, row in million_df.iterrows():
            with st.expander(f"🏆 {row['rank']}위 : {row['movieNm']}", expanded=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"📅 **개봉일**: {row['openDt']}")
                    st.write(f"🎟️ **누적 관객수**: {row['audiAcc']:,} 명")
                with col_b:
                    st.write(f"👥 **당일 관객수**: {row['audiCnt']:,} 명")
                    st.write(f"🖥️ **상영 스크린수**: {row['scrnCnt']:,} 개")

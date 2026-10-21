import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# 페이지 기본 설정 (타이틀, 레이아웃)
st.set_page_config(page_title="어제 박스오피스 순위", layout="wide")

st.title("🎬 어제 일별 박스오피스 순위")

# 1. API 키 불러오기 (streamlit secrets 이용)
# .streamlit/secrets.toml 파일 또는 Streamlit Cloud Secrets에 KOBIS_KEY 저장 필수
if "KOBIS_KEY" not in st.secrets:
    st.error(
        "🔑 **인증키 오류**: secrets에 `KOBIS_KEY`가 설정되지 않았습니다.\n\n"
        "**확인 사항:**\n"
        "1. `.streamlit/secrets.toml` 파일에 `KOBIS_KEY = '발급받은키'`를 등록했는지 확인하세요.\n"
        "2. Streamlit Cloud Advanced Settings의 Secrets 란에 키를 등록했는지 확인하세요."
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]

# 2. 한국 시간(Asia/Seoul) 기준 '어제' 날짜 계산
seoul_tz = pytz.timezone("Asia/Seoul")
now_seoul = datetime.datetime.now(seoul_tz)
yesterday = now_seoul - datetime.timedelta(days=1)
target_dt = yesterday.strftime("%Y%m%d")  # YYYYMMDD 포맷
formatted_date = yesterday.strftime("%Y년 %m월 %d일")

st.caption(f"📅 기준 일자: {formatted_date} (한국 시간)")

# 3. KOBIS API 요청 주소 생성 및 호출
url = (
    f"http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    f"?key={api_key}&targetDt={target_dt}"
)

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()  # HTTP 상태 코드 4xx, 5xx 에러 예외 발생
    data = response.json()
except requests.exceptions.RequestException as e:
    st.error(
        "📡 **네트워크 요청 실패**: KOBIS 서버와 통신할 수 없습니다.\n\n"
        "**확인 사항:**\n"
        "1. 인터넷 연결 상태를 확인하세요.\n"
        "2. KOBIS API 서버 점검 여부를 확인하세요."
    )
    st.stop()

# 4. 응답 예외 처리 (오류 응답 확인)
if "faultInfo" in data:
    fault_msg = data["faultInfo"].get("message", "알 수 없는 오류가 발생했습니다.")
    st.error(
        f"⚠️ **KOBIS API 오류 발생**: {fault_msg}\n\n"
        "**확인 사항:**\n"
        "1. secrets에 입력한 `KOBIS_KEY` 값이 정확한지 확인하세요.\n"
        "2. KOBIS 개발자센터에서 일일 요청 한도가 초과되지 않았는지 확인하세요."
    )
    st.stop()

# 5. 영화 목록 데이터 추출
box_office_result = data.get("boxOfficeResult", {})
daily_list = box_office_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.warning(
        "ℹ️ **데이터 없음**: 어제 박스오피스 목록이 비어 있습니다.\n\n"
        "**확인 사항:**\n"
        "1. 아직 집계가 완료되지 않았을 수 있습니다. 잠시 후 다시 시도해 주세요.\n"
        "2. 해당 날짜에 집계된 영화 데이터가 존재하는지 KOBIS 웹사이트에서 확인하세요."
    )
    st.stop()

# 6. 데이터프레임 변환 및 숫자형 변환 (문자열 -> 숫자)
df = pd.DataFrame(daily_list)

numeric_cols = ["rank", "audiCnt", "audiAcc", "scrnCnt", "showCnt"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 7. 1위 영화 지표 카드(Metric) 표시
top_1 = df.iloc[0]

st.subheader(f"🏆 1위 영화: {top_1['movieNm']}")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="어제 관객수", value=f"{top_1['audiCnt']:,} 명")
with col2:
    st.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")
with col3:
    st.metric(label="상영 스크린수", value=f"{top_1['scrnCnt']:,} 개")

st.divider()

# 8. 관객수 상위 5편 막대그래프
st.subheader("📊 관객수 상위 5개 영화")
top_5_df = df.head(5)[["movieNm", "audiCnt"]].copy()

# 시각화를 위해 컬럼명 변경
top_5_df.columns = ["영화명", "관객수"]
top_5_df = top_5_df.set_index("영화명")

st.bar_chart(top_5_df)

st.divider()

# 9. 전체 순위 표 표시
st.subheader("📋 어제 박스오피스 전체 순위")

# 화면에 보여 줄 컬럼 선택 및 이름 변경
display_df = df[["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
display_df.columns = ["순위", "영화명", "개봉일", "관객수", "누적관객", "스크린수"]

# 천 단위 쉼표 포맷팅을 적용한 표 출력
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

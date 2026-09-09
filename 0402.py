# C:\Users\user\VibeCode\common\raw_trade_data.csv 파일 활용
# 필터규칙: 
# 1) HS 코드가 85로 시작하는 물품 (반도체류)
# 2) 국가명 미국 또는 베트남
# 3) 수출금액이 0보다 큰 수 (실제 수출실력이 있는 행)
# 위와 같은 조건으로 필터링 한 뒤, 수출금액 상위 10행의 값을 화면에 보여주고 report2.csv로 저장.
# streamlit 사용, 실행코드 streamlit run 0402.py

import os
import pandas as pd
import streamlit as st

# Streamlit 페이지 설정
st.set_page_config(page_title="반도체 수출 데이터 분석", layout="wide")
st.title("반도체 수출 데이터 분석 (미국/베트남)")

# 1. 파일 경로 설정
current_dir = os.path.dirname(__file__)
csv_path = os.path.abspath(os.path.join(current_dir, "raw_trade_data.csv"))
report_path = os.path.join(current_dir, "report2.csv")

st.markdown(f"**원본 데이터 경로:** `{csv_path}`")

# 2. 데이터 로드 함수
@st.cache_data
def load_data(file_path):
    """안정적으로 인코딩을 처리하여 CSV를 로드합니다."""
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return pd.read_csv(file_path)

if not os.path.exists(csv_path):
    st.error(f"원본 데이터 파일을 찾을 수 없습니다: {csv_path}")
    st.stop()

try:
    df = load_data(csv_path)
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 3. 데이터 전처리 및 필터링
# 복사본을 생성하고 안전하게 타입 캐스팅 및 정제 수행
df_clean = df.copy()
df_clean["hs_code"] = df_clean["hs_code"].astype("string").str.replace(r"\.0$", "", regex=True)
df_clean["수출금액"] = pd.to_numeric(df_clean["수출금액"], errors="coerce")

# 조건 정의
# Condition 1: HS 코드가 85로 시작하는 물품 (반도체류)
cond_hs = df_clean["hs_code"].str.startswith("85", na=False)

# Condition 2: 국가명 미국 또는 베트남
cond_country = df_clean["국가명"].isin(["미국", "베트남"])

# Condition 3: 수출금액이 0보다 큰 수 (실제 수출실력이 있는 행)
cond_amount = df_clean["수출금액"] > 0

# 최종 필터 적용
filtered_df = df_clean[cond_hs & cond_country & cond_amount]

# 4. 수출금액 상위 10행 정렬 및 추출
top_10 = filtered_df.sort_values(by="수출금액", ascending=False).head(10)

# 5. 리포트 파일(report2.csv)로 자동 저장
try:
    top_10.to_csv(report_path, index=False, encoding="utf-8-sig")
    st.success(f"데이터 필터링 완료! 수출금액 상위 10행의 데이터가 `{report_path}` 파일에 성공적으로 저장되었습니다.")
except Exception as e:
    st.warning(f"리포트 파일을 저장하는 도중 오류가 발생했습니다: {e}")

# 6. 화면 출력 및 시각화
st.subheader("수출금액 상위 10행 결과")
st.dataframe(top_10, use_container_width=True, hide_index=True)

# 추가 다운로드 옵션 제공
csv_download_data = top_10.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
st.download_button(
    label="현재 상위 10개 결과 CSV 수동 다운로드",
    data=csv_download_data,
    file_name="report2.csv",
    mime="text/csv"
)

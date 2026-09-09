import pandas as pd
import streamlit as st


st.set_page_config(page_title="무역 데이터 필터링", layout="wide")
st.title("무역 데이터 필터링 및 분석")
st.caption("CSV를 올린 뒤, 왼쪽에서 원하는 조건을 직접 선택하세요.")


@st.cache_data
def load_data(file):
    """엑셀에서 저장된 CSV도 최대한 안정적으로 읽는다."""
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            file.seek(0)
            return pd.read_csv(file, encoding=encoding)
        except UnicodeDecodeError:
            continue
    file.seek(0)
    return pd.read_csv(file)


uploaded_file = st.file_uploader("무역 데이터 CSV 파일 업로드", type=["csv"])

if uploaded_file is None:
    st.info("분석할 CSV 파일을 업로드해 주세요.")
    st.stop()

try:
    df = load_data(uploaded_file)
except Exception as error:
    st.error(f"CSV 파일을 읽지 못했습니다: {error}")
    st.stop()

required_columns = {"hs_code", "국가명", "수출금액"}
missing_columns = required_columns - set(df.columns)
if missing_columns:
    st.error(f"필수 열이 없습니다: {', '.join(sorted(missing_columns))}")
    st.info(f"업로드된 열: {', '.join(map(str, df.columns))}")
    st.stop()

# 비교와 표시를 안정적으로 하기 위한 데이터 정리
df = df.copy()
df["hs_code"] = df["hs_code"].astype("string").str.replace(r"\.0$", "", regex=True)
df["수출금액"] = pd.to_numeric(df["수출금액"], errors="coerce")

with st.sidebar:
    st.header("필터 조건")

    hs_prefixes = sorted(df["hs_code"].dropna().str[:2].unique().tolist())
    selected_prefixes = st.multiselect(
        "HS 코드 앞 2자리", hs_prefixes, default=hs_prefixes,
        help="예: 85를 선택하면 85로 시작하는 HS 코드만 표시합니다.",
    )

    countries = sorted(df["국가명"].dropna().unique().tolist())
    selected_countries = st.multiselect("국가", countries, default=countries)

    selected_directions = None
    if "수출입구분" in df.columns:
        directions = sorted(df["수출입구분"].dropna().unique().tolist())
        selected_directions = st.multiselect("수출입 구분", directions, default=directions)

    valid_amounts = df["수출금액"].dropna()
    only_positive = st.checkbox("수출금액이 0보다 큰 행만", value=True)
    if valid_amounts.empty:
        amount_range = None
        st.warning("수출금액을 숫자로 읽을 수 있는 행이 없습니다.")
    else:
        min_amount, max_amount = float(valid_amounts.min()), float(valid_amounts.max())
        amount_range = st.slider(
            "수출금액 범위", min_value=min_amount, max_value=max_amount,
            value=(min_amount, max_amount),
        )

    selected_dates = None
    if "날짜" in df.columns:
        parsed_dates = pd.to_datetime(df["날짜"], errors="coerce")
        if parsed_dates.notna().any():
            df["_날짜"] = parsed_dates
            selected_dates = st.date_input(
                "기간", value=(parsed_dates.min().date(), parsed_dates.max().date()),
            )

    top_n = st.number_input("표시할 상위 건수", min_value=1, max_value=len(df), value=min(10, len(df)))

filtered_df = df.copy()
filtered_df = filtered_df[filtered_df["hs_code"].str[:2].isin(selected_prefixes)]
filtered_df = filtered_df[filtered_df["국가명"].isin(selected_countries)]

if selected_directions is not None:
    filtered_df = filtered_df[filtered_df["수출입구분"].isin(selected_directions)]
if only_positive:
    filtered_df = filtered_df[filtered_df["수출금액"] > 0]
if amount_range is not None:
    filtered_df = filtered_df[filtered_df["수출금액"].between(*amount_range)]
if selected_dates and len(selected_dates) == 2:
    start_date, end_date = pd.Timestamp(selected_dates[0]), pd.Timestamp(selected_dates[1])
    filtered_df = filtered_df[filtered_df["_날짜"].between(start_date, end_date + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1))]

result_df = filtered_df.sort_values("수출금액", ascending=False).head(int(top_n))
result_df = result_df.drop(columns="_날짜", errors="ignore")

left, right = st.columns(2)
left.metric("전체 행", f"{len(df):,}")
right.metric("필터 후 행", f"{len(filtered_df):,}")

st.subheader(f"수출금액 상위 {len(result_df):,}건")
st.dataframe(result_df, use_container_width=True, hide_index=True)

csv_data = result_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
st.download_button(
    "현재 결과 CSV 다운로드", csv_data, file_name="filtered_trade_report.csv", mime="text/csv"
)

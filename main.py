import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 데이터 불러오기
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("energy(2024).csv", encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv("energy(2024).csv", encoding='cp949')

    # 컬럼 정리
    df.columns = df.columns.str.strip()
    df.drop(columns=[col for col in df.columns if 'Unnamed' in col], inplace=True)

    # 월별 컬럼 자동 인식 및 숫자 처리
    month_columns = [col for col in df.columns if any(str(m) + "월" in col for m in range(1, 13))]

    for month in month_columns:
        df[month] = df[month].astype(str).str.replace(",", "").str.strip().astype(float)

    return df


df = load_data()

# 사이드바 필터 설정
st.sidebar.header("필터 선택")

years = df["연도"].unique()
sidos = df["시도"].unique()

selected_year = st.sidebar.selectbox("연도", years)
selected_sido = st.sidebar.selectbox("시도", sidos)

filtered_sgg = df[df["시도"] == selected_sido]["시군구"].unique()
selected_sgg = st.sidebar.selectbox("시군구", filtered_sgg)

filtered_contracts = df[
    (df["연도"] == selected_year) & 
    (df["시도"] == selected_sido) & 
    (df["시군구"] == selected_sgg)
]["계약종별"].unique()

selected_contract = st.sidebar.selectbox("계약종별", filtered_contracts)

# 데이터 필터링
filtered_df = df[
    (df["연도"] == selected_year) &
    (df["시도"] == selected_sido) &
    (df["시군구"] == selected_sgg) &
    (df["계약종별"] == selected_contract)
]

# 시각화
if not filtered_df.empty:
    st.subheader(f"{selected_year}년 {selected_sido} {selected_sgg} ({selected_contract}) 월별 전력 사용량")

    months = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월']
    usage = filtered_df[months].values.flatten()

    fig, ax = plt.subplots()
    ax.plot(months, usage, marker='o')
    ax.set_ylabel("전력 사용량 (kWh)")
    ax.set_xlabel("월")
    ax.set_title("월별 전력 사용량 추이")
    st.pyplot(fig)
else:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")

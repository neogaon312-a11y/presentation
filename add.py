import streamlit as st
import pandas as pd
from datetime import date
import os   # 🔹파일 존재 여부 확인용

st.set_page_config(page_title="수행평가 일정 관리", layout="centered")

st.title("📚 수행평가 · 시험 일정 관리 웹앱")
st.write("과제와 시험 일정을 한 곳에 모아서 D-day로 확인해보는 웹앱입니다!")

DATA_FILE = "tasks.csv"   # 🔹데이터를 저장할 파일 이름

# 🔹 파일에서 데이터 불러오기 함수
def load_tasks():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # 날짜 컬럼 문자열 -> date로 변환
        if "마감일" in df.columns:
            df["마감일"] = pd.to_datetime(df["마감일"]).dt.strftime("%Y-%m-%d")
        return df.to_dict(orient="records")
    return []

# 🔹 세션에 데이터 없으면 파일에서 먼저 불러오기
if "tasks" not in st.session_state:
    st.session_state["tasks"] = load_tasks()

# 🔹 현재 tasks를 파일로 저장하는 함수
def save_tasks():
    if len(st.session_state["tasks"]) > 0:
        df = pd.DataFrame(st.session_state["tasks"])
        df.to_csv(DATA_FILE, index=False)
    else:
        # 일정이 하나도 없으면 빈 파일/기존 파일 삭제 선택 가능
        # 여기서는 그냥 빈 파일로 저장
        df = pd.DataFrame(columns=["과목", "내용", "마감일", "중요도"])
        df.to_csv(DATA_FILE, index=False)

st.subheader("📌 일정 추가하기")

with st.form("add_task_form"):
    subject = st.text_input("과목명 (예: 수학, 정보)")
    title = st.text_input("과제 / 시험 이름")
    due_date = st.date_input("마감일", value=date.today())
    level = st.selectbox("중요도", ["하", "중", "상"])
    submitted = st.form_submit_button("추가하기")

    if submitted:
        if subject and title:
            st.session_state["tasks"].append({
                "과목": subject,
                "내용": title,
                "마감일": due_date.strftime("%Y-%m-%d"),
                "중요도": level
            })
            save_tasks()  # 🔹추가할 때마다 파일로 저장
            st.success("일정이 추가되었습니다!")
        else:
            st.error("과목과 내용을 꼭 입력해주세요.")

st.subheader("📅 일정 목록")

if len(st.session_state["tasks"]) == 0:
    st.info("아직 추가된 일정이 없습니다. 위에서 일정을 추가해보세요!")
else:
    df = pd.DataFrame(st.session_state["tasks"])

    # D-day 계산
    today = date.today()
    df["마감일_date"] = pd.to_datetime(df["마감일"]).dt.date
    df["D-day"] = df["마감일_date"].apply(lambda d: (d - today).days)

    # 정렬 (가까운 순)
    df = df.sort_values(by="D-day")

    # 필터
    with st.expander("🔍 필터"):
        subject_filter = st.text_input("특정 과목만 보기 (비워두면 전체)")
        only_this_week = st.checkbox("이번 주(7일 이내) 마감만 보기")

    filtered_df = df.copy()

    if subject_filter:
        filtered_df = filtered_df[filtered_df["과목"].str.contains(subject_filter)]

    if only_this_week:
        filtered_df = filtered_df[filtered_df["D-day"] <= 7]

    show_df = filtered_df[["과목", "내용", "마감일", "중요도", "D-day"]]

    st.write("※ D-day가 0이면 오늘 마감, 음수면 이미 지난 일정입니다.")
    st.dataframe(show_df, use_container_width=True)

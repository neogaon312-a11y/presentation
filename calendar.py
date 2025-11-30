import streamlit as st
from datetime import date, datetime
import calendar
import os
import json

st.set_page_config(page_title="수행평가 캘린더", layout="wide")

# -------------------------------------------------------
# 📌 폴더 & 파일 경로 설정
# -------------------------------------------------------
DATA_DIR = "data"
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
SUBJECTS_FILE = os.path.join(DATA_DIR, "subjects.json")
ASSIGNMENTS_FILE = os.path.join(DATA_DIR, "assignments.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)


# -------------------------------------------------------
# 📌 유틸 함수들 — JSON 저장 / 불러오기 / 이미지 저장
# -------------------------------------------------------
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_uploaded_images(assign_id, uploaded_files):
    """업로드된 이미지들을 파일로 저장하고 경로 리스트 반환"""
    paths = []
    if not uploaded_files:
        return paths

    for idx, file in enumerate(uploaded_files):
        safe_name = f"{assign_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx}_{file.name}"
        dest = os.path.join(UPLOAD_DIR, safe_name)

        with open(dest, "wb") as out:
            out.write(file.getbuffer())

        paths.append(dest)

    return paths


def delete_image_files(path_list):
    if not path_list:
        return
    for p in path_list:
        if os.path.exists(p):
            try:
                os.remove(p)
            except:
                pass


def force_rerun():
    try:
        st.rerun()
    except:
        st.experimental_rerun()


# -------------------------------------------------------
# 📌 세션 초기화 — 최초 1회 실행
# -------------------------------------------------------
if "initialized" not in st.session_state:

    # 과목 로드
    st.session_state["subject_colors"] = load_json(SUBJECTS_FILE, {})

    # 수행평가 로드
    st.session_state["assignments"] = load_json(ASSIGNMENTS_FILE, [])

    # next_id 설정
    if st.session_state["assignments"]:
        max_id = max(a["id"] for a in st.session_state["assignments"])
        st.session_state["next_id"] = max_id + 1
    else:
        st.session_state["next_id"] = 1

    st.session_state["selected_assignment_id"] = None
    st.session_state["edit_mode"] = False

    today = date.today()
    st.session_state["current_month"] = date(today.year, today.month, 1)

    st.session_state["initialized"] = True


# -------------------------------------------------------
# 📌 유틸 — 특정 날짜 과제 가져오기 / ID로 가져오기
# -------------------------------------------------------
def get_assignments_for(day: date):
    iso = day.isoformat()
    return [a for a in st.session_state["assignments"] if a["due_date"] == iso]


def get_assignment_by_id(assign_id):
    for a in st.session_state["assignments"]:
        if a["id"] == assign_id:
            return a
    return None


def change_month(delta: int):
    d = st.session_state["current_month"]
    year = d.year + (d.month + delta - 1) // 12
    month = (d.month + delta - 1) % 12 + 1
    st.session_state["current_month"] = date(year, month, 1)


# -------------------------------------------------------
# 📌 사이드바 — 과목 관리
# -------------------------------------------------------
with st.sidebar:
    st.header("🎨 과목 관리")

    if st.session_state["subject_colors"]:
        st.caption("등록된 과목들")
        for sub, col in st.session_state["subject_colors"].items():
            st.markdown(
                f"""
                <div style='display:flex;align-items:center;margin-bottom:4px;'>
                    <div style='width:16px;height:16px;background:{col};
                        border-radius:3px;margin-right:6px;border:1px solid #999;'></div>
                    <span>{sub}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("---")

    # 과목 삭제
    if st.session_state["subject_colors"]:
        st.subheader("과목 삭제")
        delete_subj = st.selectbox("삭제할 과목 선택", ["(선택없음)"] + list(st.session_state["subject_colors"].keys()))

        if delete_subj != "(선택없음)":
            if st.button("과목 삭제"):
                # 과목 삭제
                st.session_state["subject_colors"].pop(delete_subj, None)

                # 해당 과목의 수행평가 삭제
                new_list = []
                for a in st.session_state["assignments"]:
                    if a["subject"] == delete_subj:
                        delete_image_files(a["images"])
                    else:
                        new_list.append(a)

                st.session_state["assignments"] = new_list

                # 저장
                save_json(SUBJECTS_FILE, st.session_state["subject_colors"])
                save_json(ASSIGNMENTS_FILE, st.session_state["assignments"])

                st.success(f"'{delete_subj}' 과목 및 관련 과제 삭제 완료")
                force_rerun()

    st.markdown("---")

    # 과목 추가
    with st.form("add_subject"):
        st.subheader("과목 추가")
        subj = st.text_input("과목명")
        color = st.text_input("색상(#RRGGBB)", value="#")

        submit_subj = st.form_submit_button("저장")
        if submit_subj:
            if not subj.strip():
                st.warning("과목명을 입력해주세요.")
            elif not (len(color) == 7 and color.startswith("#")):
                st.warning("색상 형식이 잘못되었습니다 (#RRGGBB).")
            else:
                st.session_state["subject_colors"][subj.strip()] = color.upper()
                save_json(SUBJECTS_FILE, st.session_state["subject_colors"])
                st.success("과목 저장 완료")
                force_rerun()


# -------------------------------------------------------
# 📌 메인 화면
# -------------------------------------------------------
st.title("📅 수행평가 달력")

# ------------------- 달 이동 --------------------
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("◀"):
        change_month(-1)

with col2:
    cm = st.session_state["current_month"]
    st.markdown(f"<h2 style='text-align:center'>{cm.year}년 {cm.month}월</h2>", unsafe_allow_html=True)

with col3:
    if st.button("▶"):
        change_month(1)

st.markdown("---")


# -------------------------------------------------------
# 📌 수행평가 추가
# -------------------------------------------------------
st.subheader("✏️ 수행평가 추가")

with st.form("add_assignment"):
    c1, c2 = st.columns(2)
    with c1:
        due_date = st.date_input("마감일", value=date.today())
        title = st.text_input("제목")

    with c2:
        subjects = list(st.session_state["subject_colors"].keys())
        subject = st.selectbox("과목", subjects if subjects else ["(먼저 과목을 추가하세요)"])
        memo = st.text_area("메모", height=80)

    images = st.file_uploader("사진 업로드", accept_multiple_files=True)

    submit_assign = st.form_submit_button("등록")

    if submit_assign:
        if not title.strip():
            st.warning("제목을 입력해주세요.")
        elif not subjects:
            st.warning("먼저 과목을 추가해야 합니다.")
        else:
            new_id = st.session_state["next_id"]
            st.session_state["next_id"] += 1

            img_paths = save_uploaded_images(new_id, images)

            assignment = {
                "id": new_id,
                "title": title.strip(),
                "subject": subject,
                "due_date": due_date.isoformat(),
                "memo": memo.strip(),
                "images": img_paths,
                "created_at": datetime.now().isoformat()
            }

            st.session_state["assignments"].append(assignment)
            save_json(ASSIGNMENTS_FILE, st.session_state["assignments"])

            st.success("등록 완료!")
            force_rerun()


st.markdown("---")


# -------------------------------------------------------
# 📌 달력 렌더링
# -------------------------------------------------------
year = cm.year
month = cm.month
cal = calendar.Calendar(firstweekday=0)
weeks = cal.monthdatescalendar(year, month)

weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
cols = st.columns(7)
for i, name in enumerate(weekday_names):
    cols[i].markdown(f"<div style='text-align:center;font-weight:bold'>{name}</div>", unsafe_allow_html=True)

for week in weeks:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day.month != month:
                st.markdown(f"<div style='color:#999'>{day.day}</div>")
            else:
                st.markdown(f"**{day.day}**")

                day_assignments = get_assignments_for(day)
                for a in day_assignments:
                    color = st.session_state["subject_colors"].get(a["subject"], "#666")

                    st.markdown(
                        f"""
                        <div style="
                            background:{color}22;
                            border-left:4px solid {color};
                            padding:2px 4px;
                            font-size:0.75rem;
                            margin:2px 0;
                            border-radius:3px;">
                            <b>{a['subject']}</b><br>{a['title']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.button("열기", key=f"open_{a['id']}"):
                        st.session_state["selected_assignment_id"] = a["id"]
                        st.session_state["edit_mode"] = False
                        force_rerun()


st.markdown("---")


# -------------------------------------------------------
# 📌 선택된 수행평가 상세보기 / 수정
# -------------------------------------------------------
st.subheader("📌 선택된 수행평가")

selected = get_assignment_by_id(st.session_state["selected_assignment_id"])

if not selected:
    st.info("달력에서 열기를 눌러 과제를 선택하세요.")
else:
    if not st.session_state["edit_mode"]:
        color = st.session_state["subject_colors"].get(selected["subject"], "#666")

        st.markdown(
            f"""
            <div style="
                border:1px solid #ccc;
                border-left:6px solid {color};
                padding:10px;
                border-radius:6px;">
                <h4>{selected['title']}</h4>
                <p><b>과목:</b> {selected['subject']}</p>
                <p><b>마감일:</b> {selected['due_date']}</p>
                <p style="white-space:pre-wrap">{selected['memo']}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        if selected["images"]:
            st.caption("📸 업로드된 사진")
            for img in selected["images"]:
                st.image(img, width=400)

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("수정"):
                st.session_state["edit_mode"] = True
                force_rerun()

        with col_b:
            if st.button("삭제"):
                delete_image_files(selected["images"])
                st.session_state["assignments"] = [
                    x for x in st.session_state["assignments"] if x["id"] != selected["id"]
                ]
                save_json(ASSIGNMENTS_FILE, st.session_state["assignments"])
                st.session_state["selected_assignment_id"] = None
                st.success("삭제 완료!")
                force_rerun()

    else:
        st.subheader("✏️ 수행평가 수정")

        with st.form("edit_form"):
            c1, c2 = st.columns(2)

            with c1:
                new_title = st.text_input("제목", value=selected["title"])
                new_date = st.date_input("마감일", value=date.fromisoformat(selected["due_date"]))

            with c2:
                subjects = list(st.session_state["subject_colors"].keys())
                new_subject = st.selectbox("과목", subjects, index=subjects.index(selected["subject"]))
                new_memo = st.text_area("메모", value=selected["memo"], height=80)

            new_images = st.file_uploader("사진 다시 업로드(선택)", accept_multiple_files=True)

            save_btn = st.form_submit_button("저장")
            cancel_btn = st.form_submit_button("취소")

            if save_btn:
                selected["title"] = new_title
                selected["subject"] = new_subject
                selected["due_date"] = new_date.isoformat()
                selected["memo"] = new_memo

                if new_images:
                    delete_image_files(selected["images"])
                    selected["images"] = save_uploaded_images(selected["id"], new_images)

                save_json(ASSIGNMENTS_FILE, st.session_state["assignments"])
                st.session_state["edit_mode"] = False
                st.success("수정 완료!")
                force_rerun()

            if cancel_btn:
                st.session_state["edit_mode"] = False
                st.session_state["selected_assignment_id"] = None
                force_rerun()


st.markdown("---")


# -------------------------------------------------------
# 📌 해야 할 수행평가 목록
# -------------------------------------------------------
st.subheader("⏳ 해야 할 수행평가")

today = date.today()
upcoming = sorted(
    [a for a in st.session_state["assignments"] if a["due_date"] >= today.isoformat()],
    key=lambda x: x["due_date"]
)

if not upcoming:
    st.info("해야 할 수행평가가 없습니다.")
else:
    for a in upcoming:
        color = st.session_state["subject_colors"].get(a["subject"], "#666")
        st.markdown(
            f"""
            <div style="
                border:1px solid #ccc;
                border-left:6px solid {color};
                padding:8px;
                border-radius:6px;
                margin-bottom:6px;">
                <b>{a['subject']}</b> — {a['title']}  
                <div>마감일: {a['due_date']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

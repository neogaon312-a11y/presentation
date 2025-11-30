import streamlit as st
from datetime import date, datetime
import calendar
import os
import json

st.set_page_config(page_title="수행평가 캘린더", layout="wide")

# ---------- 경로 및 폴더 설정 ----------
DATA_DIR = "data"
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
SUBJECTS_FILE = os.path.join(DATA_DIR, "subjects.json")
ASSIGNMENTS_FILE = os.path.join(DATA_DIR, "assignments.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------- 공통: 강제 새로고침 ----------
def force_rerun():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# ---------- 파일 로드 / 저장 함수 ----------
def load_subjects():
    if os.path.exists(SUBJECTS_FILE):
        with open(SUBJECTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_subjects():
    with open(SUBJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state["subject_colors"], f, ensure_ascii=False, indent=2)

def load_assignments():
    if os.path.exists(ASSIGNMENTS_FILE):
        with open(ASSIGNMENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_assignments():
    with open(ASSIGNMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state["assignments"], f, ensure_ascii=False, indent=2)

def save_uploaded_images(assign_id, uploaded_files):
    """업로드된 파일들을 디스크에 저장하고 경로 리스트를 반환"""
    paths = []
    if not uploaded_files:
        return paths
    for idx, file in enumerate(uploaded_files):
        safe_name = f"{assign_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx}_{file.name}"
        dest_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(dest_path, "wb") as out:
            out.write(file.getbuffer())
        paths.append(dest_path)
    return paths

def delete_image_files(path_list):
    """과제 삭제 시 이미지 파일도 같이 삭제(있으면)"""
    if not path_list:
        return
    for p in path_list:
        try:
            if os.path.exists(p):
                os.remove(p)
        except:
            # 삭제 실패해도 앱이 죽지 않게
            pass

# ---------- 최초 1회 초기화 & 파일 로드 ----------
if "initialized" not in st.session_state:
    st.session_state["subject_colors"] = load_subjects()
    st.session_state["assignments"] = load_assignments()

    # next_id는 기존 데이터의 최대 id + 1 로 설정
    if st.session_state["assignments"]:
        max_id = max(a.get("id", 0) for a in st.session_state["assignments"])
        st.session_state["next_id"] = max_id + 1
    else:
        st.session_state["next_id"] = 1

    st.session_state["selected_assignment_id"] = None
    st.session_state["edit_mode"] = False

    today = date.today()
    st.session_state["current_m_]()_

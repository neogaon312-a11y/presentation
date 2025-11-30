import streamlit as st
from datetime import date, datetime
import calendar

st.set_page_config(page_title="수행평가 캘린더", layout="wide")

# ---------- 세션 상태 초기화 ----------
if "subject_colors" not in st.session_state:
    # 과목 색상 딕셔너리: {"과목명": "#RRGGBB"}
    st.session_state.subject_colors = {}

if "assignments" not in st.session_state:
    # 수행평가 리스트
    # 각 항목 예시:
    # {
    #   "id": 1,
    #   "title": "...",
    #   "subject": "...",
    #   "due_date": "2025-12-03",
    #   "memo": "...",
    #   "images": [UploadedFile, ...],
    # }
    st.session_state.assignments = []

if "next_id" not in st.session_state:
    st.session_state.next_id = 1

if "selected_assignment_id" not in st.session_state:
    st.session_state.selected_assignment_id = None

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

today = date.today()
if "current_month" not in st.session_state:
    st.session_state.current_month = date(today.year, today.month, 1)


# ---------- 유틸 함수 ----------
def change_month(delta: int):
    """현재 선택된 달을 delta(±1)만큼 이동"""
    d = st.session_state.current_month
    year = d.year + (d.month + delta - 1) // 12
    month = (d.month + delta - 1) % 12 + 1
    st.session_state.current_month = date(year, month, 1)


def get_assignments_by_date(target_date: date):
    iso = target_date.isoformat()
    return [a for a in st.session_state.assignments if a["due_date"] == iso]


def get_assignment_by_id(aid: int):
    for a in st.session_state.assignments:
        if a["id"] == aid:
            return a
    return None


# ---------- 사이드바: 과목 색상 관리 ----------
with st.sidebar:
    st.header("🎨 과목 색상 설정")

    # 현재 과목 목록 보여주기
    if st.session_state.subject_colors:
        st.caption("현재 등록된 과목들")
        for subj, color in st.session_state.subject_colors.items():
            st.markdown(
                f"<div style='display:flex;align-items:center;margin-bottom:4px;'>"
                f"<div style='width:14px;height:14px;background:{color};"
                f"border-radius:3px;margin-right:6px;border:1px solid #aaa;'></div>"
                f"<span>{subj}</span></div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("아직 등록된 과목이 없습니다. 아래에서 추가하세요!")

    st.markdown("---")
    with st.form("add_subject_form"):
        st.subheader("과목 추가 / 수정")
        subj = st.text_input("과목 이름", placeholder="예: 물리, 국어, 정보")
        color = st.text_input(
            "색상 (HEX 코드)", value="#", placeholder="#FF0000 처럼 입력"
        )
        submitted = st.form_submit_button("저장")
        if submitted:
            if not subj.strip():
                st.warning("과목 이름을 입력해 주세요.")
            elif not (len(color) == 7 and color.startswith("#")):
                st.warning("색상은 #RRGGBB 형태로 입력해 주세요.")
            else:
                st.session_state.subject_colors[subj.strip()] = color.upper()
                st.success(f"과목 '{subj.strip()}' 색상을 {color.upper()} 로 저장했습니다.")


# ---------- 메인 타이틀 ----------
st.title("📅 수행평가 캘린더")

# ---------- 상단: 월 이동 / 현재 월 표시 ----------
col_prev, col_month, col_next = st.columns([1, 2, 1])

with col_prev:
    if st.button("◀ 지난달"):
        change_month(-1)

with col_month:
    cm = st.session_state.current_month
    st.markdown(
        f"<h3 style='text-align:center;'>{cm.year}년 {cm.month}월</h3>",
        unsafe_allow_html=True,
    )

with col_next:
    if st.button("다음달 ▶"):
        change_month(1)


# ---------- 수행평가 추가 폼 ----------
st.markdown("### ✏️ 수행평가 추가")

with st.form("add_assignment_form"):
    left, right = st.columns(2)

    with left:
        due_date = st.date_input("마감일", value=today)
        title = st.text_input("제목", placeholder="예: 물리 포물선 실험 보고서")

    with right:
        subjects = list(st.session_state.subject_colors.keys())
        subject = st.selectbox(
            "과목",
            options=subjects if subjects else ["(먼저 과목을 추가해 주세요)"],
        )
        memo = st.text_area("메모 (선택)", height=80)

    images = st.file_uploader(
        "수행평가 관련 사진 업로드 (여러 장 가능)",
        type=["png", "jpg", "jpeg", "webp", "heic", "heif"],
        accept_multiple_files=True,
    )

    submitted = st.form_submit_button("수행평가 등록")

    if submitted:
        if not title.strip():
            st.warning("제목을 입력해 주세요.")
        elif not subjects:
            st.warning("먼저 왼쪽 사이드바에서 과목을 추가해 주세요.")
        else:
            new_id = st.session_state.next_id
            st.session_state.next_id += 1

            st.session_state.assignments.append(
                {
                    "id": new_id,
                    "title": title.strip(),
                    "subject": subject if subjects else "",
                    "due_date": due_date.isoformat(),
                    "memo": memo.strip(),
                    "images": images,
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                }
            )
            st.success("수행평가를 캘린더에 등록했습니다!")


st.markdown("---")

# ---------- 월별 캘린더 렌더링 ----------
st.markdown("### 🗓 월별 캘린더 (박스 클릭 → 상세 보기)")

year = st.session_state.current_month.year
month = st.session_state.current_month.month

cal = calendar.Calendar(firstweekday=0)  # 0 = Monday, 6 = Sunday
month_weeks = cal.monthdatescalendar(year, month)

# 요일 헤더
weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
cols = st.columns(7)
for i, name in enumerate(weekday_names):
    with cols[i]:
        st.markdown(
            f"<div style='text-align:center;font-weight:bold;'>{name}</div>",
            unsafe_allow_html=True,
        )

# 날짜 + 수행평가 표시 (각 수행평가별로 '열기' 버튼)
for week in month_weeks:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            # 이번 달이 아닌 날짜는 흐리게
            if day.month != month:
                st.markdown(
                    f"<div style='color:#bbbbbb;text-align:left;'>{day.day}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f"**{day.day}**")

                day_assignments = get_assignments_by_date(day)
                if not day_assignments:
                    continue

                for a in day_assignments:
                    color = st.session_state.subject_colors.get(a["subject"], "#666666")

                    # 색깔 박스 (정보 표시)
                    st.markdown(
                        f"""
                        <div style="
                            background-color:{color}22;
                            border-left:4px solid {color};
                            padding:2px 4px;
                            margin:2px 0;
                            font-size:0.7rem;
                            border-radius:4px;
                            ">
                            <strong>{a['subject']}</strong><br/>
                            {a['title']}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # '열기' 버튼 (클릭 시 선택된 수행평가 변경)
                    if st.button("열기", key=f"open_{a['id']}"):
                        st.session_state.selected_assignment_id = a["id"]
                        st.session_state.edit_mode = False

st.markdown("---")

# ---------- 선택된 수행평가 상세 + 수정 ----------
st.markdown("### 📌 선택된 수행평가")

selected = (
    get_assignment_by_id(st.session_state.selected_assignment_id)
    if st.session_state.selected_assignment_id is not None
    else None
)

if selected is None:
    st.info("캘린더에서 보고 싶은 수행평가의 '열기' 버튼을 눌러 선택해 주세요.")
else:
    # 보기 모드 / 수정 모드 나누기
    if not st.session_state.edit_mode:
        top_left, top_right = st.columns([3, 1])
        with top_left:
            color = st.session_state.subject_colors.get(selected["subject"], "#666666")
            st.markdown(
                f"""
                <div style="
                    border:1px solid #dddddd;
                    border-left:6px solid {color};
                    border-radius:6px;
                    padding:10px 12px;
                    margin-bottom:10px;
                    ">
                    <div style="font-size:1rem;font-weight:bold;margin-bottom:4px;">
                        {selected['title']}
                    </div>
                    <div style="font-size:0.9rem;color:{color};font-weight:bold;">
                        과목: {selected['subject']}
                    </div>
                    <div style="font-size:0.85rem;margin-top:4px;">
                        마감일: {selected['due_date']}
                    </div>
                    <div style="font-size:0.85rem;margin-top:8px;white-space:pre-wrap;">
                        {selected['memo'] if selected['memo'] else "(메모 없음)"}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 업로드된 사진 표시
            if selected["images"]:
                st.caption("📷 업로드된 사진")
                st.image(selected["images"], use_column_width=True)
            else:
                st.caption("📷 업로드된 사진이 없습니다.")

        with top_right:
            st.write("")  # 여백
            st.write("")
            if st.button("수정", key="edit_btn"):
                st.session_state.edit_mode = True

    else:
        st.markdown("#### ✏️ 수행평가 수정")

        # 수정 폼
        with st.form("edit_assignment_form"):
            left, right = st.columns(2)

            with left:
                new_due_date = st.date_input(
                    "마감일",
                    value=date.fromisoformat(selected["due_date"]),
                    key="edit_due_date",
                )
                new_title = st.text_input(
                    "제목",
                    value=selected["title"],
                    key="edit_title",
                )

            with right:
                subjects = list(st.session_state.subject_colors.keys())
                # 과목 선택 박스에서 현재 과목을 기본값으로
                if selected["subject"] in subjects:
                    default_index = subjects.index(selected["subject"])
                else:
                    default_index = 0

                new_subject = st.selectbox(
                    "과목",
                    options=subjects if subjects else ["(먼저 과목을 추가해 주세요)"],
                    index=default_index if subjects else 0,
                    key="edit_subject",
                )

                new_memo = st.text_area(
                    "메모 (선택)",
                    value=selected["memo"],
                    height=80,
                    key="edit_memo",
                )

            new_images = st.file_uploader(
                "수행평가 관련 사진 다시 업로드 (선택, 새로 올리면 기존 사진을 대체)",
                type=["png", "jpg", "jpeg", "webp", "heic", "heif"],
                accept_multiple_files=True,
                key="edit_images",
            )

            col_save, col_cancel = st.columns(2)
            with col_save:
                save_clicked = st.form_submit_button("저장")
            with col_cancel:
                cancel_clicked = st.form_submit_button("취소")

            if save_clicked:
                # 값 업데이트
                selected["title"] = new_title.strip()
                selected["subject"] = new_subject if subjects else selected["subject"]
                selected["due_date"] = new_due_date.isoformat()
                selected["memo"] = new_memo.strip()
                # 새 이미지를 업로드했으면 교체, 아니면 기존 유지
                if new_images:
                    selected["images"] = new_images

                st.session_state.edit_mode = False
                st.success("수행평가 정보를 수정했습니다.")

            elif cancel_clicked:
                st.session_state.edit_mode = False
                st.info("수정을 취소했습니다.")

st.markdown("---")

# ---------- 해야 할 수행평가 리스트 (날짜 순) ----------
st.markdown("### 🔔 해야 할 수행평가 (다가오는 과제)")

# 오늘 기준으로 아직 마감일이 남은 과제만
upcoming = [
    a
    for a in st.session_state.assignments
    if a["due_date"] >= today.isoformat()
]

# 마감일 기준으로 정렬
upcoming.sort(key=lambda x: x["due_date"])

if not upcoming:
    st.info("앞으로 해야 할 수행평가가 없습니다.")
else:
    for a in upcoming:
        due = date.fromisoformat(a["due_date"])
        color = st.session_state.subject_colors.get(a["subject"], "#666666")

        st.markdown(
            f"""
            <div style="
                border:1px solid #dddddd;
                border-left:6px solid {color};
                border-radius:6px;
                padding:6px 8px;
                margin-bottom:8px;
                ">
                <div style="font-weight:bold;color:{color};">
                    {a['subject']}
                </div>
                <div style="font-size:0.85rem;">
                    마감일: {due.strftime('%Y-%m-%d')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

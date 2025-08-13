import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

st.set_page_config(page_title="출석 기록", page_icon="🗓️")

@st.cache_resource
def get_ws():
    # Secrets에 문자열로 넣은 JSON을 파싱
    info = json.loads(st.secrets["gcp_service_account"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)

    # 시트 열기
    sh = gc.open(st.secrets.get("SPREADSHEET_NAME", "출석부"))
    ws = sh.worksheet(st.secrets.get("WORKSHEET_NAME", "시트1"))

    # 비어 있으면 헤더 보장
    if not ws.get_all_values():
        ws.update("A1:B1", [["날짜", "출석 기록"]])

    return ws

def write_record(name: str):
    if not name.strip():
        return "이름을 입력하세요.", False

    ws = get_ws()
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    record = f"{name.strip()} ({current_time})"

    try:
        cell = ws.find(today, in_column=1)
        row = cell.row
        row_data = ws.row_values(row)
        next_col = len(row_data) + 1
        ws.update_cell(row, next_col, record)
        return f"[{today}] [{name}] 기록 추가 완료", True
    except gspread.exceptions.CellNotFound:
        ws.append_row([today, record])
        return f"새 날짜 [{today}]에 [{name}] 기록 추가 완료", True
    except Exception as e:
        return f"오류: {e}", False

st.title("출근 기록")
st.caption("이름을 입력하고 [기록하기]를 누르면 구글 시트에 저장됩니다.")

col1, col2 = st.columns([3,1])
with col1:
    name = st.text_input("이름", placeholder="예) 홍길동")
with col2:
    st.write("")  # 정렬용

if st.button("기록하기", type="primary"):
    msg, ok = write_record(name)
    (st.success if ok else st.error)(msg)

st.divider()
st.markdown(
    """
**사용 팁**
- 스프레드시트 이름: `SPREADSHEET_NAME`(기본: 출석부)  
- 워크시트 탭 이름: `WORKSHEET_NAME`(기본: 시트1)  
이름이 다르면 Secrets에서 바꿔주세요.
"""
)


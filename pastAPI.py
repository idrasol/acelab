from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Union
import os
import openai  # ✅ 최신 방식

# --- 유틸 및 프롬프트
from utils import ask_gpt, get_current_distribution_time
from prompt import get_press_release_prompt

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("❌ OPENAI_API_KEY가 .env에 설정되어 있지 않습니다.")

openai.api_key = api_key  # ✅ 클라이언트 객체 대신 직접 설정

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def get_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="index.html 파일이 없습니다.")
    return FileResponse(index_file)

@app.post("/generate-dummy")
async def generate_dummy(
    title: str = Form(...),
    author: str = Form(...),
    contact: str = Form(...),
    content: str = Form(...),
    department: str = Form(""),
    files: List[UploadFile] = File([])
):
    filenames = [file.filename for file in files]
    distribute_date, distribute_time = get_current_distribution_time()

    dummy_text = f"(첨부파일 {len(files)}개: " + ", ".join(filenames) + ")"
    prompt = get_press_release_prompt(
        dummy_text, title, author, contact, content, department,
        distribute_date, distribute_time
    )

    try:
        reply = ask_gpt(prompt)  # ✅ client 제거
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ GPT 응답 실패: {e}")

@app.get("/health")
def health_check():
    return {"status": "running"}

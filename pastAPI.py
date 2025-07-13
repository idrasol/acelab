from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Union, Optional
import os
from fastapi.responses import JSONResponse

# --- 모듈 import ---
from utils import ask_gpt, get_current_distribution_time
from utils import MAX_FILE_SIZE_MB, MAX_FILE_SIZE, MAX_TEXT_CHARS
from readfile import (
    extract_pdf_text,
    extract_hwp_text,
    extract_hwpx_text_zip,
    extract_docx_text,
    extract_txt_text,
)
from prompt import get_press_release_prompt

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("❌ OPENAI_API_KEY가 .env에 설정되어 있지 않습니다.")

client = OpenAI(api_key=api_key)
app = FastAPI(max_body_size=1024*1024*50)

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

@app.post("/generate-with-pdf")
async def generate_with_pdf(
    title: str = Form(...),
    author: str = Form(...),
    contact: str = Form(...),
    content: str = Form(...),
    department: str = Form(""),
    files: List[UploadFile] = File([])
):
    print("\n📥 클라이언트 입력값 수신")
    print(f"제목       : {title}")
    print(f"담당자     : {author}")
    print(f"연락처     : {contact}")
    print(f"부처명     : {department}")
    print(f"핵심내용   : {content}")
    print(f"파일이 전송되었습니다: {len(files)}개 파일")

    text_content = ""

    if files:
        for file in files:
            print(f"파일 이름: {file.filename}")

            contents = await file.read()
            if len(contents) > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail=f"'{file.filename}' 파일이 10MB를 초과합니다.")

            file_path = UPLOAD_DIR / file.filename
            with open(file_path, "wb") as fobj:
                fobj.write(contents)
            print("✅ 파일 저장 완료:", file_path)

            try:
                extracted_text = ""
                if file.filename.endswith('.pdf'):
                    extracted_text = extract_pdf_text(file_path)
                elif file.filename.endswith(".docx"):
                    extracted_text = extract_docx_text(file_path)
                elif file.filename.endswith(".hwp"):
                    extracted_text = extract_hwp_text(file_path)
                elif file.filename.endswith(".hwpx"):
                    extracted_text = extract_hwpx_text_zip(file_path)
                else:
                    extracted_text = "(지원되지 않는 파일 형식입니다.)"

                print(f"📄 텍스트 추출 완료: {len(extracted_text)}자")
                text_content += "\n" + extracted_text

            except Exception as e:
                print(f"❌ 파일 처리 오류, 무시하고 진행합니다: {e}")
                continue

    # 텍스트 추출 결과 확인
    print(f"📌 누적된 전체 텍스트 길이: {len(text_content)}자")
    short_text_content = text_content[:MAX_TEXT_CHARS]

    if not short_text_content.strip():
        raise HTTPException(status_code=400, detail="❗ 첨부된 파일에서 내용을 추출하지 못했습니다.")

    distribute_date, distribute_time = get_current_distribution_time()

    prompt = get_press_release_prompt(
        short_text_content,
        title, author, contact, content, department,
        distribute_date, distribute_time
    )

    print("\n📝 GPT 요청 프롬프트 전체:\n" + "=" * 50)
    print(prompt)
    print("=" * 50)

    try:
        reply = ask_gpt(client, prompt)
        if not reply.strip():
            return {"result": "❗ GPT로부터 응답을 받지 못했습니다."}

        print("\n✅ GPT 응답 전체 내용:\n" + "=" * 50)
        print(reply)
        print("=" * 50)
        return {"reply": reply}

    except OpenAIError as oe:
        print("❌ OpenAI 오류:", oe)
        raise HTTPException(status_code=502, detail="OpenAI API 호출 실패")
    
    except Exception as e:
        print("❌ 서버 오류:", e)
        raise HTTPException(status_code=500, detail="서버 내부 오류")

from fastapi import Form, UploadFile, File
from typing import Optional, Union, List
from fastapi.responses import JSONResponse

@app.post("/api/chat")
async def chat(
    message: Optional[str] = Form(None),
    files: Union[UploadFile, List[UploadFile], None] = File(None)
):
    print("🔥 [디버그] files의 실제 타입:", type(files))
    gpt_input = ""

    if message:
        gpt_input += f"사용자 메시지:\n{message}\n"

    # ✅ 강제 리스트 변환
    if files is None:
        files = []
    elif not isinstance(files, list):
        files = [files]

    for file in files:
        print(f"📎 첨부파일 수신: {file.filename}")
        content = await file.read()

        if len(content) > MAX_FILE_SIZE:
            return JSONResponse(
                status_code=400,
                content={"reply": f"❌ '{file.filename}'은 너무 큽니다. 최대 {MAX_FILE_SIZE_MB}MB까지만 허용됩니다."}
            )

        temp_path = UPLOAD_DIR / file.filename
        with open(temp_path, "wb") as f:
            f.write(content)
        print(f"✅ 파일 저장 완료: {temp_path}")

        try:
            suffix = file.filename.lower()
            if suffix.endswith(".pdf"):
                text = extract_pdf_text(temp_path)
            elif suffix.endswith(".hwp"):
                text = extract_hwp_text(temp_path)
            elif suffix.endswith(".hwpx"):
                text = extract_hwpx_text_zip(temp_path)
            elif suffix.endswith(".docx"):
                text = extract_docx_text(temp_path)
            elif suffix.endswith(".txt"):
                text = extract_txt_text(temp_path)
            else:
                text = "(지원되지 않는 파일 형식입니다.)"
        except Exception as e:
            text = f"(❌ 파일 처리 오류: {e})"

        gpt_input += f"\n📎 첨부파일 '{file.filename}' 내용:\n{text[:2000]}\n"

    if not gpt_input.strip():
        return JSONResponse(
            status_code=400,
            content={"reply": "❗ 메시지나 첨부파일 내용이 없습니다."}
        )

    try:
        reply = ask_gpt(client, gpt_input)
        if not reply or not reply.strip():
            return JSONResponse(status_code=200, content={"reply": "❗ GPT 응답이 비어 있습니다."})

        print("✅ GPT 응답 완료")
        return JSONResponse(status_code=200, content={"reply": reply})

    except OpenAIError as oe:
        print("❌ OpenAI 오류:", oe)
        return JSONResponse(status_code=502, content={"reply": "❌ OpenAI API 호출 실패"})

    except Exception as e:
        print("❌ 서버 오류:", e)
        return JSONResponse(status_code=500, content={"reply": f"❌ 서버 내부 오류: {e}"})

@app.post("/generate-greeting")
async def generate_greeting(
    speaker: str = Form(...),
    position: str = Form(...),
    event: str = Form(...),
    date: str = Form(...),
    message: str = Form(...)
):
    print("\n📥 인사말 요청 수신")
    print(f"작성자: {speaker}, 직위: {position}")
    print(f"행사: {event}, 날짜: {date}")
    print(f"주요 메시지: {message}")

    # ✅ 변수 텍스트를 그대로 사용하지 않고 자연어로 제공
    prompt = f"""
너는 공공기관 행사에서 낭독되는 품격 있는 인사말을 작성하는 전문가야.

다음 정보를 참고하여 진심 어린 인사말을 약 500~800자 분량으로 작성해줘:

- 작성자명은 "{speaker}"이고, 직위는 "{position}"야.
- 이 인사말은 "{event}"라는 행사에서 발표될 거야.
- 행사 날짜는 {date}야.
- 전달하고 싶은 핵심 메시지는 "{message}"야.

[작성 조건]
- 서두 → 감사 인사 → 핵심 메시지 강조 → 희망적 마무리 순서로 구성해줘.
- 너무 딱딱하거나 건조하지 않게, 공손하고 자연스럽게 써줘.
- HTML이나 마크업 없이, 줄 바꿈은 그대로 출력하고, 인사말만 작성해줘.
"""

    try:
        result = ask_gpt(client, prompt)
        print("\n✅ GPT 인사말 생성 완료:")
        print(result)
        return {"result": result}

    except OpenAIError as oe:
        print("❌ OpenAI 오류:", oe)
        raise HTTPException(status_code=502, detail="OpenAI API 호출 실패")
    
    except Exception as e:
        print("❌ 서버 오류:", e)
        raise HTTPException(status_code=500, detail="서버 내부 오류")
    
@app.post("/generate-congrats")
async def generate_congrats(
    org_name: str = Form(..., alias="org-name"),
    org_leader: str = Form(..., alias="org-leader"),
    event_name: str = Form(..., alias="event-name"),
    event_purpose: str = Form(..., alias="event-purpose"),
    audience: str = Form(...),
    audience_etc: str = Form("", alias="audience-etc"),
    style: str = Form(...),
    style_etc: str = Form("", alias="style-etc"),
    length: str = Form(...),
    length_etc: str = Form("", alias="length-etc"),
):
    print("\n🎉 축사 요청 수신")
    print(f"기관명: {org_name}, 기관장: {org_leader}, 행사명: {event_name}")
    print(f"목적: {event_purpose}, 청중: {audience}, 스타일: {style}, 분량: {length}")

    # 기타 항목이 선택된 경우 대체
    audience_final = audience_etc if audience == "기타" else audience
    style_final = style_etc if style == "기타" else style
    length_final = length_etc if length == "기타" else length

    prompt = f"""
너는 공공기관 공식 행사를 위한 축사를 대신 작성해주는 AI 비서야.

다음 정보를 바탕으로 품격 있고 진정성 있는 축사를 작성해줘.

[입력 정보]
- 기관명: {org_name}
- 기관장 이름 및 직함: {org_leader}
- 행사명: {event_name}
- 행사 목적 및 성격: {event_purpose}
- 청중 대상: {audience_final}
- 문체 스타일: {style_final}
- 분량: {length_final}

[작성 조건]
- 서두 인사 → 행사 취지 강조 → 격려 → 희망 메시지 → 마무리 인사 순으로 작성
- 줄바꿈과 단락 구분 포함
- 공공기관 행사에 어울리는 말투로 작성
- 전체 길이는 요청된 분량에 맞춰 작성
- 괄호나 대괄호 없이 실제 값으로 작성

작성된 축사:
"""

    try:
        result = ask_gpt(client, prompt)
        print("\n✅ GPT 인사말 생성 완료:")
        print(result)
        return {"result": result}

    except OpenAIError as oe:
        print("❌ OpenAI 오류:", oe)
        raise HTTPException(status_code=502, detail="OpenAI API 호출 실패")
    
    except Exception as e:
        print("❌ 서버 오류:", e)
        raise HTTPException(status_code=500, detail="서버 내부 오류")

@app.get("/health")
def health_check():
    return {"status": "running"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 서버 실행 중: http://127.0.0.1:5000")
    uvicorn.run("pastAPI:app", host="127.0.0.1", port=5000, reload=True)

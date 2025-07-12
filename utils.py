import html
from datetime import datetime
from openai import OpenAIError

# 파일 업로드 최대 크기 (단위: MB)
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024

# 최대 텍스트 길이 (GPT 프롬프트에 전달할 문서 내용 제한 길이)
MAX_TEXT_CHARS = 2000

def ask_gpt(client, prompt: str, temperature=0.7, max_tokens=2000, model="gpt-4o") -> str:
    """
    OpenAI GPT 모델에 프롬프트를 전달하고 응답 텍스트를 반환
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ GPT 요청 오류: {e}")
        raise

def sanitize_text(text: str) -> str:
    """
    사용자 입력 텍스트에서 HTML 특수문자 이스케이프 및 불필요한 개행/공백 제거
    """
    return html.escape(text.strip()).replace("\n", " ").replace("  ", " ")

def get_current_distribution_time():
    """
    현재 시각 기준 배포일과 배포시각 문자열 생성
    예: ('2025년 07월 10일', '16:42')
    """
    now = datetime.now()
    distribute_date = now.strftime("%Y년 %m월 %d일")
    distribute_time = now.strftime("%H:%M")
    return distribute_date, distribute_time

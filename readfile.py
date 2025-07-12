import fitz
import pyhwp
import olefile
import re
from pyhwpx import Hwp
import zipfile
import xml.etree.ElementTree as ET
from docx import Document

def extract_docx_text(file_path):
    try:
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        print(f"❌ DOCX 텍스트 추출 오류: {e}")
        return ""

def extract_hwpx_text_zip(file_path: str) -> str:
    text_result = ""
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            if "Contents/section0.xml" in z.namelist():
                with z.open("Contents/section0.xml") as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    for elem in root.iter():
                        if elem.tag.endswith("t") and elem.text:
                            text_result += elem.text.strip() + " "
        return text_result.strip()
    except Exception as e:
        print(f"❌ hwpx XML 파싱 오류: {e}")
        return ""

def extract_hwp_text(file_path):
    try:
        if not olefile.isOleFile(file_path):
            print("❌ OLE 형식이 아닌 HWP 파일입니다.")
            return ""
        ole = olefile.OleFileIO(file_path)
        if not ole.exists("PrvText"):
            print("❌ 'PrvText' 스트림이 존재하지 않습니다. 버전이 다르거나 암호화된 파일일 수 있습니다.")
            return ""
        content = ole.openstream("PrvText").read()
        text = content.decode('utf-16', errors='ignore')
        text = re.sub(r'[^\uAC00-\uD7A3a-zA-Z0-9\s.,!?]', '', text)
        return text.strip()
    except Exception as e:
        print(f"❌ olefile을 이용한 HWP 처리 중 오류: {e}")
        return ""

def extract_pdf_text(file_path: str) -> str:
    text_content = ""
    try:
        with fitz.open(str(file_path)) as doc:
            for page in doc:
                text_content += page.get_text()
        text_content = text_content.strip()
        return text_content
    except Exception as e:
        print(f"❌ PDF 파싱 오류: {e}")
        return ""

def extract_txt_text(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        # EUC-KR 같은 경우도 대응
        with open(file_path, "r", encoding="euc-kr") as f:
            return f.read()
    except Exception as e:
        return f"(❌ TXT 파일 읽기 오류: {e})"
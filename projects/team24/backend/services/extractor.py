import re
import httpx
import os


def preprocess_text(text: str) -> str:
    """
    추출된 텍스트를 전처리합니다.
    - 불필요한 연속된 공백 및 탭을 단일 공백으로 치환합니다.
    - 3개 이상의 연속된 개행 문자를 2개로 다듬어 구조를 정돈합니다.
    - 텍스트 앞뒤의 공백을 제거합니다.
    """
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    계약서 파일에서 텍스트를 추출합니다.
    - .txt 파일인 경우: 인코딩에 맞추어 직접 디코딩 처리 및 전처리를 수행합니다.
    - 그 외 파일(PDF, DOCX 등): Upstage Document Parse API를 호출하여 텍스트를 추출합니다.
    """
    if filename.lower().endswith(".txt"):
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("cp949", errors="ignore")
        return preprocess_text(text)

    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "PDF/DOCX 텍스트 추출에는 UPSTAGE_API_KEY가 필요합니다."
        )

    # Upstage Document Parse API endpoint
    url = "https://api.upstage.ai/v1/document-ai/document-parse"
    
    response = httpx.post(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        files={"document": (filename, file_bytes)},
        data={"output_formats": '["text"]'},
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    content_text = data.get("content", {}).get("text", "")
    if content_text:
        return preprocess_text(content_text)

    pages = data.get("pages", [])
    extracted_texts = []
    for page in pages:
        # text 혹은 markdown 필드에서 텍스트를 가져옴
        page_text = page.get("text", "") or page.get("markdown", "")
        if page_text:
            extracted_texts.append(page_text)

    if not extracted_texts:
        for element in data.get("elements", []):
            element_text = element.get("text", "") or element.get("content", {}).get("text", "")
            if element_text:
                extracted_texts.append(element_text)

    combined_text = "\n".join(extracted_texts)
    text = preprocess_text(combined_text)
    if not text:
        raise ValueError("문서에서 텍스트를 추출하지 못했습니다.")
    return text


def split_clauses(text: str) -> list[str]:
    """
    전처리된 계약서 텍스트를 조항 단위로 정밀하게 나눕니다.
    - 제N조, N., (N) 등의 패턴을 기준으로 텍스트를 분할합니다.
    - 각 조항별 트림 처리 후, 유의미한 길이(30자 이상)의 조항을 최대 20개 추출합니다.
    """
    pattern = r"(?=제\s*\d+\s*조|^\s*\d+\.\s|^\s*\(\d+\)\s)"
    parts = re.split(pattern, text, flags=re.MULTILINE)

    clauses = []
    for part in parts:
        cleaned = part.strip()
        if not re.match(r"^(제\s*\d+\s*조|\d+\.\s|\(\d+\)\s)", cleaned):
            continue
        if len(cleaned) >= 30:
            clauses.append(cleaned)

    if not clauses:
        fallback_parts = re.split(
            r"\n\s*\n|(?<=[.!?])\s+(?=[가-힣A-Za-z0-9])",
            text,
        )
        clauses = [
            part.strip()
            for part in fallback_parts
            if len(part.strip()) >= 20
        ]

    return clauses[:20]

# 데이터 셋업 가이드

ChromaDB에 문서를 적재하는 방법을 설명한다.

## 구조

```
data/
├── raw/           ← 크롤링한 원문 (.md, .txt)
├── embeddings/    ← 임베딩 벡터 (.npy)
└── chroma/        ← ChromaDB 저장소 (자동 생성)
```

Google Drive에 원문과 임베딩이 미리 준비되어 있다.  
파일 목록은 프로젝트 루트의 CSV 또는 [구글 시트](https://docs.google.com/spreadsheets/d/1gXUPPp3z0Vw2s3I6JzXrmPzW1ZIqgn3KflOUtgzaTiQ)를 참고한다.

---

## 1단계: 파일 다운로드

```bash
pip install gdown
python scripts/setup_data.py
```

| 옵션 | 설명 |
|------|------|
| (없음) | 원문 + 임베딩 모두 다운로드 |
| `--emb-only` | 임베딩만 다운로드 |
| `--raw-only` | 원문만 다운로드 |

---

## 2단계: ChromaDB 적재

```bash
python -m src.ingest_crawl
```

전체 초기화 후 재적재:

```bash
python -m src.ingest_crawl --reset
```

---

## 파이프라인 비교

| 스크립트 | 입력 | 출력 | 용도 |
|----------|------|------|------|
| `embed.py` | `data/crawl/*.md` | `data/embeddings/*.npy` (단일 벡터) | 크롤링 문서 임베딩 |
| `embed_pdf.py` | PDF 파일 | `data/raw/*.md` + `data/embeddings/*.npy` (청크) | PDF 임베딩 |
| `ingest_crawl.py` | `data/raw/` + `data/embeddings/` | `data/chroma/` | **현재 사용** |
| `ingest_chroma.py` | `data/raw/` (청크 형식) + `data/embeddings/` | `data/chroma/` | PDF 파이프라인 전용 |

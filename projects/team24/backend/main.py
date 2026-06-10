import json

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.explainer import explain
from services.orchestrator import (
    AnalysisPipelineError,
    iter_analysis_pipeline_events,
    run_analysis_pipeline,
)

app = FastAPI()


class ExplainRequest(BaseModel):
    clause: str


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...), contract_type: str = Form(...)):
    file_bytes = await file.read()
    try:
        return run_analysis_pipeline(
            file_bytes,
            file.filename or "uploaded_file",
            contract_type,
        )
    except AnalysisPipelineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "message": str(exc),
                "step": exc.step,
                "process_logs": exc.process_logs,
            },
        ) from exc


@app.post("/analyze/stream")
async def analyze_stream(file: UploadFile = File(...), contract_type: str = Form(...)):
    file_bytes = await file.read()
    filename = file.filename or "uploaded_file"

    def event_stream():
        try:
            for event in iter_analysis_pipeline_events(
                file_bytes,
                filename,
                contract_type,
            ):
                yield json.dumps(event, ensure_ascii=False) + "\n"
        except AnalysisPipelineError as exc:
            yield json.dumps(
                {
                    "event": "error",
                    "step": exc.step,
                    "status": "failed",
                    "message": str(exc),
                    "process_logs": exc.process_logs,
                },
                ensure_ascii=False,
            ) + "\n"
        except Exception as exc:
            yield json.dumps(
                {
                    "event": "error",
                    "step": "unknown",
                    "status": "failed",
                    "message": str(exc) or "알 수 없는 오류가 발생했습니다.",
                    "process_logs": [],
                },
                ensure_ascii=False,
            ) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@app.post("/explain")
def explain_clause(body: ExplainRequest):
    return {"explanation": explain(body.clause)}
